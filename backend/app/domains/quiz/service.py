from __future__ import annotations

import json
import random
from pathlib import Path

from app.core.scoring_config import (
    get_option_dimension_scores,
    get_qa_dimension_mapping,
    scoring_config,
)
from app.domains.quiz.qa_evaluators import (
    fallback_qa_evaluation,
    get_qa_evaluator,
    has_custom_evaluator,
)
from app.domains.quiz.schemas import (
    AttemptRequest,
    AttemptResult,
    DiagnosisResult,
    Question,
    QuestionListResponse,
    QuizAnswerItem,
    QuizResultRequest,
    QuizResultResponse,
)

_DATA_FILE = Path(__file__).parent.parent.parent.parent / "data" / "questions.json"

_questions: list[Question] = []


def _load() -> None:
    global _questions
    if _questions:
        return
    raw = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    for q in raw:
        if "score_k" not in q:
            q["score_k"] = scoring_config.get_k(q.get("difficulty", 1))
        if "score_b" not in q:
            q["score_b"] = 0.0
    _questions = [Question(**q) for q in raw]


def list_questions(
    topic: str | None = None,
    difficulty: int | None = None,
    q_type: str | None = None,
) -> QuestionListResponse:
    _load()
    result = _questions
    if topic:
        result = [q for q in result if q.topic == topic]
    if difficulty:
        result = [q for q in result if q.difficulty == difficulty]
    if q_type:
        result = [q for q in result if q.type == q_type]
    return QuestionListResponse(total=len(result), questions=result)


def get_question(question_id: str) -> Question | None:
    _load()
    for q in _questions:
        if q.id == question_id:
            return q
    return None


def random_questions(
    topic: str | None = None,
    count: int = 5,
) -> QuestionListResponse:
    _load()
    pool = _questions if not topic else [q for q in _questions if q.topic == topic]
    sample = random.sample(pool, min(count, len(pool)))
    return QuestionListResponse(total=len(sample), questions=sample)


def check_attempt(request: AttemptRequest) -> AttemptResult:
    _load()
    question = get_question(request.question_id)
    if question is None:
        return AttemptResult(
            question_id=request.question_id,
            is_correct=False,
            score=0,
            correct_answer=[],
            explanation="题目不存在",
        )

    if question.type in ("single", "multiple"):
        given = sorted(a.upper() for a in request.answer)
        expected = sorted(a.upper() for a in question.correct_answer)
        is_correct = given == expected

        # 选择题：按用户实际选项取三维得分，再乘以难度系数 k
        k = question.score_k
        raw_dim = get_option_dimension_scores(question.id, given[0] if given else "")
        dimension_scores = {dim: score * k for dim, score in raw_dim.items()}

        return AttemptResult(
            question_id=request.question_id,
            is_correct=is_correct,
            score=100 if is_correct else 0,
            correct_answer=question.correct_answer,
            raw_score=1.0 if is_correct else 0.0,
            confidence=1.0,
            weighted_score=question.weighted_score(1.0 if is_correct else 0.0),
            max_possible=question.max_score,
            dimension_scores=dimension_scores,
        )

    # 问答题
    user_text = " ".join(request.answer)
    if has_custom_evaluator(question.id):
        evaluator = get_qa_evaluator(question.id)
        raw_score, confidence, reasoning = evaluator(user_text) if evaluator else (0.0, 0.5, "")
    else:
        raw_score, confidence, reasoning = fallback_qa_evaluation(user_text, question.keywords)

    weighted = question.weighted_score(raw_score, confidence)
    score = round(weighted / question.max_score * 100) if question.max_score > 0 else 0

    dim_ratios = get_qa_dimension_mapping(question.id)
    dimension_scores = {dim: weighted * ratio for dim, ratio in dim_ratios.items()}

    matched_keywords = [kw for kw in question.keywords if kw.lower() in user_text.lower()]

    return AttemptResult(
        question_id=request.question_id,
        is_correct=raw_score >= 0.5,
        score=score,
        correct_answer=question.correct_answer,
        raw_score=raw_score,
        confidence=confidence,
        weighted_score=weighted,
        max_possible=question.max_score,
        dimension_scores=dimension_scores,
        matched_keywords=matched_keywords,
        llm_reasoning=reasoning,
    )


_DIAGNOSES: dict[str, dict[str, str]] = {
    "all": {
        "label": "三维均衡",
        "title": "真的挺少见",
        "body": "数据先行、规则压感觉、不从结果倒推——这三件事你都做到了。不是说完美，是说结构上没有明显的窟窿。市场里大多数人只满足其中一条。",
    },
    "trigger": {
        "label": "最薄弱：Trigger",
        "title": "你容易被「有人说」带跑",
        "body": "不是说你傻，是说进场这个动作经常被别人的话触发，而不是你自己查完数据之后触发。这个问题很常见，修起来也不难——养成「先查，再决定」的习惯就行。难的是每次都要忍住那股冲动。",
    },
    "execution": {
        "label": "最薄弱：Execution",
        "title": "脑子懂，手跟不上",
        "body": "止损、不追涨、沉没成本不相关——这些你都明白。但真到那个时刻，感觉还是会压过规则。不是意志力问题，是规则没有提前写死。没有写下来的规则，在压力下等于没有。",
    },
    "attribution": {
        "label": "最薄弱：Attribution",
        "title": "你把运气当成能力了",
        "body": "赚了觉得是自己判断对，亏了觉得是时机不好——这套解释方式会让你越来越自信，但和实际胜率没什么关系。最难受的一类人：有时候赚很多，但不知道为什么，所以也不知道下次会不会重现。",
    },
}

_DIM_MAX = {"trigger": 7.1, "execution": 11.68, "attribution": 10.52}


def analyze_quiz(request: QuizResultRequest) -> QuizResultResponse:
    _load()
    totals: dict[str, float] = {"trigger": 0.0, "execution": 0.0, "attribution": 0.0}

    for item in request.answers:
        result = check_attempt(AttemptRequest(question_id=item.question_id, answer=item.answer))
        for dim, score in result.dimension_scores.items():
            if dim in totals:
                totals[dim] += score

    pcts: dict[str, int] = {
        d: round((totals[d] / _DIM_MAX[d]) * 100) for d in totals
    }

    all_high = all(v >= 70 for v in pcts.values())
    min_dim = min(pcts, key=lambda d: pcts[d])
    weakest = "all" if all_high else min_dim

    d = _DIAGNOSES[weakest]
    return QuizResultResponse(
        dimension_pcts=pcts,
        weakest_dim=weakest,
        all_high=all_high,
        diagnosis=DiagnosisResult(label=d["label"], title=d["title"], body=d["body"]),
    )
