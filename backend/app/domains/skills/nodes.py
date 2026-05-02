from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.core import llm as llm_mod
from app.core.document_fetcher import (
    build_pdf_queries,
    fetch_documents_parallel,
    is_pdf_url,
)
from app.core.search import SearchResult, run_queries
from app.domains.skills import assembler, prompts, quality, storage
from app.domains.skills.schemas import (
    DIMENSIONS,
    DimensionName,
    DimensionReport,
    SynthesisOutput,
)


# ---------- helpers ----------

def _llm_overrides_from_request(request_dict: dict[str, Any]) -> dict[str, Any]:
    keys = ("llm_base_url", "llm_api_key", "model_cheap", "model_strong")
    return {k: request_dict[k] for k in keys if request_dict.get(k)}


def _format_search_block(
    hits: list[SearchResult],
    documents: dict[str, str] | None = None,
) -> str:
    if not hits:
        return "(无)"
    lines = []
    for i, hit in enumerate(hits, 1):
        entry = f"[{i}] {hit.title} — {hit.url}\n    摘要: {hit.snippet}"
        if documents:
            full = documents.get(hit.url, "")
            if full and not full.startswith("[fetch失败") and not full.startswith("[PDF:"):
                # Indent the full text so it reads as part of this result
                indented = "\n".join(
                    "    " + ln for ln in full.splitlines()
                )
                entry += f"\n    全文节选:\n{indented}"
        lines.append(entry)
    return "\n\n".join(lines)


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        # remove leading "json\n" if present
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    return text


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = _strip_json_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # try to slice from first { to last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


# ---------- nodes ----------

def intake_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    storage.append_progress(record, "intake", f"开始处理: {record.name}")
    record.status = "researching"
    storage.save_job(record)
    return {"record": record}


def cache_probe_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    if record.request.force_refresh:
        storage.append_progress(record, "cache_probe", "强制刷新, 跳过缓存")
        return {"reports": {}, "cache_hits": []}

    reports: dict[str, DimensionReport] = {}
    hits: list[str] = []
    for dim in DIMENSIONS:
        if storage.is_cache_fresh(record.slug, dim):
            cached = storage.load_cached_report(record.slug, dim)
            if cached:
                reports[dim] = cached
                hits.append(dim)
    record.cache_hit_dimensions = hits
    storage.append_progress(record, "cache_probe", f"命中缓存维度: {hits or '无'}")
    return {"reports": reports, "cache_hits": hits}


def plan_queries_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    cache_hits = state.get("cache_hits") or []
    if len(cache_hits) == len(DIMENSIONS):
        # full cache, nothing to plan
        storage.append_progress(record, "plan_queries", "全维度命中, 跳过 query 规划")
        return {"queries": {}}

    overrides = _llm_overrides_from_request(record.request.model_dump())
    messages = [
        {"role": "system", "content": prompts.PLAN_QUERIES_SYSTEM},
        {"role": "user", "content": prompts.PLAN_QUERIES_USER_TEMPLATE.format(name=record.name)},
    ]
    result = llm_mod.chat(
        messages,
        tier="cheap",
        overrides=overrides,
        max_tokens=900,
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    record.token_usage.add(result.prompt_tokens, result.completion_tokens)
    queries: dict[str, list[str]] = {}
    try:
        parsed = _parse_json(result.text)
        for dim in DIMENSIONS:
            raw = parsed.get(dim) or []
            queries[dim] = [str(q).strip() for q in raw if str(q).strip()][:5]
    except Exception as exc:  # noqa: BLE001
        storage.append_progress(record, "plan_queries", f"JSON 解析失败, 使用默认 query: {exc}")
        queries = {dim: [f"{record.name} {dim}"] for dim in DIMENSIONS}

    storage.append_progress(record, "plan_queries", f"已生成 {sum(len(q) for q in queries.values())} 条查询")
    return {"queries": queries}


def _research_one(
    record,
    dimension: DimensionName,
    queries: list[str],
    uploads_block: str,
) -> DimensionReport:
    request = record.request

    # 1. Build query list: standard queries + filetype:pdf variants for rich dimensions
    base_queries = queries or [f"{record.name} {dimension}"]
    pdf_queries = build_pdf_queries(base_queries, dimension)
    all_queries = base_queries + pdf_queries

    # 2. DDGS search (deduped across all queries)
    hits = run_queries(
        all_queries,
        provider=request.search_provider,  # type: ignore[arg-type]
        api_key=request.search_api_key,
    )

    # 3. Fetch full document content for PDF URLs (top 3 hits that look like PDFs)
    pdf_urls = [h.url for h in hits if h.url and is_pdf_url(h.url)][:3]
    documents: dict[str, str] = {}
    if pdf_urls:
        documents = fetch_documents_parallel(pdf_urls, max_workers=3, max_chars=6000)

    # 4. Build enriched search block
    search_block = _format_search_block(hits, documents)

    # 5. LLM synthesis — bump max_tokens slightly when we have full doc content
    has_docs = any(v and not v.startswith("[") for v in documents.values())
    overrides = _llm_overrides_from_request(request.model_dump())
    messages = [
        {"role": "system", "content": prompts.RESEARCH_SYSTEM},
        {
            "role": "user",
            "content": prompts.RESEARCH_USER_TEMPLATE.format(
                name=record.name,
                dimension=dimension,
                dimension_brief=prompts.DIMENSION_BRIEFS[dimension],
                search_block=search_block,
                uploads_block=uploads_block or "(无)",
            ),
        },
    ]
    result = llm_mod.chat(
        messages,
        tier="cheap",
        overrides=overrides,
        max_tokens=2000 if has_docs else 1500,
        temperature=0.2,
    )
    record.token_usage.add(result.prompt_tokens, result.completion_tokens)
    return DimensionReport(
        dimension=dimension,
        queries=all_queries,
        summary_md=result.text.strip(),
        sources=[{"title": h.title, "url": h.url} for h in hits],
        cached=False,
    )


def research_all_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    cached_reports: dict[str, DimensionReport] = state.get("reports") or {}
    queries_by_dim: dict[str, list[str]] = state.get("queries") or {}

    todo = [d for d in DIMENSIONS if d not in cached_reports]
    if not todo:
        storage.append_progress(record, "research", "全维度命中缓存, 跳过研究")
        return {"reports": cached_reports}

    uploads_block = storage.load_uploads(record.slug, record.request.upload_ids or None)

    storage.append_progress(record, "research", f"开始研究: {todo}")
    new_reports = dict(cached_reports)

    # Note: we do not parallelize here on purpose — the cheap-tier provider may
    # rate-limit, and python's threadpool would only help wall-clock. The bigger
    # win for token efficiency comes from caching and tight max_tokens budgets.
    for dim in todo:
        try:
            report = _research_one(record, dim, queries_by_dim.get(dim, []), uploads_block)
            new_reports[dim] = report
            storage.write_cached_report(record.slug, report)
            storage.append_progress(record, "research", f"完成 {dim}")
        except Exception as exc:  # noqa: BLE001
            storage.append_progress(record, "research", f"维度 {dim} 失败: {exc}")
            new_reports[dim] = DimensionReport(
                dimension=dim,
                queries=queries_by_dim.get(dim, []),
                summary_md=f"## 维度概要\n该维度调研失败: {exc}\n\n## 来源\n(无)",
                sources=[],
                cached=False,
            )
    return {"reports": new_reports}


def merge_research_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    reports: dict[str, DimensionReport] = state["reports"]

    primary = 0
    secondary = 0
    total_sources = 0
    for report in reports.values():
        text = report.summary_md
        primary += text.count("[一手]")
        secondary += text.count("[二手]")
        total_sources += len(report.sources)

    aggregate = (
        f"维度数量: {len(reports)}\n"
        f"搜索结果合计: {total_sources}\n"
        f"一手标注次数: {primary}\n"
        f"二手标注次数: {secondary}\n"
    )
    storage.append_progress(record, "merge_research", "聚合完成")
    return {"aggregate": aggregate}


def synthesize_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    record.status = "synthesizing"
    storage.save_job(record)

    reports: dict[str, DimensionReport] = state["reports"]
    aggregate: str = state.get("aggregate", "")

    research_block_parts = []
    for dim in DIMENSIONS:
        report = reports.get(dim)
        if not report:
            continue
        research_block_parts.append(f"### 维度: {dim}\n\n{report.summary_md}")
    research_block = "\n\n---\n\n".join(research_block_parts)

    overrides = _llm_overrides_from_request(record.request.model_dump())
    today = datetime.now().strftime("%Y-%m-%d")
    messages = [
        {"role": "system", "content": prompts.SYNTHESIS_SYSTEM},
        {
            "role": "user",
            "content": prompts.SYNTHESIS_USER_TEMPLATE.format(
                name=record.name,
                today=today,
                research_block=research_block,
                aggregate_block=aggregate,
            ),
        },
    ]
    result = llm_mod.chat(
        messages,
        tier="strong",
        overrides=overrides,
        max_tokens=6000,
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    record.token_usage.add(result.prompt_tokens, result.completion_tokens)

    parsed = _parse_json(result.text)
    parsed.setdefault("research_date", today)
    parsed.setdefault("person_name", record.name)
    synthesis = SynthesisOutput.model_validate(parsed)
    storage.write_synthesis(record.slug, parsed)
    storage.append_progress(record, "synthesize", f"提炼完成: {len(synthesis.models)} 个心智模型")
    return {"synthesis": synthesis}


def agentic_protocol_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    synthesis: SynthesisOutput = state["synthesis"]
    overrides = _llm_overrides_from_request(record.request.model_dump())

    models_payload = [m.model_dump() for m in synthesis.models]
    messages = [
        {"role": "system", "content": prompts.AGENTIC_PROTOCOL_SYSTEM},
        {
            "role": "user",
            "content": prompts.AGENTIC_PROTOCOL_USER_TEMPLATE.format(
                name=synthesis.person_name or record.name,
                models_json=json.dumps(models_payload, ensure_ascii=False, indent=2),
            ),
        },
    ]
    try:
        result = llm_mod.chat(
            messages,
            tier="cheap",
            overrides=overrides,
            max_tokens=900,
            temperature=0.2,
        )
        record.token_usage.add(result.prompt_tokens, result.completion_tokens)
        protocol_md = result.text.strip()
    except Exception as exc:  # noqa: BLE001
        storage.append_progress(record, "agentic_protocol", f"降级到模板: {exc}")
        protocol_md = _fallback_agentic_protocol(synthesis)
    return {"agentic_protocol": protocol_md}


def assemble_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    record.status = "assembling"
    storage.save_job(record)
    synthesis: SynthesisOutput = state["synthesis"]
    protocol_md: str = state.get("agentic_protocol") or _fallback_agentic_protocol(synthesis)
    skill_md = assembler.render_skill_md(
        synthesis,
        slug=record.slug,
        agentic_protocol_md=protocol_md,
    )
    storage.append_progress(record, "assemble", f"SKILL.md 已渲染 ({len(skill_md)} 字符)")
    return {"skill_md": skill_md}


def validate_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    record.status = "validating"
    storage.save_job(record)
    skill_md: str = state["skill_md"]
    results = quality.run_checks(skill_md)
    passed, total = quality.summarize(results)
    summary = "; ".join(f"{r.name}={'OK' if r.passed else 'FAIL'}" for r in results)
    storage.append_progress(record, "validate", f"{passed}/{total} 通过 — {summary}")
    return {"quality_results": [r.__dict__ for r in results], "quality_passed": passed, "quality_total": total}


def persist_node(state: dict[str, Any]) -> dict[str, Any]:
    record = state["record"]
    skill_md: str = state["skill_md"]
    path = storage.write_skill(record.slug, skill_md)
    storage.mark_done(record, path)
    storage.append_progress(record, "persist", f"写入 {path}")
    return {"skill_path": str(path)}


def _fallback_agentic_protocol(synthesis: SynthesisOutput) -> str:
    name = synthesis.person_name or "此人"
    model_lines = "\n".join(
        f"- **{m.name}**: {m.one_liner}" for m in synthesis.models
    )
    return f"""### Step 1: 问题分类

| 类型 | 特征 | 行动 |
|------|------|------|
| 需要事实的问题 | 涉及具体公司/事件/数据 | → 先调研再回答 |
| 纯框架问题 | 抽象方法论 | → 直接套用心智模型 |
| 混合问题 | 用具体案例讨论原理 | → 先取案例再框架 |

### Step 2: 研究维度

围绕以下心智模型, 在回答前快速核查关键事实:

{model_lines}

### Step 3: 回答时调用

- 优先用 {name} 的心智模型作为推理框架
- 引用一手言论(著作/访谈/年报)而非二手解读
- 保持 {name} 的表达 DNA(见下文)
"""
