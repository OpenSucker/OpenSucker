"""
OpenAI function calling 工具 JSON Schema 定义 — Sucker 金融版
======================================================
"""
from __future__ import annotations
from typing import List, Dict, Any


GET_MARKET_SENTIMENT_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_market_sentiment",
        "description": "扫描社交媒体（Twitter, Reddit, 微博）的情绪指数，返回恐慌或贪婪数值。",
        "parameters": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "资产名称，如 'NVDA', 'BTC', '大盘'"}
            },
            "required": ["asset"]
        }
    }
}

GET_TECHNICAL_INDICATORS_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_technical_indicators",
        "description": "获取指定标的的技术指标，如 RSI, MACD, KDJ, BOLL。",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "股票或标的代码，如 'NVDA'"},
                "indicators": {"type": "array", "items": {"type": "string"}, "description": "请求的指标列表"}
            },
            "required": ["symbol", "indicators"]
        }
    }
}

CALCULATE_POSITION_SIZE_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "calculate_position_size",
        "description": "使用凯利公式计算建议的试仓比例或补仓仓位。",
        "parameters": {
            "type": "object",
            "properties": {
                "win_rate": {"type": "number", "description": "预估胜率 (0-1)"},
                "profit_loss_ratio": {"type": "number", "description": "预估盈亏比"},
                "total_capital": {"type": "number", "description": "账户总资金"}
            },
            "required": ["win_rate", "profit_loss_ratio"]
        }
    }
}

GET_STOCK_QUOTE_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_stock_quote",
        "description": "获取实时股价、涨跌幅、成交量等行情数据。",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "标的代码"}
            },
            "required": ["symbol"]
        }
    }
}

ANALYZE_MACRO_DATA_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "analyze_macro_data",
        "description": "查询宏观经济指标，如美联储利率、CPI、非农数据。",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {"type": "string", "description": "指标名称，如 'FED_RATE', 'CPI'"}
            },
            "required": ["metric"]
        }
    }
}

AUDIT_PORTFOLIO_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "audit_portfolio",
        "description": "对用户当前持仓进行健康诊断与风险压力测试。",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

BACKTEST_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "run_backtest",
        "description": "量化回测与数据抓取工具。输入策略代码、标的代码列表、开始和结束日期。如果只需抓取行情数据而无需特定策略，signal_code 可以留空。",
        "parameters": {
            "type": "object",
            "properties": {
                "signal_code": {"type": "string", "description": "Python 策略代码 (继承 SignalEngine)。如果仅抓取数据，请留空。"},
                "codes": {"type": "array", "items": {"type": "string"}, "description": "股票/标的代码列表，如 ['AAPL', 'TSLA']"},
                "start_date": {"type": "string", "description": "开始日期 (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "结束日期 (YYYY-MM-DD)"},
                "source": {"type": "string", "description": "数据源: 'yahoo', 'binance', 'local'", "default": "auto"}
            },
            "required": ["codes", "start_date", "end_date"]
        }
    }
}

EXTRACT_SHADOW_STRATEGY_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "extract_shadow_strategy",
        "description": "从用户的历史交割单（交易日志）中提取‘影子账户’投资策略原型，生成行为准则。",
        "parameters": {
            "type": "object",
            "properties": {
                "journal_path": {"type": "string", "description": "交割单文件路径 (CSV/Excel)"}
            },
            "required": ["journal_path"]
        }
    }
}

ANALYZE_TRADE_JOURNAL_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "analyze_trade_journal",
        "description": "对交易日志进行深度统计分析，计算胜率、盈亏比、回撤等核心指标。",
        "parameters": {
            "type": "object",
            "properties": {
                "journal_path": {"type": "string", "description": "文件路径"}
            },
            "required": ["journal_path"]
        }
    }
}

PATTERN_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "run_pattern",
        "description": "形态识别工具。在回测或行情数据目录上运行，识别双底、头肩底、缠论中枢等技术形态。",
        "parameters": {
            "type": "object",
            "properties": {
                "run_dir": {"type": "string", "description": "数据所在目录（需包含 OHLCV 数据）"},
                "patterns": {"type": "string", "description": "要识别的形态名称或 'all'"},
                "window": {"type": "integer", "description": "识别窗口大小"}
            },
            "required": ["run_dir"]
        }
    }
}

FACTOR_ANALYSIS_TOOL: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "run_factor_analysis",
        "description": "多因子分析工具。计算因子IC/IR，并进行分层回测。输出分析报告和曲线。",
        "parameters": {
            "type": "object",
            "properties": {
                "factor_csv": {"type": "string", "description": "因子值 CSV 路径 (index=date, columns=codes)"},
                "return_csv": {"type": "string", "description": "收益率 CSV 路径"},
                "output_dir": {"type": "string", "description": "报告输出目录"},
                "n_groups": {"type": "integer", "description": "分层数量", "default": 5}
            },
            "required": ["factor_csv", "return_csv", "output_dir"]
        }
    }
}

ALL_TOOLS_SCHEMAS = [
    GET_MARKET_SENTIMENT_TOOL,
    GET_TECHNICAL_INDICATORS_TOOL,
    CALCULATE_POSITION_SIZE_TOOL,
    GET_STOCK_QUOTE_TOOL,
    ANALYZE_MACRO_DATA_TOOL,
    AUDIT_PORTFOLIO_TOOL,
    BACKTEST_TOOL,
    EXTRACT_SHADOW_STRATEGY_TOOL,
    ANALYZE_TRADE_JOURNAL_TOOL,
    PATTERN_TOOL,
    FACTOR_ANALYSIS_TOOL
]


def get_tools_for_cell(x_axis: str, y_axis: str) -> List[Dict[str, Any]]:
    """
    根据 XxY 矩阵位置获取可用工具子集。
    目前金融版 Phase 1 阶段所有专家共享全量金融工具库。
    """
    return ALL_TOOLS_SCHEMAS
