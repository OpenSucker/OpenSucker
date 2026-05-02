import os
import sys
import json
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# ============================================================
# Vibe-Trading Bridge — OpenSucker 集成桥接器
# ============================================================

# 获取 backend 根目录，将其加入 sys.path
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

# Vibe 引擎根目录
VIBE_ROOT = os.path.join(BACKEND_ROOT, "modules", "vibe_engines")
# 为了让移植的代码正常运行，我们需要把 vibe_engines 目录也加入路径，
# 模拟 Vibe 原本的包结构（原本它们位于 src/ 或 backtest/）
if VIBE_ROOT not in sys.path:
    sys.path.append(VIBE_ROOT)

def run_backtest_impl(
    signal_code: str,
    codes: List[str],
    start_date: str,
    end_date: str,
    source: str = "auto"
) -> Dict[str, Any]:
    """
    量化回测执行桥接逻辑。
    1. 创建临时运行目录
    2. 写入 config.json 和 signal_engine.py
    3. 调用 vibe_engines.backtest.runner
    """
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    workspace = os.path.join(BACKEND_ROOT, "temp_backtests", run_id)
    os.makedirs(os.path.join(workspace, "code"), exist_ok=True)

    # 写入配置
    config = {
        "codes": codes,
        "start_date": start_date,
        "end_date": end_date,
        "source": source,
        "interval": "1D",
        "engine": "daily"
    }
    with open(os.path.join(workspace, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    # 写入策略代码
    # 如果代码为空或者只是个占位符，注入一个最小化、可独立运行的 SignalEngine。
    # runner 只检查 `class SignalEngine` + `.generate(data_map)`, 不需要继承任何基类。
    # 默认行为: 全仓 buy-and-hold (信号恒为 1.0), 适合做压力测试 / 持有期最大回撤。
    final_code = signal_code.strip()
    if not final_code or len(final_code) < 20:
        final_code = '''"""Auto-injected baseline SignalEngine: 全仓 buy-and-hold (信号恒为 1.0)."""
import pandas as pd


class SignalEngine:
    """全仓 buy-and-hold 基准: 用于压力测试 / 最大回撤评估。"""

    def generate(self, data_map: dict) -> dict:
        signals: dict[str, pd.Series] = {}
        for code, df in (data_map or {}).items():
            signals[code] = pd.Series(1.0, index=df.index)
        return signals
'''
    
    with open(os.path.join(workspace, "code", "signal_engine.py"), "w", encoding="utf-8") as f:
        f.write(final_code)

    # 构造执行命令
    # 我们直接通过 python 运行移植后的 runner.py
    runner_path = os.path.join(VIBE_ROOT, "backtest", "runner.py")
    
    try:
        # 设置 PYTHONPATH 确保 runner 能找到 backtest 模块
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{VIBE_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
        
        process = subprocess.run(
            [sys.executable, runner_path, workspace],
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )
        
        # 尝试解析输出: runner 输出多行 pretty-printed JSON, 优先整段解析,
        # 失败再回退到 "最后一个 { ... } 块"。
        result: Dict[str, Any] = {}
        out = (process.stdout or "").strip()
        if out:
            try:
                result = json.loads(out)
            except Exception:
                # 找最后一个 '{' 到末尾, 兜底解析
                last_brace = out.rfind("{")
                if last_brace >= 0:
                    try:
                        result = json.loads(out[last_brace:])
                    except Exception:
                        result = {}

        if not result:
            result = {
                "status": "error",
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
            }
        elif process.returncode == 0 and "status" not in result:
            # runner 默认只打 metrics, 没 status 字段, 视为成功
            result = {"status": "ok", "metrics": result, "exit_code": 0}
        elif process.returncode != 0 and "status" not in result:
            result["status"] = "error"
            result["exit_code"] = process.returncode

        return result

    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        # 实际生产中可以保留一段时间，演示时暂不删除
        # shutil.rmtree(workspace)
        pass

def extract_shadow_strategy_impl(journal_path: str) -> Dict[str, Any]:
    """
    影子账户提取桥接。
    """
    try:
        from modules.vibe_engines.shadow_account import extract_shadow_profile
        # 这里可能需要根据文件类型进行预处理，或者直接调用
        profile = extract_shadow_profile(journal_path)
        return {
            "status": "ok",
            "shadow_id": profile.shadow_id,
            "rules": [r.human_text for r in profile.rules],
            "profile_summary": profile.profile_text[:500]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def analyze_trade_journal_impl(journal_path: str) -> Dict[str, Any]:
    """
    交易日志分析桥接。
    """
    try:
        import pandas as pd
        # 简单的统计逻辑占位（实际可调用 Vibe 的 extractor）
        df = pd.read_csv(journal_path) if journal_path.endswith('.csv') else pd.read_excel(journal_path)
        return {
            "status": "ok",
            "trades_count": len(df),
            "summary": "分析完成，建议执行影子账户提取以获取更深层的行为模式。"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def run_pattern_impl(run_dir: str, patterns: str = "all", window: int = 10) -> Dict[str, Any]:
    """形态识别桥接。"""
    try:
        from modules.vibe_engines.tools.pattern_tool import run_pattern
        res_str = run_pattern(run_dir, patterns, window)
        res = json.loads(res_str)
        
        # 优化报错体验：如果没数据，明确告知需要先回测
        if res.get("status") == "error" and "No OHLCV data" in res.get("error", ""):
            return {
                "status": "error",
                "error": "缺少行情数据（OHLCV）。形态识别工具需要先运行 'run_backtest' 工具获取历史数据后才能工作。",
                "suggestion": "请先指示专家执行 run_backtest 获取数据，例如：'先获取 TSLA 最近 30 天的数据'。"
            }
        return res
    except Exception as e:
        return {"status": "error", "error": str(e)}

def run_factor_analysis_impl(factor_csv: str, return_csv: str, output_dir: str, n_groups: int = 5) -> Dict[str, Any]:
    """多因子分析桥接。"""
    try:
        from modules.vibe_engines.tools.factor_analysis_tool import run_factor_analysis
        res_str = run_factor_analysis(factor_csv, return_csv, output_dir, n_groups)
        return json.loads(res_str)
    except Exception as e:
        return {"status": "error", "error": str(e)}
