from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DimensionLiteral = Literal["Trigger", "Execution", "Attribution", "Mixed"]


class Option(BaseModel):
    key: str = Field(..., description="选项标识，如 A/B/C/D")
    text: str


class Question(BaseModel):
    id: str
    type: Literal["single", "multiple", "qa"]
    topic: Literal["量化交易", "交易终端", "券商柜台", "风险识别", "情景判断", "交易心理"]
    difficulty: int = Field(..., ge=1, le=3, description="1=基础 2=进阶 3=高难")
    dimension: DimensionLiteral | None = Field(default=None, description="题目主维度")
    stem: str
    options: list[Option] = Field(default_factory=list, description="选择题选项，问答题为空")
    correct_answer: list[str] = Field(..., description="选择题为选项 key 列表，问答题为参考答案列表", exclude=True)
    explanation: str = Field(default="", exclude=True)
    keywords: list[str] = Field(default_factory=list, description="问答题评分关键词", exclude=True)
    score_k: float = Field(default=1.0, ge=0.0, description="得分量程，按难度自动设置", exclude=True)
    score_b: float = Field(default=0.0, description="底分，统一为0", exclude=True)

    @property
    def max_score(self) -> float:
        return self.score_k + self.score_b

    def weighted_score(self, raw: float, confidence: float = 1.0) -> float:
        effective_raw = raw * (0.6 + 0.4 * confidence)
        return self.score_k * effective_raw + self.score_b


class AttemptRequest(BaseModel):
    question_id: str
    answer: list[str] = Field(..., description="选择题传选项 key，问答题传文字答案")


class AttemptResult(BaseModel):
    question_id: str
    is_correct: bool
    score: int = Field(..., description="得分 0-100（旧版保留）")
    correct_answer: list[str]
    matched_keywords: list[str] = Field(default_factory=list, description="问答题命中的关键词")
    llm_reasoning: str = Field(default="", description="LLM 评分理由")
    raw_score: float = Field(default=0.0, ge=0.0, le=1.0, description="LLM 原始评分 0.0/0.5/1.0")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="LLM 置信度")
    weighted_score: float = Field(default=0.0, ge=0.0, description="加权后得分")
    max_possible: float = Field(default=1.0, description="本题满分")
    dimension_scores: dict[str, float] = Field(default_factory=dict, description="各维度得分")


class QuestionListResponse(BaseModel):
    total: int
    questions: list[Question]


class QuizAnswerItem(BaseModel):
    question_id: str
    answer: list[str]


class QuizResultRequest(BaseModel):
    answers: list[QuizAnswerItem]


class DiagnosisResult(BaseModel):
    label: str
    title: str
    body: str


class QuizResultResponse(BaseModel):
    dimension_pcts: dict[str, int] = Field(description="各维度百分比 0-100")
    weakest_dim: str = Field(description="最薄弱维度，all_high=True 时为 'all'")
    all_high: bool
    diagnosis: DiagnosisResult
