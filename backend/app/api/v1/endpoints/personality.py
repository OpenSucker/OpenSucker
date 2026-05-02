from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.domains.quiz.schemas import AttemptRequest
from app.domains.quiz.service import check_attempt, list_questions
from app.graphs.trading_personality_workflow import (
    TradingPsychologyState,
    TradingPersonalityWorkflow,
    create_personality_workflow,
)
from app.core.scoring_config import DIMENSION_MAX_SCORES, scoring_config

router = APIRouter()

_sessions: dict[str, TradingPsychologyState] = {}
_workflow: TradingPersonalityWorkflow | None = None


def _get_workflow() -> TradingPersonalityWorkflow:
    global _workflow
    if _workflow is None:
        questions = list_questions().questions
        _workflow = create_personality_workflow(questions)
    return _workflow


def _build_dimension_block(state: TradingPsychologyState) -> dict:
    trigger_norm = state.get("trigger_score", 0.0) / DIMENSION_MAX_SCORES["trigger"]
    execution_norm = state.get("execution_score", 0.0) / DIMENSION_MAX_SCORES["execution"]
    attribution_norm = state.get("attribution_score", 0.0) / DIMENSION_MAX_SCORES["attribution"]

    base_purity = (
        trigger_norm * scoring_config.dimension.trigger +
        execution_norm * scoring_config.dimension.execution +
        attribution_norm * scoring_config.dimension.attribution
    )
    final_purity = state.get("_final_quant_purity", base_purity)
    min_dim = min(trigger_norm, execution_norm, attribution_norm)

    return {
        "dimension_scores": {
            "trigger":     {"score": state.get("trigger_score", 0.0),     "normalized": trigger_norm},
            "execution":   {"score": state.get("execution_score", 0.0),   "normalized": execution_norm},
            "attribution": {"score": state.get("attribution_score", 0.0), "normalized": attribution_norm},
        },
        "scoring_details": {
            "base_quant_purity":  round(base_purity, 4),
            "final_quant_purity": round(final_purity, 4),
            "shortfall_penalty": {
                "min_dimension":  round(min_dim, 4),
                "penalty_amount": round(base_purity - final_purity, 4),
                "enabled":        scoring_config.shortfall_penalty.enabled,
            },
        },
    }


@router.post("/start", summary="开始新的画像评估会话")
def start_personality_session(user_id: str) -> dict:
    workflow = _get_workflow()
    state = workflow.initialize(user_id)
    _sessions[user_id] = state

    current_q = workflow.get_current_question(state)
    if current_q is None:
        raise HTTPException(status_code=500, detail="没有可用题目")

    return {
        "user_id": user_id,
        "current_question": current_q.dict(),
        "progress": {
            "current": 0,
            "total": len(workflow.questions),
            "percentage": 0.0,
        },
    }


@router.get("/session/{user_id}", summary="获取当前会话状态")
def get_session_state(user_id: str) -> dict:
    if user_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    state = _sessions[user_id]
    workflow = _get_workflow()
    current_q = workflow.get_current_question(state)
    progress_current = min(state["current_q_index"], len(workflow.questions))
    progress_total = len(workflow.questions)

    return {
        "user_id": user_id,
        "progress": {
            "current": progress_current,
            "total": progress_total,
            "percentage": progress_current / progress_total if progress_total > 0 else 0.0,
        },
        "current_question": current_q.dict() if current_q else None,
        "is_finished": workflow.is_finished(state),
        "trait_tags": state.get("trait_tags", []),
    }


@router.post("/answer", summary="提交答案")
def submit_answer(user_id: str, request: AttemptRequest) -> dict:
    if user_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在，请先开始会话")

    state = _sessions[user_id]
    workflow = _get_workflow()

    current_q = workflow.get_current_question(state)
    if current_q is None or current_q.id != request.question_id:
        raise HTTPException(status_code=400, detail="题目ID不匹配")

    # 为当前题目添加日志条目
    state = workflow.dispatch(state)

    # 问答题才做内容有效性校验，选择题不校验（单字母不满足长度要求）
    if current_q.type == "qa":
        state = workflow.validate_answer(state, " ".join(request.answer))
        last_log = state["history_logs"][-1]
        if last_log.get("skipped"):
            # 超过重试上限，跳过本题
            next_q = workflow.get_current_question(state)
            return {
                "next_question": next_q.dict() if next_q else None,
                "progress": {
                    "current": state["current_q_index"],
                    "total": len(workflow.questions),
                },
                "is_finished": False,
            }
        if last_log.get("answer") is None:
            # 答案太短，尚未达到重试上限，要求用户重新作答
            state["history_logs"].pop()
            return {
                "retry": True,
                "retry_count": state["retry_count"],
                "message": "答案太简短，请提供更完整的回答",
                "question": current_q.dict(),
                "progress": {
                    "current": state["current_q_index"],
                    "total": len(workflow.questions),
                },
            }
    else:
        state["history_logs"][-1]["answer"] = " ".join(request.answer)

    result = check_attempt(request)
    state = workflow.evaluate_answer(state, result)

    if workflow.should_continue(state):
        next_q = workflow.get_current_question(state)
        return {
            "next_question": next_q.dict() if next_q else None,
            "progress": {
                "current": state["current_q_index"],
                "total": len(workflow.questions),
            },
            "is_finished": False,
        }

    state = workflow.aggregate_and_route(state)
    dim_block = _build_dimension_block(state)

    return {
        "is_finished": True,
        "final_result": {
            "persona": state["final_persona"],
            "route_action": state["route_action"],
            "trait_tags": state.get("trait_tags", []),
            **dim_block,
        },
    }


@router.get("/result/{user_id}", summary="获取最终画像结果")
def get_personality_result(user_id: str) -> dict:
    if user_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    state = _sessions[user_id]
    workflow = _get_workflow()

    if not workflow.is_finished(state):
        raise HTTPException(status_code=400, detail="评估尚未完成")

    dim_block = _build_dimension_block(state)

    return {
        "user_id": user_id,
        "final_result": {
            "persona": state["final_persona"],
            "route_action": state["route_action"],
            "trait_tags": state.get("trait_tags", []),
            **dim_block,
        },
        "history": state["history_logs"],
    }


@router.delete("/session/{user_id}", summary="结束并删除会话")
def end_session(user_id: str) -> dict:
    if user_id not in _sessions:
        raise HTTPException(status_code=404, detail="会话不存在")

    del _sessions[user_id]
    return {"message": "会话已结束"}
