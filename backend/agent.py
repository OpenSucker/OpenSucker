"""
Sucker Smart Trading Matrix AI Agent v1 — LangGraph Version
Institutional-grade trading assistance for retail investors.
"""
import json
import os
import uuid
import base64
import operator
from typing import Optional, List, Dict, Any, TypedDict, Annotated, Literal

# Database & Infrastructure
from database import (
    get_or_create_user, update_user_profile, get_user_profile,
    get_or_create_conversation, save_message, get_conversation_messages,
    get_db_stats, list_user_conversations,
    end_conversation,
)

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph, END

from modules import (
    Intent, detect_intent, detect_intent_full, set_intent_api_config,
    LanguageModel, SessionManager,
)
from modules.xy_prompts import (
    build_xy_system_prompt,
    get_role_name_cn as xy_get_role_name_cn,
    get_role_name_en as xy_get_role_name_en,
)
from modules.function_calling_engine import run_function_calling_loop

from dotenv import load_dotenv
load_dotenv() # Load from .env file

app = FastAPI(title="Sucker Smart Trading Matrix API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件与前端 (React 生产版本)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")

from fastapi.staticfiles import StaticFiles
if os.path.exists(os.path.join(FRONTEND_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "React Frontend not built. Please run 'npm run build' in frontend folder."

# 如果有 JS/CSS 静态资源可以这样挂载（当前 index.html 是单文件，暂时不需要，但为了扩展性保留）
# from fastapi.staticfiles import StaticFiles
# app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ============================================================
# 1. State & Profile Definitions
# ============================================================

class UserEntity(TypedDict, total=False):
    """User Entity - Cross-session financial profile"""
    risk_preference: Optional[str]      # conservative/moderate/aggressive
    investment_style: Optional[str]     # value/growth/speculative
    capital_size: Optional[str]         # small/medium/large
    cognitive_level: Optional[int]      # 1-5
    holdings: Optional[List[Dict]]      # [{"symbol": "NVDA", "qty": 10}]
    last_trade: Optional[Dict]
    historical_lessons: Optional[List[str]]
    watchlist: Optional[List[str]]
    api_trading_enabled: bool
    paper_trading_mode: bool

from operator import add
from typing import Annotated

class SuckerState(TypedDict, total=False):
    """Global Flow State for Sucker Matrix"""
    session_id: str
    message: str
    model_version: str
    user: UserEntity
    x_axis: str
    y_axis: str
    intent: str
    intent_cn: str
    task_chain: List[str]
    risk_level: int
    risk_reason: Optional[str]
    risk_redirected: bool
    response_message: str
    skill_used: str
    debug_steps: Annotated[List[str], add]
    tools_called: Annotated[List[Dict], add]  # 新增：记录所有工具调用
    history: List[Dict]
    _cached_intent: Dict

# ============================================================
# 2. Tool Instances
# ============================================================

API_KEY = os.environ.get("LLM_API_KEY", "")
BASE_URL = os.environ.get("LLM_API_BASE", "https://api.openai-next.com")
MODEL_MAIN = os.environ.get("LLM_API_MODEL", "gpt-4o")
api_config = {"api_key": API_KEY, "base_url": BASE_URL, "model": MODEL_MAIN}


sessions = SessionManager()
llm_api = LanguageModel(model_path=None, lora_path=None, api_config=api_config)
set_intent_api_config(api_config)

INTENT_CN = {
    "greeting": "打招呼", "chitchat": "闲聊",
    "market_analysis": "大盘分析", "stock_scan": "选股扫描",
    "trade_execution": "交易执行", "portfolio_audit": "持仓诊断",
    "risk_warning": "风险预警", "psychology_care": "情绪安抚",
    "confirm": "确认操作", "reset": "重置状态",
}

def get_llm(version: str = "api"):
    return llm_api

# ============================================================
# 3. Node Functions
# ============================================================

def profile_update(state: SuckerState) -> dict:
    """第一步：画像同步与初步意图识别 (Router Agent Pre-run)"""
    steps = list(state.get("debug_steps", []))
    user = dict(state.get("user", {}))
    msg = state.get("message", "")
    session = sessions.get_or_create(state.get("session_id"))
    
    # 将 DB 中的画像同步到内存 session
    session.cognitive_level = user.get("cognitive_level", 1)
    session.risk_preference = user.get("risk_preference", "moderate")
    session.holdings = user.get("holdings", [])

    # 调用 Router Agent 进行分析
    result = detect_intent_full(msg, session, user_profile=user)
    
    _cached_intent = {
        "intent": result.get("intent", "chitchat"),
        "x_axis": result.get("x_axis", "X1"),
        "y_axis": result.get("y_axis", "Y1"),
        "cognitive_level": result.get("cognitive_level", 1),
        "task_chain": result.get("task_chain", []),
    }
    
    return {"user": user, "_cached_intent": _cached_intent, "debug_steps": steps}

def node_intent_router(state: SuckerState) -> dict:
    steps = list(state.get("debug_steps", []))
    cached = state.get("_cached_intent")
    if cached:
        result = cached
    else:
        from modules.intent import _keyword_intent
        result = _keyword_intent(state.get("message", ""), sessions.get_or_create(state.get("session_id")))
    
    intent_str = result.get("intent", "chitchat")
    return {
        "intent": intent_str,
        "intent_cn": INTENT_CN.get(intent_str, intent_str),
        "x_axis": result.get("x_axis", "X1"),
        "y_axis": result.get("y_axis", "Y1"),
        "task_chain": result.get("task_chain", []),
        "debug_steps": steps,
    }

def node_risk_check(state: SuckerState) -> dict:
    msg = state.get("message", "").lower()
    risk_level = 0
    risk_reason = None
    if "all in" in msg or "全仓" in msg:
        risk_level = 2
        risk_reason = "警告：检测到过度投机倾向（All-in）。"
    return {"risk_level": risk_level, "risk_reason": risk_reason}

def generic_matrix_node(state: SuckerState, x: str) -> dict:
    y = state.get("y_axis", "Y1")
    cell_id = f"{x}{y}"
    user = state.get("user", {})
    session = sessions.get_or_create(state.get("session_id"))

    # 加载技能并构建增强 prompt
    from modules.skills_manager import build_system_prompt_with_skills
    base_prompt = build_xy_system_prompt(x, y, session)
    
    intent_str = state.get("intent", "chitchat")
    system_prompt, skill_summary = build_system_prompt_with_skills(base_prompt, cell_id, intent_str)

    if skill_summary:
        print(f"  ✅ 技能加载: [{cell_id}] {skill_summary}")

    # 兜底逻辑 (原生提示词模式)
    llm = get_llm(state.get("model_version", "api"))
    result = run_function_calling_loop(
        llm=llm,
        system_prompt=system_prompt,
        user_message=state.get("message", ""),
        history=state.get("history", []),
        user_profile=user,
        session=session,
        state=state,
        x_axis=x,
        y_axis=y,
        max_iterations=6
    )
    return {
        "response_message": result.get("content", ""),
        "skill_used": skill_summary,
        "user": user,
        "tools_called": result.get("tools_called", []),
        "debug_steps": [f"{cell_id}: 分析完成，使用方法论 [{skill_summary or '核心逻辑'}]"]
    }


def node_committee(state: SuckerState) -> dict:
    """
    Swarm Committee 模式：并行激活 X1, X2, X4 专家进行会诊。
    """
    print("  🤝 启动矩阵委员会共识会议 (Swarm Debate)...")
    experts = ["X1", "X2", "X4"]
    results = []
    
    for x in experts:
        res = generic_matrix_node(state, x)
        results.append(f"### {x} 专家意见:\n{res['response_message']}")
    
    combined = "\n\n".join(results)
    summary_prompt = f"你是一个首席投研审计师。请综合以下三个专家的意见，为用户提供一个最终的决策建议：\n\n{combined}"
    
    llm = get_llm(state.get("model_version", "api"))
    final_res = llm.chat_with_tools(
        messages=[{"role": "user", "content": summary_prompt}],
        temperature=0.3
    )
    
    return {
        "response_message": final_res.get("content", ""),
        "skill_used": "Swarm-Consensus (X1|X2|X4)",
        "debug_steps": ["COMMITTEE: 已综合多方专家意见达成共识矩阵方案。"]
    }

def node_X1(state: SuckerState) -> dict: return generic_matrix_node(state, "X1")
def node_X2(state: SuckerState) -> dict: return generic_matrix_node(state, "X2")
def node_X3(state: SuckerState) -> dict: return generic_matrix_node(state, "X3")
def node_X4(state: SuckerState) -> dict: return generic_matrix_node(state, "X4")
def node_X5(state: SuckerState) -> dict: return generic_matrix_node(state, "X5")

def respond(state: SuckerState) -> dict:
    return {"response_message": state.get("response_message", "处理完毕。")}

# ============================================================
# 4. Graph Construction
# ============================================================

workflow = StateGraph(SuckerState)

workflow.add_node("profile_update", profile_update)
workflow.add_node("intent_router", node_intent_router)
workflow.add_node("risk_check", node_risk_check)
workflow.add_node("node_X1", node_X1)
workflow.add_node("node_X2", node_X2)
workflow.add_node("node_X3", node_X3)
workflow.add_node("node_X4", node_X4)
workflow.add_node("node_X5", node_X5)
workflow.add_node("node_committee", node_committee)
workflow.add_node("respond", respond)

workflow.set_entry_point("profile_update")
workflow.add_edge("profile_update", "intent_router")

def route_after_router(state):
    if state["intent"] == "confirm": return "node_X3" # Example
    return "risk_check"

workflow.add_conditional_edges("intent_router", route_after_router)

def route_after_risk(state):
    if state["risk_level"] >= 2: return "node_X5" # Evolution/Care
    if state["intent"] == "committee": return "node_committee"
    x = state.get("x_axis", "X1")
    return f"node_{x}"

workflow.add_conditional_edges("risk_check", route_after_risk)

for node in ["node_X1", "node_X2", "node_X3", "node_X4", "node_X5", "node_committee"]:
    workflow.add_edge(node, "respond")

workflow.add_edge("respond", END)

agent_graph = workflow.compile()

# ============================================================
# 5. FastAPI Endpoints
# ============================================================

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: str
    model_version: str = "api"

class AgentResponse(BaseModel):
    message: str
    intent: str
    x_axis: str
    y_axis: str
    skill_used: str = ""
    user: Optional[Dict] = None
    tools: List[Dict] = []
    debug: Dict

@app.post("/api/chat")
async def chat(req: ChatRequest):
    user_id = req.user_id
    sid = req.session_id
    
    # 1. 确保用户存在 (修复 FOREIGN KEY 报错)
    # 获取数据库中的真实 ID (如果是旧数据，ID 可能是 UUID，指纹才是 user_id)
    user_rec = get_or_create_user(user_id)
    db_uid = user_rec["id"]
    
    # 2. 获取画像
    profile = get_user_profile(db_uid) or {}
    
    initial_state = {
        "session_id": sid,
        "message": req.message,
        "user": profile,
        "debug_steps": [],
        "history": [],
    }
    
    result = agent_graph.invoke(initial_state)
    
    # 3. 持久化存储 (使用 db_uid)
    conv_id = get_or_create_conversation(db_uid, sid)
    
    # 更新画像
    update_user_profile(db_uid, result.get("user", {}))
    
    # 存储用户消息
    save_message(
        conv_id, db_uid, "user", req.message,
        intent=result.get("intent"),
        intent_cn=result.get("intent_cn"),
        x_axis=result.get("x_axis"),
        y_axis=result.get("y_axis"),
        risk_level=result.get("risk_level", 0)
    )
    
    # 存储 AI 响应
    save_message(
        conv_id, db_uid, "assistant", result.get("response_message", ""),
        intent=result.get("intent"),
        x_axis=result.get("x_axis"),
        y_axis=result.get("y_axis")
    )
    
    return AgentResponse(
        message=result.get("response_message", ""),
        intent=result.get("intent", ""),
        x_axis=result.get("x_axis", ""),
        y_axis=result.get("y_axis", ""),
        skill_used=result.get("skill_used", ""),
        user=result.get("user"),
        tools=result.get("tools_called", []),
        debug={"steps": result.get("debug_steps", [])}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
