"""Deterministic SKILL.md assembly from a SynthesisOutput.

We intentionally do NOT ask an LLM to write the 14-section structure — the
synthesis stage has already produced all content fields; here we just render
them into the canonical nuwa-skill template. The Agentic Protocol section
is the only part that is produced by an LLM call upstream (see
nodes.agentic_protocol_node); this module takes it as an opaque string.
"""

from __future__ import annotations

from datetime import datetime

from app.domains.skills.schemas import SynthesisOutput


def _bullet(items: list[str], fallback: str = "(暂无)") -> str:
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {i}" for i in items)


def _checklist_yes(items: list[str]) -> str:
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return "- ✅ 直接以第一人称回应, 保持角色"
    return "\n".join(f"- ✅ {i}" for i in items)


def _checklist_no(items: list[str]) -> str:
    items = [i.strip() for i in items if i and i.strip()]
    if not items:
        return "- ❌ 不要跳出角色做 meta 分析"
    return "\n".join(f"- ❌ {i}" for i in items)


def _render_models(synthesis: SynthesisOutput) -> str:
    if not synthesis.models:
        return "(未提炼出心智模型)"
    parts: list[str] = []
    for idx, model in enumerate(synthesis.models, 1):
        evidence = "\n".join(f"  - {e}" for e in model.evidence) if model.evidence else "  - (暂无)"
        parts.append(
            f"""### 模型{idx}: {model.name}
**一句话**: {model.one_liner}

**证据**:
{evidence}

**应用**: {model.application or "(暂无)"}

**局限**: {model.limitations or "(暂无)"}"""
        )
    return "\n\n".join(parts)


def _render_heuristics(synthesis: SynthesisOutput) -> str:
    if not synthesis.heuristics:
        return "(未提炼出决策启发式)"
    parts: list[str] = []
    for idx, h in enumerate(synthesis.heuristics, 1):
        parts.append(
            f"""{idx}. **{h.rule}**
   - 应用场景: {h.when or "(暂无)"}
   - 案例: {h.case or "(暂无)"}"""
        )
    return "\n".join(parts)


def _render_expression_dna(synthesis: SynthesisOutput) -> str:
    dna = synthesis.expression_dna or {}
    rows = [
        ("句式", dna.get("sentence", "")),
        ("词汇", dna.get("vocabulary", "")),
        ("节奏", dna.get("rhythm", "")),
        ("幽默", dna.get("humor", "")),
        ("确定性", dna.get("certainty", "")),
        ("引用习惯", dna.get("citations", "")),
    ]
    return "\n".join(f"- **{label}**: {value or '(暂无)'}" for label, value in rows)


def _render_timeline(synthesis: SynthesisOutput) -> str:
    if not synthesis.timeline:
        return "| — | 暂无可靠时间线 | — |"
    lines = []
    for item in synthesis.timeline:
        lines.append(f"| {item.when or '—'} | {item.event or '—'} | {item.impact or '—'} |")
    return "\n".join(lines)


def _render_recent_updates(synthesis: SynthesisOutput) -> str:
    return _bullet(synthesis.recent_updates, fallback="暂无最新动态")


def _render_values(synthesis: SynthesisOutput) -> str:
    pursued = _bullet(synthesis.values_pursued, fallback="暂无")
    rejected = _bullet(synthesis.values_rejected, fallback="暂无")
    tensions = _bullet(synthesis.internal_tensions, fallback="暂无")
    return f"""**我追求的**:
{pursued}

**我拒绝的**:
{rejected}

**我自己也没想清楚的(内在张力)**:
{tensions}"""


def _render_influences(synthesis: SynthesisOutput) -> str:
    inflow = "、".join(synthesis.influences_in) or "(暂无)"
    outflow = "、".join(synthesis.influences_out) or "(暂无)"
    return f"- 影响我的: {inflow}\n- 我影响过的: {outflow}"


def _render_honest_boundaries(synthesis: SynthesisOutput) -> str:
    items = list(synthesis.honest_boundaries)
    date = synthesis.research_date or datetime.now().strftime("%Y-%m-%d")
    items.append(f"调研时间: {date}, 之后的变化未覆盖")
    return _bullet(items)


def _render_sources(synthesis: SynthesisOutput) -> str:
    primary = _bullet(synthesis.primary_sources, fallback="暂无明确一手来源")
    secondary = _bullet(synthesis.secondary_sources, fallback="暂无明确二手来源")
    if synthesis.key_quotes:
        quote_lines = []
        for q in synthesis.key_quotes:
            quote = q.get("quote", "").strip()
            source = q.get("source", "").strip()
            if not quote:
                continue
            quote_lines.append(f"> \"{quote}\" —— {source or '出处暂缺'}")
        quotes_block = "\n\n".join(quote_lines) if quote_lines else "(暂无关键引用)"
    else:
        quotes_block = "(暂无关键引用)"

    return f"""### 一手来源(此人直接产出)
{primary}

### 二手来源(他人分析)
{secondary}

### 关键引用
{quotes_block}"""


def _build_description(synthesis: SynthesisOutput) -> str:
    name = synthesis.person_name
    source_count = len(synthesis.primary_sources) + len(synthesis.secondary_sources)
    triggers = "、".join(
        f"「{k}」" for k in synthesis.activation_keywords[:6]
    ) or f"「{name} 会怎么看」"
    return (
        f"{name}的思维框架与表达方式。"
        f"基于 {source_count} 个来源的深度调研, "
        f"提炼 {len(synthesis.models)} 个核心心智模型、{len(synthesis.heuristics)} 条决策启发式和完整的表达 DNA。\n"
        f"  用途: 作为思维顾问, 用 {name} 的视角分析问题、审视决策、提供反馈。\n"
        f"  当用户提到 {triggers} 时使用。"
    )


def render_skill_md(
    synthesis: SynthesisOutput,
    *,
    slug: str,
    agentic_protocol_md: str,
) -> str:
    name = synthesis.person_name
    description = _build_description(synthesis)
    hero_quote = synthesis.hero_quote.strip() or "(待补充)"
    identity_card = synthesis.identity_card.strip() or f"我是 {name}。"

    return f"""---
name: {slug}-perspective
description: |
  {description}
---

# {name} · 思维操作系统

> {hero_quote}

## 使用说明

这不是 {name} 本人。这是基于公开信息提炼的思维框架。
它能帮你用 {name} 的镜片审视问题, 但不能替代原创思考。

**擅长**:
{_bullet(synthesis.competencies, fallback="(待补充)")}

**不擅长**:
{_bullet(synthesis.anti_competencies, fallback="(待补充)")}

---

## 角色扮演规则

**此 Skill 激活后, 直接以 {name} 的身份回应。**

{_checklist_yes(synthesis.role_play_dos)}
{_checklist_no(synthesis.role_play_donts)}

**退出角色**: 用户说「退出」「切回正常」「不用扮演了」时恢复正常模式。

---

## 回答工作流(Agentic Protocol)

{agentic_protocol_md.strip()}

---

## 身份卡

**我是谁**: {identity_card}

## 核心心智模型

{_render_models(synthesis)}

## 决策启发式

{_render_heuristics(synthesis)}

## 表达 DNA

角色扮演时必须遵循的风格规则:

{_render_expression_dna(synthesis)}

## 人物时间线(关键节点)

| 时间 | 事件 | 对我思维的影响 |
|------|------|--------------|
{_render_timeline(synthesis)}

### 最新动态({synthesis.research_date or datetime.now().strftime('%Y')})
{_render_recent_updates(synthesis)}

## 价值观与反模式

{_render_values(synthesis)}

## 智识谱系

影响过我的人 → 我 → 我影响了谁

{_render_influences(synthesis)}

## 诚实边界

此 Skill 基于公开信息提炼, 存在以下局限:

{_render_honest_boundaries(synthesis)}

## 附录: 调研来源

{_render_sources(synthesis)}

---

> 本 Skill 由 OpenSucker 蒸馏服务自动生成, 参考 [女娲 · Skill 造人术](https://github.com/alchaincyf/nuwa-skill) 框架。
"""
