from __future__ import annotations

from pydantic import BaseModel, Field


class DifficultyWeights(BaseModel):
    level_1: float = Field(default=1.0)
    level_2: float = Field(default=1.4)
    level_3: float = Field(default=2.0)

    def get_k(self, difficulty: int) -> float:
        return {1: self.level_1, 2: self.level_2, 3: self.level_3}.get(difficulty, 1.0)


class DimensionWeights(BaseModel):
    trigger: float = Field(default=0.33, description="信息触发源权重")
    execution: float = Field(default=0.34, description="规则执行力权重")
    attribution: float = Field(default=0.33, description="结果归因权重")

    def get_weight(self, dimension: str) -> float:
        return {"trigger": self.trigger, "execution": self.execution, "attribution": self.attribution}.get(dimension, 0.0)


class RouteThresholds(BaseModel):
    emotional: float = Field(default=0.25, description="跟着感觉走 上限")
    retail: float = Field(default=0.45, description="靠直觉交易 上限")
    developing: float = Field(default=0.65, description="开始有方法了 上限")
    advanced: float = Field(default=0.80, description="想清楚再动手 上限")


class ShortfallPenaltyConfig(BaseModel):
    enabled: bool = Field(default=True)
    penalty_weight: float = Field(default=0.2)
    base_weight: float = Field(default=0.8)

    def apply_penalty(self, base_score: float, dimension_scores: dict[str, float]) -> float:
        if not self.enabled or not dimension_scores:
            return base_score
        min_dim_score = min(dimension_scores.values())
        return self.base_weight * base_score + self.penalty_weight * min_dim_score


class ValidationConfig(BaseModel):
    max_retries: int = Field(default=2)
    confidence_smooth_min: float = Field(default=0.6)
    confidence_smooth_factor: float = Field(default=0.4)


class ScoringConfig(BaseModel):
    difficulty: DifficultyWeights = Field(default_factory=DifficultyWeights)
    dimension: DimensionWeights = Field(default_factory=DimensionWeights)
    route: RouteThresholds = Field(default_factory=RouteThresholds)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    shortfall_penalty: ShortfallPenaltyConfig = Field(default_factory=ShortfallPenaltyConfig)

    def get_k(self, difficulty: int) -> float:
        return self.difficulty.get_k(difficulty)

    def get_dimension_weight(self, dimension: str) -> float:
        return self.dimension.get_weight(dimension)


scoring_config = ScoringConfig()


# 选择题：每个选项的三维得分矩阵 {question_id: {option_key: {trigger, execution, attribution}}}
OPTION_DIMENSION_SCORES: dict[str, dict[str, dict[str, float]]] = {
    "q021": {
        "A": {"trigger": 0.0, "execution": 0.5, "attribution": 0.0},
        "B": {"trigger": 1.0, "execution": 0.5, "attribution": 0.5},
        "C": {"trigger": 0.5, "execution": 0.0, "attribution": 0.5},
        "D": {"trigger": 0.5, "execution": 0.5, "attribution": 1.0},
    },
    "q022": {
        "A": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "B": {"trigger": 0.5, "execution": 1.0, "attribution": 0.5},
        "C": {"trigger": 0.5, "execution": 0.5, "attribution": 0.5},
        "D": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
    },
    "q023": {
        "A": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "B": {"trigger": 0.5, "execution": 0.5, "attribution": 1.0},
        "C": {"trigger": 0.5, "execution": 0.5, "attribution": 0.5},
        "D": {"trigger": 0.5, "execution": 0.5, "attribution": 0.0},
    },
    "q024": {
        "A": {"trigger": 0.5, "execution": 0.5, "attribution": 0.0},
        "B": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "C": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "D": {"trigger": 0.5, "execution": 1.0, "attribution": 0.5},
    },
    "q025": {
        "A": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "B": {"trigger": 0.5, "execution": 1.0, "attribution": 0.5},
        "C": {"trigger": 0.5, "execution": 0.5, "attribution": 0.5},
        "D": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
    },
    "q026": {
        "A": {"trigger": 0.5, "execution": 0.5, "attribution": 0.5},
        "B": {"trigger": 1.0, "execution": 0.5, "attribution": 0.5},
        "C": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "D": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
    },
    "q027": {
        "A": {"trigger": 0.5, "execution": 1.0, "attribution": 0.5},
        "B": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "C": {"trigger": 0.5, "execution": 0.5, "attribution": 1.0},
        "D": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
    },
    "q028": {
        "A": {"trigger": 0.5, "execution": 0.5, "attribution": 0.0},
        "B": {"trigger": 0.5, "execution": 0.5, "attribution": 1.0},
        "C": {"trigger": 0.5, "execution": 0.5, "attribution": 0.5},
        "D": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
    },
    "q029": {
        "A": {"trigger": 0.5, "execution": 0.5, "attribution": 0.0},
        "B": {"trigger": 1.0, "execution": 1.0, "attribution": 0.5},
        "C": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "D": {"trigger": 0.5, "execution": 0.5, "attribution": 1.0},
    },
    "q030": {
        "A": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
        "B": {"trigger": 0.5, "execution": 1.0, "attribution": 0.5},
        "C": {"trigger": 0.5, "execution": 0.5, "attribution": 1.0},
        "D": {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
    },
}

# 问答题：raw_score 按比例分配到各维度
QA_DIMENSION_MAPPING: dict[str, dict[str, float]] = {
    "q031": {"trigger": 0.0, "execution": 0.6, "attribution": 0.4},
    "q032": {"trigger": 0.0, "execution": 1.0, "attribution": 0.0},
    "q033": {"trigger": 0.0, "execution": 0.2, "attribution": 0.8},
}

# 各维度理论最高分（选择题 + 问答题满分，难度系数 k 已纳入）
# 选择题部分：按每题最优选项 × k 累加
# 问答题部分：q031(k=1.0) q032(k=1.4) q033(k=2.0)，按维度分配比例计算
DIMENSION_MAX_SCORES: dict[str, float] = {
    "trigger":     7.1,   # 选择题贡献，问答题无贡献
    "execution":  11.68,  # 选择题 8.8 + 问答题 2.88
    "attribution": 10.52, # 选择题 8.6 + 问答题 1.92
}


def get_option_dimension_scores(question_id: str, option_key: str) -> dict[str, float]:
    """返回选择题某个选项的三维原始得分，未找到返回全零。"""
    return OPTION_DIMENSION_SCORES.get(question_id, {}).get(
        option_key.upper(),
        {"trigger": 0.0, "execution": 0.0, "attribution": 0.0},
    )


def get_qa_dimension_mapping(question_id: str) -> dict[str, float]:
    """返回问答题的维度分配比例。"""
    return QA_DIMENSION_MAPPING.get(
        question_id,
        {"trigger": 0.33, "execution": 0.34, "attribution": 0.33},
    )


# 兼容旧接口
def get_dimension_mapping(question_id: str) -> dict[str, float]:
    if question_id in QA_DIMENSION_MAPPING:
        return QA_DIMENSION_MAPPING[question_id]
    return {}
