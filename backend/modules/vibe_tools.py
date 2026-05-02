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
    # 如果代码为空或者只是个占位符，我们自动注入一个最小化可运行的 Vibe 策略框架
    final_code = signal_code.strip()
    if not final_code or len(final_code) < 20:
        final_code = """
from backtest.engine import SignalEngine
import pandas as pd

class MySignalEngine(SignalEngine):
    \"\"\"最小化数据抓取引擎，不产生信号\"\"\"
    def on_bar(self, bar: pd.Series):
        pass
"""
    
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
        
        # 尝试解析输出
        try:
            # 找到最后一行 JSON (runner 通常会 print JSON)
            lines = process.stdout.strip().split("\n")
            result = json.loads(lines[-1])
        except:
            result = {
                "status": "error",
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode
            }
            
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
