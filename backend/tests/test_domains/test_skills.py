from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core import llm as llm_mod
from app.core import search as search_mod
from app.core.config import settings
from app.domains.skills import service, storage
from app.domains.skills.schemas import DistillRequest, DIMENSIONS


@pytest.fixture(autouse=True)
def isolate_data_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    storage.ensure_dirs()
    yield


@pytest.fixture
def stub_search(monkeypatch):
    def fake_run_queries(queries, **kwargs):
        return [
            search_mod.SearchResult(
                title=f"Result for {q}",
                url=f"https://example.com/{i}",
                snippet=f"Snippet for {q}.",
            )
            for i, q in enumerate(queries)
        ]

    monkeypatch.setattr("app.domains.skills.nodes.run_queries", fake_run_queries)


@pytest.fixture
def stub_llm(monkeypatch):
    synthesis_payload = {
        "person_name": "测试投资人",
        "person_name_en": "Test Investor",
        "hero_quote": "永远不要亏损。",
        "identity_card": "我是测试投资人, 我相信长期主义。",
        "competencies": ["判断护城河", "估值"],
        "anti_competencies": ["短线交易", "加密货币"],
        "role_play_dos": ["用我", "先故事后原则"],
        "role_play_donts": ["不说 DCF", "不跳出角色"],
        "models": [
            {"name": "护城河", "one_liner": "生意的耐久竞争优势", "evidence": ["股东信1988", "Columbia演讲"], "application": "判断长期生意", "limitations": "前沿科技领域不适用"},
            {"name": "能力圈", "one_liner": "只投看得懂的生意", "evidence": ["年会2001", "Lowenstein传记"], "application": "过滤机会", "limitations": "容易过度保守"},
            {"name": "安全边际", "one_liner": "价格远低于价值", "evidence": ["Graham传承", "1973买入WashPost"], "application": "买入时机", "limitations": "牛市中极难找到"},
            {"name": "Owner Earnings", "one_liner": "真正可分配的现金流", "evidence": ["1986股东信"], "application": "估值", "limitations": "需要长期视角"},
        ],
        "heuristics": [
            {"rule": "不懂就不买", "when": "遇到新技术", "case": "错过早期Google也不后悔"},
            {"rule": "市场先生是仆人", "when": "市场波动大时", "case": "2008金融危机买入"},
            {"rule": "别人恐惧我贪婪", "when": "恐慌性抛售", "case": "2008 NYT op-ed"},
            {"rule": "永远持有伟大生意", "when": "评估卖出", "case": "See's Candies"},
            {"rule": "关注管理层", "when": "挑选公司", "case": "投资苹果因为库克"},
        ],
        "expression_dna": {
            "sentence": "先讲故事后给原则",
            "vocabulary": "打击区、农场、棒球",
            "rhythm": "慢节奏, 留白",
            "humor": "温和自嘲",
            "certainty": "大量 'I don't know'",
            "citations": "爱引 Graham / Munger",
        },
        "timeline": [
            {"when": "1930", "event": "出生", "impact": "奠定性格"},
            {"when": "1965", "event": "接手 Berkshire", "impact": "开启投资实验"},
        ],
        "recent_updates": ["2023 年会继续谈护城河"],
        "values_pursued": ["长期主义", "诚信"],
        "values_rejected": ["短线投机", "过度杠杆"],
        "internal_tensions": ["一方面重视分散, 另一方面又高度集中持仓", "既要谦逊又要快速果断"],
        "influences_in": ["Benjamin Graham", "Charlie Munger"],
        "influences_out": ["众多价值投资者"],
        "honest_boundaries": ["不懂加密货币", "不懂前沿科技", "宏观预测不擅长"],
        "primary_sources": ["一手: Berkshire 股东信", "一手: 年会 Q&A"],
        "secondary_sources": ["二手: Schroeder 传记", "二手: AQR 学术论文"],
        "key_quotes": [{"quote": "Rule No. 1: Never lose money", "source": "Berkshire letter"}],
        "activation_keywords": ["价值投资", "护城河", "能力圈"],
        "research_date": "2026-05-01",
    }

    def fake_chat(messages, **kwargs):
        system = (messages[0].get("content") or "") if messages else ""
        if "JSON" in system and "nuwa-skill" in system:
            return llm_mod.LLMResult(text=json.dumps(synthesis_payload), prompt_tokens=100, completion_tokens=200)
        if "策划助手" in system:
            queries = {d: [f"{d} q1", f"{d} q2"] for d in DIMENSIONS}
            return llm_mod.LLMResult(text=json.dumps(queries), prompt_tokens=50, completion_tokens=80)
        if "研究分析师" in system:
            return llm_mod.LLMResult(
                text="## 维度概要\n测试概要\n\n## 关键发现\n- 要点1 [一手]\n- 要点2 [二手]\n\n## 来源\n1. [一手] 来源A — https://a\n",
                prompt_tokens=80,
                completion_tokens=120,
            )
        if "工作流设计师" in system:
            return llm_mod.LLMResult(text="### Step 1: 问题分类\n...\n### Step 2: 研究维度\n...\n### Step 3: 回答时调用\n...", prompt_tokens=40, completion_tokens=60)
        return llm_mod.LLMResult(text="", prompt_tokens=0, completion_tokens=0)

    monkeypatch.setattr(llm_mod, "chat", fake_chat)
    monkeypatch.setattr("app.domains.skills.nodes.llm_mod.chat", fake_chat)


def test_end_to_end_distillation(stub_search, stub_llm):
    request = DistillRequest(name="Test Investor", llm_api_key="fake-key")
    record = service.start_job(request)
    service.execute_job(record.job_id)

    final = service.get_job(record.job_id)
    assert final is not None, "job record should exist"
    assert final.status == "done", f"expected done, got {final.status}: {final.error}"
    assert final.skill_path is not None

    skill_md = Path(final.skill_path).read_text(encoding="utf-8")
    assert "核心心智模型" in skill_md
    assert "决策启发式" in skill_md
    assert "诚实边界" in skill_md
    assert "表达 DNA" in skill_md
    assert "护城河" in skill_md

    # cache populated for all dimensions
    for dim in DIMENSIONS:
        assert storage.cache_path(final.slug, dim).exists()

    # token usage was accumulated
    assert final.token_usage.total > 0


def test_cache_hits_skip_research(stub_search, stub_llm):
    request = DistillRequest(name="Test Investor", llm_api_key="fake-key")
    first = service.start_job(request)
    service.execute_job(first.job_id)

    # second run: should hit cache for every dimension
    second_request = DistillRequest(name="Test Investor", llm_api_key="fake-key")
    second = service.start_job(second_request)
    service.execute_job(second.job_id)
    final = service.get_job(second.job_id)
    assert final is not None
    assert final.status == "done"
    assert set(final.cache_hit_dimensions) == set(DIMENSIONS)


def test_quality_checks_pass_on_rendered_skill(stub_search, stub_llm):
    from app.domains.skills import quality

    request = DistillRequest(name="Test Investor", llm_api_key="fake-key")
    record = service.start_job(request)
    service.execute_job(record.job_id)
    final = service.get_job(record.job_id)
    assert final is not None and final.skill_path
    content = Path(final.skill_path).read_text(encoding="utf-8")

    results = quality.run_checks(content)
    failed = [r for r in results if not r.passed]
    assert not failed, f"quality failures: {[(r.name, r.detail) for r in failed]}"
