"""
Tool Dispatcher — Sucker 金融版
把 LLM 输出的 tool_calls 路由到真实（或模拟）的金融数据函数
"""
from __future__ import annotations
import json
import time
from typing import Any, Dict, List, Optional, Tuple


class ToolExecutionResult:
    def __init__(
        self,
        tool_call_id: str,
        tool_name: str,
        success: bool,
        result_for_llm: str,
        side_effects: Dict[str, Any] = None,
        audit: Dict[str, Any] = None,
        error: Optional[str] = None,
    ):
        self.tool_call_id = tool_call_id
        self.tool_name = tool_name
        self.success = success
        self.result_for_llm = result_for_llm
        self.side_effects = side_effects or {}
        self.audit = audit or {}
        self.error = error


def dispatch_tool_call(
    tool_call: Any,
    context: Dict[str, Any],
) -> ToolExecutionResult:
    # 适配 OpenAI SDK 对象模式
    tc_id = getattr(tool_call, "id", "call_unknown")
    fn = getattr(tool_call, "function", None)
    if not fn:
        return ToolExecutionResult(tc_id, "unknown", False, "ERROR: No function in tool_call")
    
    name = getattr(fn, "name", "")
    raw_args = getattr(fn, "arguments", "{}")

    try:
        args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
    except Exception as e:
        return ToolExecutionResult(tc_id, name, False, f"ERROR: JSON parse failed: {e}")

    # --- 模拟金融工具实现 ---
    
    if name == "get_market_sentiment":
        asset = args.get("asset", "大盘")
        # 模拟数据
        result = {"asset": asset, "sentiment_score": 0.75, "label": "Greed", "source_count": 1250}
        return ToolExecutionResult(tc_id, name, True, json.dumps(result))

    elif name == "get_technical_indicators":
        symbol = args.get("symbol", "UNKNOWN")
        indicators = args.get("indicators", [])
        # 模拟数据
        data = {ind: 50.0 for ind in indicators}
        if "RSI" in indicators: data["RSI"] = 72.5
        if "MACD" in indicators: data["MACD"] = {"dif": 0.5, "dea": 0.3, "hist": 0.2}
        return ToolExecutionResult(tc_id, name, True, json.dumps({"symbol": symbol, "indicators": data}))

    elif name == "calculate_position_size":
        # 严格校验逻辑：LLM 提供参数，代码执行计算
        win_rate = args.get("win_rate", 0.5)
        p_l_ratio = args.get("profit_loss_ratio", 2.0)
        # 凯利公式: f* = (bp - q) / b = (p(b+1)-1) / b
        kelly_f = (win_rate * (p_l_ratio + 1) - 1) / p_l_ratio
        kelly_f = max(0, min(kelly_f, 0.2)) # 强制风控：单标的不超过 20%
        
        result = {
            "suggested_ratio": f"{kelly_f*100:.2f}%",
            "formula": "Kelly Criterion",
            "risk_warning": "Position capped at 20% by Risk Barrier."
        }
        return ToolExecutionResult(tc_id, name, True, json.dumps(result))

    elif name == "get_stock_quote":
        symbol = args.get("symbol", "UNKNOWN")
        # 模拟实时数据
        quote = {"symbol": symbol, "price": 450.23, "change_pct": "+1.2%", "volume": "25.4M"}
        return ToolExecutionResult(tc_id, name, True, json.dumps(quote))

    elif name == "analyze_macro_data":
        metric = args.get("metric", "FED_RATE")
        # 模拟宏观数据
        macro = {"metric": metric, "value": "5.25%-5.50%", "status": "Stable", "next_meeting": "2026-06-15"}
        return ToolExecutionResult(tc_id, name, True, json.dumps(macro))

    elif name == "audit_portfolio":
        # 模拟账户健康检查
        audit = {
            "health_score": 85,
            "diversification": "Good",
            "max_drawdown_risk": "12.5%",
            "recommendation": "Reduce tech exposure if NVDA exceeds 15% of total capital."
        }
        return ToolExecutionResult(tc_id, name, True, json.dumps(audit))

    # --- Vibe-Trading 集成工具 (Phase 3) ---

    elif name == "run_backtest":
        from .vibe_tools import run_backtest_impl
        result = run_backtest_impl(
            signal_code=args.get("signal_code", ""),
            codes=args.get("codes", []),
            start_date=args.get("start_date", ""),
            end_date=args.get("end_date", ""),
            source=args.get("source", "auto")
        )
        return ToolExecutionResult(tc_id, name, result.get("status") == "ok", json.dumps(result))

    elif name == "extract_shadow_strategy":
        from .vibe_tools import extract_shadow_strategy_impl
        result = extract_shadow_strategy_impl(journal_path=args.get("journal_path", ""))
        return ToolExecutionResult(tc_id, name, result.get("status") == "ok", json.dumps(result))

    elif name == "analyze_trade_journal":
        from .vibe_tools import analyze_trade_journal_impl
        result = analyze_trade_journal_impl(journal_path=args.get("journal_path", ""))
        return ToolExecutionResult(tc_id, name, result.get("status") == "ok", json.dumps(result))

    elif name == "run_pattern":
        from .vibe_tools import run_pattern_impl
        result = run_pattern_impl(
            run_dir=args.get("run_dir", ""),
            patterns=args.get("patterns", "all"),
            window=args.get("window", 10)
        )
        return ToolExecutionResult(tc_id, name, result.get("status") == "ok", json.dumps(result))

    elif name == "run_factor_analysis":
        from .vibe_tools import run_factor_analysis_impl
        result = run_factor_analysis_impl(
            factor_csv=args.get("factor_csv", ""),
            return_csv=args.get("return_csv", ""),
            output_dir=args.get("output_dir", ""),
            n_groups=args.get("n_groups", 5)
        )
        return ToolExecutionResult(tc_id, name, result.get("status") == "ok", json.dumps(result))

    return ToolExecutionResult(tc_id, name, False, f"Unknown tool: {name}")


def dispatch_all(
    tool_calls: List[Dict[str, Any]],
    context: Dict[str, Any]
) -> List[ToolExecutionResult]:
    """
    并行或顺序执行一组工具调用。
    """
    results = []
    for tc in tool_calls:
        results.append(dispatch_tool_call(tc, context))
    return results
