from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


JobStatus = Literal[
    "queued",
    "researching",
    "synthesizing",
    "assembling",
    "validating",
    "done",
    "failed",
]

DimensionName = Literal[
    "writings",
    "conversations",
    "expression",
    "external_views",
    "decisions",
    "timeline",
]

DIMENSIONS: tuple[DimensionName, ...] = (
    "writings",
    "conversations",
    "expression",
    "external_views",
    "decisions",
    "timeline",
)


class DistillRequest(BaseModel):
    name: str = Field(..., description="Person name to distill, e.g. 'Warren Buffett'")
    locale: str = "zh-CN"

    search_provider: str | None = None
    search_api_key: str | None = None

    llm_base_url: str | None = None
    llm_api_key: str | None = None
    model_cheap: str | None = None
    model_strong: str | None = None

    force_refresh: bool = False
    upload_ids: list[str] = Field(default_factory=list)


class TokenUsage(BaseModel):
    prompt: int = 0
    completion: int = 0

    @property
    def total(self) -> int:
        return self.prompt + self.completion

    def add(self, prompt: int, completion: int) -> None:
        self.prompt += int(prompt or 0)
        self.completion += int(completion or 0)


class JobProgress(BaseModel):
    timestamp: datetime
    stage: str
    message: str


class JobRecord(BaseModel):
    job_id: str
    slug: str
    name: str
    status: JobStatus
    request: DistillRequest
    current_stage: str = "queued"
    progress: list[JobProgress] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    cache_hit_dimensions: list[str] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime | None = None
    error: str | None = None
    skill_path: str | None = None


class DimensionReport(BaseModel):
    dimension: DimensionName
    queries: list[str] = Field(default_factory=list)
    summary_md: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    cached: bool = False


class SynthesisModel(BaseModel):
    name: str
    one_liner: str
    evidence: list[str] = Field(default_factory=list)
    application: str = ""
    limitations: str = ""


class SynthesisHeuristic(BaseModel):
    rule: str
    when: str = ""
    case: str = ""


class SynthesisTimelineEntry(BaseModel):
    when: str
    event: str
    impact: str = ""


class SynthesisOutput(BaseModel):
    person_name: str
    person_name_en: str = ""
    hero_quote: str = ""
    identity_card: str = ""
    competencies: list[str] = Field(default_factory=list)
    anti_competencies: list[str] = Field(default_factory=list)
    role_play_dos: list[str] = Field(default_factory=list)
    role_play_donts: list[str] = Field(default_factory=list)
    models: list[SynthesisModel] = Field(default_factory=list)
    heuristics: list[SynthesisHeuristic] = Field(default_factory=list)
    expression_dna: dict[str, str] = Field(default_factory=dict)
    timeline: list[SynthesisTimelineEntry] = Field(default_factory=list)
    recent_updates: list[str] = Field(default_factory=list)
    values_pursued: list[str] = Field(default_factory=list)
    values_rejected: list[str] = Field(default_factory=list)
    internal_tensions: list[str] = Field(default_factory=list)
    influences_in: list[str] = Field(default_factory=list)
    influences_out: list[str] = Field(default_factory=list)
    honest_boundaries: list[str] = Field(default_factory=list)
    primary_sources: list[str] = Field(default_factory=list)
    secondary_sources: list[str] = Field(default_factory=list)
    key_quotes: list[dict[str, str]] = Field(default_factory=list)
    activation_keywords: list[str] = Field(default_factory=list)
    research_date: str = ""


class SkillMeta(BaseModel):
    slug: str
    dimensions: list[str]
    updated_at: datetime
    skill_path: str | None = None


class CacheEntry(BaseModel):
    slug: str
    dimensions: list[str]
    updated_at: datetime
