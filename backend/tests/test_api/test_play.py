from dotenv import load_dotenv
load_dotenv()

import pytest
from fastapi.testclient import TestClient
from app.main import app

USER_ID = "test_play_consistency"

SINGLE_ANSWERS = [
    ("q021", ["A"]),
    ("q022", ["B"]),
    ("q023", ["C"]),
    ("q024", ["D"]),
    ("q025", ["A"]),
    ("q026", ["B"]),
    ("q027", ["A"]),
    ("q028", ["B"]),
    ("q029", ["C"]),
    ("q030", ["D"]),
]

QA_ANSWERS = [
    ("q031", "亏了200万。300万买入200万卖出亏了100万，后来再花100万买回，两笔合计净流出200万。"),
    ("q032", "卖给果汁店收200元。500元进货是沉没成本不可回收，现在继续摆摊明天必然烂掉归零，200元现金比零强，止损是唯一理性选择。"),
    ("q033", "差策略。1.1的9次方约2.36再乘以0.5等于1.18，只赚18%。胜率90%看起来高，但单次亏50%在复利下破坏力极大，远超9次10%的积累，期望收益低而尾部风险大。"),
]


@pytest.fixture
def client():
    return TestClient(app)


def _post(client, answer=None):
    body = {"user_id": USER_ID}
    if answer is not None:
        body["answer"] = answer
    r = client.post("/api/v1/play", json=body)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    return r.json()


def test_full_quiz_flow(client):
    print()

    # 开始会话
    d = _post(client)
    assert d["status"] == "question"
    assert d["progress"]["current"] == 0
    assert d["progress"]["total"] == 13
    assert d["question"]["id"] == "q021"
    print(f"[开始会话] 第一题: {d['question']['id']}  进度: {d['progress']['current']}/{d['progress']['total']}")

    # 断点恢复
    d2 = _post(client)
    assert d2["question"]["id"] == d["question"]["id"]
    print(f"[断点恢复] 返回同一题: {d2['question']['id']} ✓")

    # 10 道单选
    print()
    print("── 单选题 ──────────────────────────")
    for expected_id, answer in SINGLE_ANSWERS:
        assert d["question"]["id"] == expected_id
        d = _post(client, answer)
        assert d["status"] == "question"
        print(f"  {expected_id} 答 {answer[0]}  →  下一题: {d['question']['id']}  进度: {d['progress']['current']}/13")

    # 到达问答题 q031
    assert d["question"]["id"] == "q031"
    assert d["progress"]["current"] == 10

    # retry 测试
    print()
    print("── 问答题 ──────────────────────────")
    d_retry = _post(client, ["亏了"])
    assert d_retry["status"] == "retry"
    assert d_retry["retry_count"] == 1
    assert d_retry["question"]["id"] == "q031"
    assert "简短" in d_retry["message"]
    print(f"  q031 短答案  →  status: {d_retry['status']}  retry_count: {d_retry['retry_count']}  message: {d_retry['message']}")

    # 3 道问答题正式回答
    for expected_id, answer_text in QA_ANSWERS:
        assert d["question"]["id"] == expected_id
        d = _post(client, [answer_text])
        if expected_id != "q033":
            assert d["status"] == "question"
            print(f"  {expected_id} 已评分  →  下一题: {d['question']['id']}  进度: {d['progress']['current']}/13")
        else:
            assert d["status"] == "finished"
            print(f"  {expected_id} 已评分  →  status: {d['status']}")

    # 最终结果
    assert d["status"] == "finished"
    assert d["progress"]["current"] == 13
    assert d["progress"]["pct"] == 1.0
    assert d["question"] is None

    result = d["result"]
    assert result["persona"] in ("跟着感觉走", "靠直觉交易", "开始有方法了", "想清楚再动手", "数据说话")
    assert result["route_action"] != ""
    assert 0.0 <= result["scoring_details"]["final_quant_purity"] <= 1.0
    for dim in ("trigger", "execution", "attribution"):
        assert dim in result["dimension_scores"]
        assert 0.0 <= result["dimension_scores"][dim]["normalized"] <= 1.0

    print()
    print("── 最终结果 ─────────────────────────")
    print(f"  persona       : {result['persona']}")
    print(f"  route_action  : {result['route_action']}")
    print(f"  trait_tags    : {result['trait_tags']}")
    ds = result["dimension_scores"]
    print(f"  trigger       : {ds['trigger']['score']:.2f}  (normalized {ds['trigger']['normalized']:.3f})")
    print(f"  execution     : {ds['execution']['score']:.2f}  (normalized {ds['execution']['normalized']:.3f})")
    print(f"  attribution   : {ds['attribution']['score']:.2f}  (normalized {ds['attribution']['normalized']:.3f})")
    sd = result["scoring_details"]
    print(f"  quant_purity  : base {sd['base_quant_purity']:.4f}  →  final {sd['final_quant_purity']:.4f}")

    # 幂等
    d_idem = _post(client)
    assert d_idem["status"] == "finished"
    assert d_idem["result"]["persona"] == result["persona"]
    assert d_idem["result"]["scoring_details"]["final_quant_purity"] == result["scoring_details"]["final_quant_purity"]
    print()
    print(f"[幂等验证] 重复调用结果一致 ✓")
