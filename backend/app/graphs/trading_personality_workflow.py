from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph

from app.core.scoring_config import DIMENSION_MAX_SCORES, scoring_config
from app.domains.quiz.schemas import Question, AttemptResult


class TradingPsychologyState(TypedDict, total=False):
    user_id: str
    current_q_index: int
    history_logs: list[dict]
    trigger_score: float
    execution_score: float
    attribution_score: float
    trait_tags: list[str]
    final_persona: str
    persona_description: str
    route_action: str
    retry_count: int
    is_finished: bool


def _to_level(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.6:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def initialize_state(user_id: str) -> TradingPsychologyState:
    return TradingPsychologyState(
        user_id=user_id,
        current_q_index=0,
        history_logs=[],
        trigger_score=0.0,
        execution_score=0.0,
        attribution_score=0.0,
        trait_tags=[],
        final_persona="",
        route_action="",
        retry_count=0,
        is_finished=False,
    )


def dispatcher_node(state: TradingPsychologyState, questions: list[Question]) -> TradingPsychologyState:
    current_q = questions[state["current_q_index"]]
    state["history_logs"].append({
        "question_id": current_q.id,
        "question_text": current_q.stem,
        "question_type": current_q.type,
        "difficulty": current_q.difficulty,
        "answer": None,
        "result": None,
    })
    return state


def validation_node(state: TradingPsychologyState, answer: str) -> TradingPsychologyState:
    if not answer or len(answer.strip()) < 3:
        state["retry_count"] = state["retry_count"] + 1
        if state["retry_count"] >= scoring_config.validation.max_retries:
            state["trait_tags"].append("disengaged")
            state["history_logs"][-1]["answer"] = answer
            state["history_logs"][-1]["skipped"] = True
            state["current_q_index"] = state["current_q_index"] + 1
            state["retry_count"] = 0
    else:
        state["history_logs"][-1]["answer"] = answer
        state["retry_count"] = 0
    return state


def evaluation_node(state: TradingPsychologyState, result: AttemptResult) -> TradingPsychologyState:
    state["history_logs"][-1]["result"] = result.model_dump()

    for dim, score in result.dimension_scores.items():
        if dim == "trigger":
            state["trigger_score"] = state.get("trigger_score", 0.0) + score
        elif dim == "execution":
            state["execution_score"] = state.get("execution_score", 0.0) + score
        elif dim == "attribution":
            state["attribution_score"] = state.get("attribution_score", 0.0) + score

    if result.raw_score >= 0.8:
        dominant_dim = max(result.dimension_scores, key=result.dimension_scores.get)
        state["trait_tags"].append(f"{dominant_dim}_{_to_level(result.raw_score)}")

    state["current_q_index"] = state["current_q_index"] + 1
    state["retry_count"] = 0
    return state


def aggregation_and_route_node(state: TradingPsychologyState, total_questions: int) -> TradingPsychologyState:
    trigger_norm = state.get("trigger_score", 0.0) / DIMENSION_MAX_SCORES["trigger"]
    execution_norm = state.get("execution_score", 0.0) / DIMENSION_MAX_SCORES["execution"]
    attribution_norm = state.get("attribution_score", 0.0) / DIMENSION_MAX_SCORES["attribution"]

    base_quant_purity = (
        trigger_norm * scoring_config.dimension.trigger +
        execution_norm * scoring_config.dimension.execution +
        attribution_norm * scoring_config.dimension.attribution
    )

    dimension_norms = {
        "trigger": trigger_norm,
        "execution": execution_norm,
        "attribution": attribution_norm,
    }
    quant_purity = scoring_config.shortfall_penalty.apply_penalty(base_quant_purity, dimension_norms)

    if quant_purity < scoring_config.route.emotional:
        state["final_persona"] = "跟着感觉走"
        state["persona_description"] = "今天心情好，买一点？\n涨了觉得自己天赋异禀，跌了觉得全是庄家的锅。其实两件事都跟你没什么关系。不用担心，大部分人都是从这里出发的。"
        state["route_action"] = "REDIRECT_TO_EDUCATION_AND_LIMIT_LEVERAGE"
    elif quant_purity < scoring_config.route.retail:
        state["final_persona"] = "靠直觉交易"
        state["persona_description"] = "止损线？设了，但不一定用。\n消息一来手就痒，道理都懂，就是那条止损线每次都能找到理由再往后挪一格。不是不行，就是规则还没长进肌肉里。"
        state["route_action"] = "REDIRECT_TO_EDUCATION_AND_LIMIT_LEVERAGE"
    elif quant_purity < scoring_config.route.developing:
        state["final_persona"] = "开始有方法了"
        state["persona_description"] = "脑子及格了，手还在补课。\n该看的数据会看，止损也知道要设。唯一的问题是到了真实亏损面前，计划偶尔会原地消失。框架是有的，就差稳定复现。"
        state["route_action"] = "UNLOCK_BASIC_TOOLS_AND_GUIDED_STRATEGIES"
    elif quant_purity < scoring_config.route.advanced:
        state["final_persona"] = "想清楚再动手"
        state["persona_description"] = "不是冲动型选手，难得。\n进场前有逻辑，出场后会复盘，不会把运气当实力、把亏损赖给大盘。偶尔感觉还是会来凑个热闹，但基本能摁住。"
        state["route_action"] = "UNLOCK_GRID_BOTS_AND_CONDITIONAL_ORDERS"
    else:
        state["final_persona"] = "数据说话"
        state["persona_description"] = "挺无聊的，但挺有效的。\n不追热点，不听小道消息，赚了不膨胀，亏了不崩溃。用数据做决定、用规则压感觉，然后把结果交给概率。市场里这种人不多，但赢面确实大一点。"
        state["route_action"] = "OPEN_API_ACCESS_AND_BACKTEST_ENGINE"

    state["trait_tags"] = list(dict.fromkeys(state.get("trait_tags", [])))
    state["is_finished"] = True
    state["_dimension_norms"] = dimension_norms
    state["_base_quant_purity"] = base_quant_purity
    state["_final_quant_purity"] = quant_purity
    return state


class TradingPersonalityWorkflow:
    def __init__(self, questions: list[Question]):
        self.questions = questions
        self.workflow = StateGraph(TradingPsychologyState)

    def initialize(self, user_id: str) -> TradingPsychologyState:
        return initialize_state(user_id)

    def get_current_question(self, state: TradingPsychologyState) -> Question | None:
        if state["current_q_index"] >= len(self.questions):
            return None
        return self.questions[state["current_q_index"]]

    def dispatch(self, state: TradingPsychologyState) -> TradingPsychologyState:
        return dispatcher_node(state, self.questions)

    def validate_answer(self, state: TradingPsychologyState, answer: str) -> TradingPsychologyState:
        return validation_node(state, answer)

    def evaluate_answer(self, state: TradingPsychologyState, result: AttemptResult) -> TradingPsychologyState:
        return evaluation_node(state, result)

    def aggregate_and_route(self, state: TradingPsychologyState) -> TradingPsychologyState:
        return aggregation_and_route_node(state, len(self.questions))

    def is_finished(self, state: TradingPsychologyState) -> bool:
        return state.get("is_finished", False)

    def should_continue(self, state: TradingPsychologyState) -> bool:
        return state["current_q_index"] < len(self.questions)


def create_personality_workflow(questions: list[Question]) -> TradingPersonalityWorkflow:
    return TradingPersonalityWorkflow(questions)
