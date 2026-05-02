"""LangGraph wiring for the skill distillation pipeline.

Flow:
    intake -> cache_probe -> plan_queries -> research_all -> merge_research
             -> synthesize -> agentic_protocol -> assemble -> validate -> persist

We keep the graph linear on purpose. The per-dimension research is handled
inside `research_all_node` (sequential, with tight max_tokens) so that we
don't pay the cost of six fan-out/fan-in edges in LangGraph for little
benefit on a single-machine FastAPI server.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.domains.skills import nodes
from app.domains.skills.schemas import DimensionReport, JobRecord, SynthesisOutput


class SkillDistillState(TypedDict, total=False):
    record: JobRecord
    reports: dict[str, DimensionReport]
    cache_hits: list[str]
    queries: dict[str, list[str]]
    aggregate: str
    synthesis: SynthesisOutput
    agentic_protocol: str
    skill_md: str
    quality_results: list[dict[str, Any]]
    quality_passed: int
    quality_total: int
    skill_path: str


def build_graph():
    graph: StateGraph = StateGraph(SkillDistillState)

    graph.add_node("intake", nodes.intake_node)
    graph.add_node("cache_probe", nodes.cache_probe_node)
    graph.add_node("plan_queries", nodes.plan_queries_node)
    graph.add_node("research_all", nodes.research_all_node)
    graph.add_node("merge_research", nodes.merge_research_node)
    graph.add_node("synthesize", nodes.synthesize_node)
    graph.add_node("agentic_protocol", nodes.agentic_protocol_node)
    graph.add_node("assemble", nodes.assemble_node)
    graph.add_node("validate", nodes.validate_node)
    graph.add_node("persist", nodes.persist_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "cache_probe")
    graph.add_edge("cache_probe", "plan_queries")
    graph.add_edge("plan_queries", "research_all")
    graph.add_edge("research_all", "merge_research")
    graph.add_edge("merge_research", "synthesize")
    graph.add_edge("synthesize", "agentic_protocol")
    graph.add_edge("agentic_protocol", "assemble")
    graph.add_edge("assemble", "validate")
    graph.add_edge("validate", "persist")
    graph.add_edge("persist", END)

    return graph.compile()


skill_distillation_graph = build_graph()


def run(initial_state: SkillDistillState) -> SkillDistillState:
    return skill_distillation_graph.invoke(initial_state)
