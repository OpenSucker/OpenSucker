"""
Function Calling Engine — ReAct Loop
====================================

OpenAI 标准 function calling 主循环。

工作流:
    1. 接收 system_prompt + user_message + history + state
    2. 把这些组装成 messages 数组, 加上 tools schema
    3. 调 LLM (chat_with_tools)
    4. 看 LLM 输出:
       - 有 tool_calls → 用 dispatcher 执行每个工具, 把结果作为 tool message 加进 messages, 回到 step 3
       - 没 tool_calls → LLM 给出最终答案, 退出循环
    5. 防死循环: 最多 MAX_ITERATIONS 轮, 超过强制结束

返回:
    {
        "content": str,                # 最终给用户看的回复
        "tool_calls_audit": List[Dict], # 所有跑过的工具(供 OpenAI adapter 透传给前端)
        "iterations": int,              # 实际循环次数
        "side_effects": Dict,           # 累积的副作用(画像更新/推荐列表/生图结果等)
        "error": Optional[str],
    }
"""

from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from .tool_schemas import get_tools_for_cell
from .tool_dispatcher import dispatch_all, ToolExecutionResult


# 防死循环 — 最多调几轮工具
MAX_ITERATIONS = 5


def run_function_calling_loop(
    *,
    llm,
    system_prompt: str,
    user_message: str,
    history: List[Dict],
    user_profile: Dict[str, Any],
    state: Optional[Dict[str, Any]] = None,
    image_base64: Optional[str] = None,
    session=None,
    face_analyzer=None,
    x_axis: str = "consult",
    y_axis: str = "explore",
    max_iterations: int = MAX_ITERATIONS,
) -> Dict[str, Any]:
    """
    Function calling 主循环。

    Args:
        llm:           LanguageModel 实例 (必须有 chat_with_tools 方法)
        system_prompt: 当前 cell 的 system prompt (来自 xy_prompts.build_xy_system_prompt)
        user_message:  当前轮用户消息
        history:       历史对话 (List[{"role","content"}])
        user_profile:  当前用户画像 dict
        state:         LangGraph state dict (可选, 副作用回写用)
        image_base64:  用户这一轮上传的照片 (供 analyze_face 工具用)
        session:       UserSession 实例 (供 recommend 工具读历史上下文)
        face_analyzer: FaceAnalyzer 实例 (供 analyze_face 工具用)
        x_axis/y_axis: 当前 cell, 用于 get_tools_for_cell 取工具子集
        max_iterations: 最多循环几轮

    Returns:
        见上方文件头注释的 dict 结构
    """
    # ── 1. 装配 messages ──
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt}
    ]
    # 历史消息(只保留 user/assistant, 跳过 tool 消息防止干扰)
    for h in (history or []):
        role = h.get("role")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": h.get("content", "")})
    # 当前轮用户消息
    messages.append({"role": "user", "content": user_message})

    # ── 2. 执行上下文 (供 dispatcher 注入) ──
    context: Dict[str, Any] = {
        "user_profile": dict(user_profile or {}),  # 复制一份, 副作用累积写入这个
        "image_base64": image_base64,
        "session": session,
        "llm": llm,
        "state": state or {},
        "face_analyzer": face_analyzer,
    }

    # ── 3. 工具列表 ──
    tools = get_tools_for_cell(x_axis=x_axis, y_axis=y_axis)

    # ── 4. ReAct loop ──
    audit_log: List[Dict[str, Any]] = []
    accumulated_side_effects: Dict[str, Any] = {}
    tools_called: List[Dict[str, Any]] = []
    final_content: str = ""
    error: Optional[str] = None
    iter_count = 0

    for i in range(max_iterations):
        iter_count = i + 1

        # 调 LLM
        resp = llm.chat_with_tools(
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1500,
            temperature=0.7,
        )

        if resp.get("error"):
            error = resp["error"]
            final_content = f"(LLM 调用失败: {error})"
            break

        tool_calls = resp.get("tool_calls") or []
        content = resp.get("content") or ""

        # 记录工具调用 (先占位, 调度后回填 result/success)
        round_records: List[Dict[str, Any]] = []
        for tc in tool_calls:
            try:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                rec = {"id": getattr(tc, "id", None), "name": fn_name, "args": fn_args}
                tools_called.append(rec)
                round_records.append(rec)
            except Exception:
                round_records.append(None)

        # ── 没要求调工具 → LLM 给最终答案 ──
        if not tool_calls:
            final_content = content
            break

        # ── 要求调工具 → 执行 ──
        # 把 LLM 的 assistant message (含 tool_calls) 加入 messages
        assistant_msg = {
            "role": "assistant",
            "content": content,
            "tool_calls": tool_calls,
        }
        if resp.get("reasoning_content"):
            assistant_msg["reasoning_content"] = resp["reasoning_content"]
        messages.append(assistant_msg)

        # 执行所有 tool_calls
        results: List[ToolExecutionResult] = dispatch_all(tool_calls, context)

        # 把执行结果回填到对应的 tools_called 记录里 (供前端显示)
        for r in results:
            for rec in round_records:
                if rec and rec.get("id") == r.tool_call_id:
                    rec["success"] = bool(r.success)
                    try:
                        rec["result"] = json.loads(r.result_for_llm) if isinstance(r.result_for_llm, str) else r.result_for_llm
                    except Exception:
                        rec["result"] = r.result_for_llm
                    if r.error:
                        rec["error"] = r.error
                    break

        for r in results:
            # 把 tool 结果作为 tool message 加入, 喂给 LLM 下一轮
            messages.append({
                "role": "tool",
                "tool_call_id": r.tool_call_id,
                "content": r.result_for_llm,
            })

            # 累积副作用
            for k, v in (r.side_effects or {}).items():
                if k == "user_profile_updates" and isinstance(v, dict):
                    context["user_profile"].update(v)
                    accumulated_side_effects.setdefault("user_profile_updates", {}).update(v)
                else:
                    accumulated_side_effects[k] = v

            # 累积 audit log
            if r.audit:
                audit_log.append({"id": r.tool_call_id, **r.audit})

        # 继续下一轮 LLM 决策
        continue

    else:
        # 跑满 max_iterations 还没结束
        final_content = f"(对话过于复杂, 已尝试 {max_iterations} 轮工具调用仍未得到最终答案。请简化你的问题。)"
        error = "max_iterations_exceeded"

    return {
        "content": final_content,
        "tool_calls_audit": audit_log,
        "tools_called": tools_called, # 新增结构化调用列表
        "iterations": iter_count,
        "side_effects": accumulated_side_effects,
        "user_profile_after": context["user_profile"],
        "error": error,
    }
