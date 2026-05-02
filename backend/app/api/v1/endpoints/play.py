from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.scoring_config import DIMENSION_MAX_SCORES, scoring_config
from app.domains.quiz.schemas import AttemptRequest, Question
from app.domains.quiz.service import check_attempt, list_questions
from app.graphs.trading_personality_workflow import (
    TradingPersonalityWorkflow,
    TradingPsychologyState,
    create_personality_workflow,
)

router = APIRouter()

_sessions: dict[str, TradingPsychologyState] = {}
_workflow: TradingPersonalityWorkflow | None = None


def _get_workflow() -> TradingPersonalityWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = create_personality_workflow(list_questions().questions)
    return _workflow


# ---------- 请求 / 响应 Schema ----------

class PlayRequest(BaseModel):
    user_id: str = Field(..., description="用户唯一标识")
    answer: list[str] | None = Field(
        default=None,
        description="本题答案；选择题传选项 key（如 ['B']），问答题传文字；留空表示开始新会话或恢复断点",
    )


class Progress(BaseModel):
    current: int
    total: int
    pct: float


class DimScore(BaseModel):
    score: float
    normalized: float


class ShortfallPenalty(BaseModel):
    min_dimension: float
    penalty_amount: float
    enabled: bool


class ScoringDetails(BaseModel):
    base_quant_purity: float
    final_quant_purity: float
    shortfall_penalty: ShortfallPenalty


class FinalResult(BaseModel):
    persona: str
    persona_description: str
    route_action: str
    trait_tags: list[str]
    dimension_scores: dict[str, DimScore]
    scoring_details: ScoringDetails


class PlayResponse(BaseModel):
    user_id: str
    status: Literal["question", "retry", "finished"]
    progress: Progress
    question: Question | None = Field(default=None, description="当前或下一道题；finished 时为 null")
    retry_count: int = Field(default=0, description="已重试次数；status=retry 时有效")
    message: str = Field(default="", description="提示信息；status=retry 时说明原因")
    result: FinalResult | None = Field(default=None, description="最终画像；status=finished 时有效")


# ---------- 内部工具 ----------

def _make_progress(state: TradingPsychologyState, total: int) -> Progress:
    current = min(state["current_q_index"], total)
    return Progress(current=current, total=total, pct=round(current / total, 4) if total else 0.0)


def _build_result(state: TradingPsychologyState) -> FinalResult:
    t_norm = state.get("trigger_score", 0.0) / DIMENSION_MAX_SCORES["trigger"]
    e_norm = state.get("execution_score", 0.0) / DIMENSION_MAX_SCORES["execution"]
    a_norm = state.get("attribution_score", 0.0) / DIMENSION_MAX_SCORES["attribution"]

    base = (
        t_norm * scoring_config.dimension.trigger
        + e_norm * scoring_config.dimension.execution
        + a_norm * scoring_config.dimension.attribution
    )
    final = state.get("_final_quant_purity", base)
    min_dim = min(t_norm, e_norm, a_norm)

    return FinalResult(
        persona=state["final_persona"],
        persona_description=state.get("persona_description", ""),
        route_action=state["route_action"],
        trait_tags=state.get("trait_tags", []),
        dimension_scores={
            "trigger":     DimScore(score=state.get("trigger_score", 0.0),     normalized=t_norm),
            "execution":   DimScore(score=state.get("execution_score", 0.0),   normalized=e_norm),
            "attribution": DimScore(score=state.get("attribution_score", 0.0), normalized=a_norm),
        },
        scoring_details=ScoringDetails(
            base_quant_purity=round(base, 4),
            final_quant_purity=round(final, 4),
            shortfall_penalty=ShortfallPenalty(
                min_dimension=round(min_dim, 4),
                penalty_amount=round(base - final, 4),
                enabled=scoring_config.shortfall_penalty.enabled,
            ),
        ),
    )


def _question_response(state: TradingPsychologyState, workflow: TradingPersonalityWorkflow) -> PlayResponse:
    q = workflow.get_current_question(state)
    return PlayResponse(
        user_id=state["user_id"],
        status="question",
        progress=_make_progress(state, len(workflow.questions)),
        question=q,
    )


# ---------- 统一接口 ----------

@router.post(
    "",
    response_model=PlayResponse,
    summary="统一答题接口",
    description=(
        "单接口驱动完整评估流程。\n\n"
        "- `answer` 为空：自动创建新会话（或恢复已有会话），返回当前题目。\n"
        "- `answer` 非空：提交当前题答案，返回下一题、重试提示或最终结果。\n\n"
        "响应 `status` 取值：\n"
        "- `question`：返回下一道题，继续作答\n"
        "- `retry`：问答题答案太短，请重新作答（同一道题）\n"
        "- `finished`：全部题目完成，`result` 字段含最终画像"
    ),
)
def play(req: PlayRequest) -> PlayResponse:
    workflow = _get_workflow()

    # 无 answer：开始新会话或恢复断点
    if req.answer is None:
        if req.user_id not in _sessions:
            _sessions[req.user_id] = workflow.initialize(req.user_id)
        state = _sessions[req.user_id]
        if workflow.is_finished(state):
            return PlayResponse(
                user_id=req.user_id,
                status="finished",
                progress=_make_progress(state, len(workflow.questions)),
                result=_build_result(state),
            )
        return _question_response(state, workflow)

    # 有 answer：提交答案
    if req.user_id not in _sessions:
        _sessions[req.user_id] = workflow.initialize(req.user_id)

    state = _sessions[req.user_id]

    # 已完成，直接返回结果（幂等）
    if workflow.is_finished(state):
        return PlayResponse(
            user_id=req.user_id,
            status="finished",
            progress=_make_progress(state, len(workflow.questions)),
            result=_build_result(state),
        )

    current_q = workflow.get_current_question(state)
    if current_q is None:
        # 所有题已答完但尚未汇总
        state = workflow.aggregate_and_route(state)
        return PlayResponse(
            user_id=req.user_id,
            status="finished",
            progress=_make_progress(state, len(workflow.questions)),
            result=_build_result(state),
        )

    state = workflow.dispatch(state)

    if current_q.type == "qa":
        state = workflow.validate_answer(state, " ".join(req.answer))
        last_log = state["history_logs"][-1]

        if last_log.get("skipped"):
            # 达到重试上限，跳过本题
            if not workflow.should_continue(state):
                state = workflow.aggregate_and_route(state)
                return PlayResponse(
                    user_id=req.user_id,
                    status="finished",
                    progress=_make_progress(state, len(workflow.questions)),
                    result=_build_result(state),
                )
            return _question_response(state, workflow)

        if last_log.get("answer") is None:
            # 答案太短，退回 dispatch 追加的 log，要求重试
            state["history_logs"].pop()
            return PlayResponse(
                user_id=req.user_id,
                status="retry",
                progress=_make_progress(state, len(workflow.questions)),
                question=current_q,
                retry_count=state["retry_count"],
                message="答案太简短，请提供更完整的回答",
            )
    else:
        state["history_logs"][-1]["answer"] = " ".join(req.answer)

    result = check_attempt(AttemptRequest(question_id=current_q.id, answer=req.answer))
    state = workflow.evaluate_answer(state, result)

    if workflow.should_continue(state):
        return _question_response(state, workflow)

    state = workflow.aggregate_and_route(state)
    return PlayResponse(
        user_id=req.user_id,
        status="finished",
        progress=_make_progress(state, len(workflow.questions)),
        result=_build_result(state),
    )
