# OpenSucker Matrix 核心功能测试用例 (Phase 3)

本文件定义了 OpenSucker 智能交易矩阵的核心测试场景，用于验证意图识别、矩阵路由、工具调用以及多专家协作逻辑。

---

## 1. 基础行情与情绪探索 (X1Y1)
- **测试指令**: "现在的市场情绪怎么样？大家在看好 NVDA 吗？"
- **预期意图**: `market_analysis`
- **预期坐标**: `X1Y1` (情绪面 · 侦察)
- **激活工具**: `get_market_sentiment`
- **加载技能**: `buffett-perspective` (倾向于寻找恐慌中的机会)
- **预期结果**: 返回 NVDA 的情绪指数（恐慌/贪婪）以及社交媒体热度摘要。

## 2. 深度技术面审计 (X2Y2)
- **测试指令**: "帮我分析一下 TSLA 的技术指标，看看有没有超买，RSI 多少了？"
- **预期意图**: `market_analysis`
- **预期坐标**: `X2Y2` (技术面 · 审计)
- **激活工具**: `get_technical_indicators`
- **加载技能**: `technical-analysis-expert` (专注指标背离)
- **预期结果**: 列出 TSLA 的 RSI, MACD, BOLL 等关键指标，并给出技术位支撑压力分析。

## 3. 仓位策略与风控执行 (X3Y3)
- **测试指令**: "我想买入 100 股 BTC，我的胜率大概 60%，盈亏比 1.5，帮我算下该放多少仓位。"
- **预期意图**: `trade_execution`
- **预期坐标**: `X3Y3` (战术面 · 执行)
- **激活工具**: `calculate_position_size`
- **加载技能**: `kelly-criterion-skill` (凯利公式精算)
- **预期结果**: 计算出建议的仓位比例（如 15%），并给出风控阈值提醒。

## 4. 多专家联合会审 (Committee Mode - X1/X2/X4Y2)
- **测试指令**: "全面分析一下现在是否适合买入 AAPL？考虑情绪、K线和美联储利率。"
- **预期意图**: `committee`
- **预期坐标**: `X1/X2/X4Y2` (多维审计)
- **激活工具**: `get_market_sentiment`, `get_technical_indicators`, `analyze_macro_data`
- **加载技能**: `buffett-perspective`, `munger-perspective`
- **预期结果**: 矩阵同时高亮多个格子，输出包含情绪面、技术面和宏观面的综合评估报告，并在末尾给出共识结论。

## 5. 量化回测验证 (Vibe-Trading 集成)
- **测试指令**: "帮我跑一下 TSLA 过去一年的双底形态回测。"
- **预期意图**: `stock_scan`
- **预期坐标**: `X2Y3` (技术面 · 执行)
- **激活工具**: `run_backtest`, `run_pattern`
- **加载技能**: `pattern-recognition-expert`
- **预期结果**: 启动回测引擎下载数据，随后调用形态工具识别双底，最后输出回测收益率曲线和形态识别图表。

---

## 验证列表 (Checklist)
- [ ] 意图识别准确率 > 90%
- [ ] 矩阵坐标定位无误
- [ ] 工具调用实时在前端展示标签
- [ ] 侧边栏画像根据对话实时更新
- [ ] 5 轮以上复杂工具调用不崩溃 (max_iterations=6)
