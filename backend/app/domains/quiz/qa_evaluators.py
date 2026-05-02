"""
QA 题评分模块

优先级：LLM_API_KEY + LLM_BASE_URL（OpenAI 兼容接口）→ ANTHROPIC_API_KEY → 本地 Ollama。
返回 (raw_score, confidence, reasoning)：
- raw_score: 0.0 / 0.5 / 1.0
- confidence: 0.0~1.0
- reasoning: 一句话说明
"""

from __future__ import annotations

import json
import os
from typing import Callable

QAEvaluator = Callable[[str], tuple[float, float, str]]

_anthropic_client = None
_OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
_OLLAMA_MODEL = "qwen2.5:3b"

_QA_RUBRICS: dict[str, dict[str, str]] = {
    "q031": {
        "stem": "你买了一套房子，300万买入，后来行情不好200万卖出。过了一段时间，房价继续下跌，你又花100万把这套房子买回来了。折腾这一圈到现在，你是赚了还是亏了？具体赚/亏了多少钱？你是怎么算的？",
        "rubric": (
            "满分标准（1.0）：方向正确（亏损），金额正确（100万），并能说明现金流/净资产/两笔交易独立的逻辑。\n"
            "半分标准（0.5）：方向正确，金额正确，但没有逻辑说明；或方向正确、有逻辑但金额有偏差。\n"
            "零分标准（0.0）：方向错误（说赚钱）或完全没有回答。"
        ),
    },
    "q032": {
        "stem": "你是水果摊老板，花500元进了一箱车厘子，今天市价跌到300元，明天就会烂掉归零。隔壁果汁店老板出价200元现金收购。你会怎么选？为什么？",
        "rubric": (
            "满分标准（1.0）：明确选择卖给果汁店，并能解释沉没成本/止损/流动性/机会成本等逻辑中的至少一个。\n"
            "半分标准（0.5）：选择卖出但没有给出逻辑支撑，只是直觉行动。\n"
            "零分标准（0.0）：选择不卖，或试图继续摆摊，或答案混乱。"
        ),
    },
    "q033": {
        "stem": "朋友推荐一个策略：胜率90%，赢时赚总资金10%，输时亏总资金50%。复利模式，10次交易赢9次输1次。这是好策略吗？你最终是赚翻了、微赚还是亏损？",
        "rubric": (
            "满分标准（1.0）：判断这是差策略，并能用几何复利逻辑说明（1.1^9 × 0.5 ≈ 1.17，约赚17%），或提到波动率拖累/不对称风险。\n"
            "半分标准（0.5）：判断是差策略，但没有计算过程，只是直觉或定性描述。\n"
            "零分标准（0.0）：判断是好策略，或答案混乱无法判断方向。"
        ),
    },
}

_SYSTEM_PROMPT = """\
你是一道金融心理测试题的阅卷人。
你的任务是根据评分标准，对学生的回答打分。
只输出一个 JSON 对象，格式如下（不要有任何其他文字）：
{"score": <0.0或0.5或1.0>, "confidence": <0.0到1.0之间的小数>, "reasoning": "<一句话说明>"}\
"""


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _anthropic_client


def _evaluate_with_openai_compat(question_id: str, answer: str) -> tuple[float, float, str]:
    import httpx

    api_key = os.environ.get("LLM_API_KEY", "")
    base_url = os.environ.get("LLM_BASE_URL", "").rstrip("/")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

    rubric_info = _QA_RUBRICS[question_id]
    user_prompt = (
        f"题目：{rubric_info['stem']}\n\n"
        f"评分标准：\n{rubric_info['rubric']}\n\n"
        f"学生回答：{answer}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 256,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    url = f"{base_url}/v1/chat/completions"

    for attempt in range(3):
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
            return _parse_llm_response(text)
        except Exception as e:
            if attempt == 2:
                return 0.0, 0.5, f"OpenAI 兼容接口评分失败：{e}"
    return 0.0, 0.5, "评分失败"


def _parse_llm_response(text: str) -> tuple[float, float, str]:
    data = json.loads(text.strip())
    score = float(data["score"])
    confidence = float(data.get("confidence", 0.9))
    reasoning = str(data.get("reasoning", ""))
    score = min([0.0, 0.5, 1.0], key=lambda v: abs(v - score))
    return score, confidence, reasoning


def _evaluate_with_anthropic(question_id: str, answer: str) -> tuple[float, float, str]:
    rubric_info = _QA_RUBRICS[question_id]
    user_prompt = (
        f"题目：{rubric_info['stem']}\n\n"
        f"评分标准：\n{rubric_info['rubric']}\n\n"
        f"学生回答：{answer}"
    )
    client = _get_anthropic_client()
    for attempt in range(3):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return _parse_llm_response(message.content[0].text)
        except Exception as e:
            if attempt == 2:
                return 0.0, 0.5, f"Anthropic 评分失败：{e}"
    return 0.0, 0.5, "评分失败"


def _evaluate_with_ollama(question_id: str, answer: str) -> tuple[float, float, str]:
    import urllib.request

    rubric_info = _QA_RUBRICS[question_id]
    user_prompt = (
        f"题目：{rubric_info['stem']}\n\n"
        f"评分标准：\n{rubric_info['rubric']}\n\n"
        f"学生回答：{answer}"
    )
    payload = json.dumps({
        "model": _OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.0},
    }).encode()

    for attempt in range(3):
        try:
            req = urllib.request.Request(
                _OLLAMA_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
            text = data["message"]["content"]
            return _parse_llm_response(text)
        except Exception as e:
            if attempt == 2:
                return 0.0, 0.5, f"Ollama 评分失败：{e}"
    return 0.0, 0.5, "评分失败"


def _llm_evaluate(question_id: str, answer: str) -> tuple[float, float, str]:
    if question_id not in _QA_RUBRICS:
        return 0.0, 0.5, f"未找到题目 {question_id} 的评分标准"

    if os.environ.get("LLM_API_KEY") and os.environ.get("LLM_BASE_URL"):
        return _evaluate_with_openai_compat(question_id, answer)

    if os.environ.get("ANTHROPIC_API_KEY"):
        return _evaluate_with_anthropic(question_id, answer)

    return _evaluate_with_ollama(question_id, answer)


def evaluate_q031(answer: str) -> tuple[float, float, str]:
    return _llm_evaluate("q031", answer)


def evaluate_q032(answer: str) -> tuple[float, float, str]:
    return _llm_evaluate("q032", answer)


def evaluate_q033(answer: str) -> tuple[float, float, str]:
    return _llm_evaluate("q033", answer)


QA_EVALUATORS: dict[str, QAEvaluator] = {
    "q031": evaluate_q031,
    "q032": evaluate_q032,
    "q033": evaluate_q033,
}


def register_qa_evaluator(question_id: str, evaluator: QAEvaluator) -> None:
    QA_EVALUATORS[question_id] = evaluator


def get_qa_evaluator(question_id: str) -> QAEvaluator | None:
    return QA_EVALUATORS.get(question_id)


def has_custom_evaluator(question_id: str) -> bool:
    return question_id in QA_EVALUATORS


def fallback_qa_evaluation(answer: str, keywords: list[str]) -> tuple[float, float, str]:
    """兜底逻辑，仅用于没有注册评分函数的题目。"""
    user_text = answer.lower()
    matched = [kw for kw in keywords if kw.lower() in user_text]
    ratio = len(matched) / len(keywords) if keywords else 0.0

    if ratio >= 0.8:
        return 1.0, 0.7, f"关键词匹配率 {ratio:.0%}"
    elif ratio >= 0.5:
        return 0.5, 0.7, f"关键词匹配率 {ratio:.0%}"
    else:
        return 0.0, 0.7, f"关键词匹配率 {ratio:.0%}"
