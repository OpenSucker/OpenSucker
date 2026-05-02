from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.domains.quiz.schemas import (
    AttemptRequest,
    AttemptResult,
    Question,
    QuestionListResponse,
    QuizResultRequest,
    QuizResultResponse,
)
from app.domains.quiz.service import analyze_quiz, check_attempt, get_question, list_questions, random_questions

router = APIRouter()


@router.get("/questions", response_model=QuestionListResponse, summary="获取题目列表")
def api_list_questions(
    topic: str | None = Query(default=None, description="按主题过滤：量化交易/交易终端/券商柜台/风险识别/情景判断"),
    difficulty: int | None = Query(default=None, ge=1, le=3, description="按难度过滤：1=基础 2=进阶 3=高难"),
    type: str | None = Query(default=None, description="按题型过滤：single/multiple/qa"),
) -> QuestionListResponse:
    return list_questions(topic=topic, difficulty=difficulty, q_type=type)


@router.get("/questions/random", response_model=QuestionListResponse, summary="随机抽题")
def api_random_questions(
    topic: str | None = Query(default=None, description="按主题随机抽题"),
    count: int = Query(default=5, ge=1, le=20, description="抽题数量"),
) -> QuestionListResponse:
    return random_questions(topic=topic, count=count)


@router.get("/questions/{question_id}", response_model=Question, summary="获取单道题目")
def api_get_question(question_id: str) -> Question:
    q = get_question(question_id)
    if q is None:
        raise HTTPException(status_code=404, detail=f"题目 {question_id} 不存在")
    return q


@router.post("/attempt", response_model=AttemptResult, summary="提交答案")
def api_attempt(request: AttemptRequest) -> AttemptResult:
    return check_attempt(request)


@router.post("/result", response_model=QuizResultResponse, summary="提交全部答案，返回测试结果")
def api_quiz_result(request: QuizResultRequest) -> QuizResultResponse:
    return analyze_quiz(request)
