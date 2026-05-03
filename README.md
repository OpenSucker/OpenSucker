<div align="center">

<img src="https://img.shields.io/badge/OpenSucker-智能交易矩阵-00D4E4?style=for-the-badge&labelColor=0D1117" alt="OpenSucker" />

# OpenSucker

**消除金融市场的认知不对称**

*一个"伴随投资者一生"的全栈 AI 交易平台 · 20 专家 Agent 矩阵 · 白盒化决策*

---

[![Stars](https://img.shields.io/github/stars/LangQi99/OpenSucker?style=for-the-badge&color=00D4E4&labelColor=0D1117)](https://github.com/LangQi99/OpenSucker/stargazers)
[![Forks](https://img.shields.io/github/forks/LangQi99/OpenSucker?style=for-the-badge&color=00D4E4&labelColor=0D1117)](https://github.com/LangQi99/OpenSucker/network/members)
[![License](https://img.shields.io/badge/License-MIT-DE5FE9?style=for-the-badge&labelColor=0D1117)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=0D1117)](https://python.org)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=white&labelColor=0D1117)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-LangGraph-009688?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=0D1117)](https://fastapi.tiangolo.com)

</div>

---

## 这是什么？

散户在市场里天然处于劣势：没有量化团队、没有机构信源、没有心态管理。**OpenSucker** 用 20 个协同运作的专家 Agent，把机构级分析流水线打包给每个人用。

- 你问"茅台能买吗"，系统识别出你是 Lv.2 认知水平，自动调度 X1（情绪）+ X2（技术）+ X4（宏观）三路专家会诊，给出可归因、可回溯的分析结论。
- 你喊"All in 了"，风险防火墙立刻介入，转交 X5 博弈专家进行情绪安抚与仓位再评估。
- 所有推理过程白盒透明，不是黑盒预测，你永远知道结论从何而来。

---

## 矩阵架构

```
         Y1 侦察      Y2 审计      Y3 执行      Y4 复盘
        ─────────────────────────────────────────────────
X1 情绪  │ 情绪雷达  │ 舆情校验  │ 恐慌拦截  │ 情绪复盘  │
X2 技术  │ 形态扫描  │ 信号核验  │ 点位执行  │ 策略归因  │
X3 策略  │ 系统选股  │ 规则审计  │ 批量下单  │ 策略迭代  │
X4 宏观  │ 宏观侦察  │ 政策研判  │ 配置调仓  │ 宏观复盘  │
X5 博弈  │ 主力追踪  │ 筹码验证  │ 博弈执行  │ 顶部复盘  │
```

**Router Agent（中枢路由）** 自动识别用户认知层级（Lv.1–Lv.5），将每条消息路由到最合适的矩阵节点，并在必要时激活 **Swarm Committee 共识会议**，让多个专家同时会诊后综合出最终建议。

---

## 核心特性

### 🎯 认知自适应
Router Agent 实时评估用户画像（风险偏好、持仓结构、历史教训、认知层级），同一个问题对新手和老手给出完全不同深度的回答，且答案质量随使用时长持续进化。

### 🛡️ 风险防火墙
遵循 **"LLM 推理，逻辑代码计算"** 原则。仓位计算、止损触发等涉及资金安全的逻辑全部走确定性代码，不让 LLM 直接操控数字。`All in`、`全仓` 等危险意图被硬拦截并转交情绪专家。

### ⚡ 实时流式推送
前端通过 SSE 接收每个 Agent 节点的实时状态：意图识别 → 风险检查 → 专家介入 → 工具调用 → 结论生成，全程可视化，无黑盒等待。

### 🔍 白盒化决策
每条建议均携带：触发的矩阵节点、调用的技能、执行的工具链、推理步骤摘要。可归因、可回溯、可质疑。

### 🧩 开放技能系统
每个矩阵节点（如 X2Y1）可挂载独立的技能包（methodology），覆盖 K 线形态、均线系统、量价关系等细分领域，热插拔，无需重启服务。

---

## 生态子项目

OpenSucker 是一个工具生态，以下子项目均可独立部署：

| 项目 | 描述 | 技术栈 |
|------|------|--------|
| [**NeoFish**](./NeoFish) | 全能浏览器 Agent，多平台接入（Web / Telegram / QQ）| Playwright · FastAPI · Vue 3 |
| [**MiniFish**](./MiniFish) | 长文本 → GraphRAG → Agent 人设，两步生成 | Neo4j · Qdrant · Flask |
| [**InfoFish**](./InfoFish) | 多平台舆情聚合，SSE 流式深度抓取导出 | FastAPI · Vue 3 · trafilatura |

---

## 快速开始

### 环境要求

| 工具 | 版本 | 安装 |
|------|------|------|
| Node.js | >= 18 | [nodejs.org](https://nodejs.org) |
| Python | >= 3.11 | [python.org](https://python.org) |
| uv | >= 0.4 | `brew install uv` / [文档](https://docs.astral.sh/uv/) |

### 一键启动

```bash
# 克隆（含子模块）
git clone --recurse-submodules https://github.com/LangQi99/OpenSucker.git
cd OpenSucker

# 安装所有依赖
npm install && npm run setup

# 配置 LLM 密钥
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入以下变量：
#   LLM_API_KEY=sk-...
#   LLM_API_BASE=https://api.openai.com   （或任意兼容接口）
#   LLM_API_MODEL=gpt-4o

# 启动（前后端并发）
npm run dev
```

启动后：
- **后端 API** → http://localhost:7860 · 交互文档 → http://localhost:7860/docs
- **前端界面** → http://localhost:5173

### 环境变量说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `LLM_API_KEY` | ✅ | OpenAI-compatible API Key |
| `LLM_API_BASE` | ✅ | API Base URL（不带 `/v1`） |
| `LLM_API_MODEL` | ✅ | 模型名，如 `gpt-4o`、`claude-3-5-sonnet` |
| `PORT` | ❌ | 后端端口，默认 `7860` |
| `USE_FUNCTION_CALLING` | ❌ | `1` = LLM 自主调工具；`0` = 硬编码状态机 |

---

## 项目结构

```
OpenSucker/
├── backend/
│   ├── agent.py          # 主入口，LangGraph 图定义 + FastAPI 路由
│   ├── database.py       # 用户画像持久化（SQLite）
│   ├── modules/
│   │   ├── intent.py     # Router Agent，认知层级识别
│   │   ├── xy_prompts.py # 矩阵节点系统提示词
│   │   ├── skills_manager.py     # 技能包热插拔
│   │   └── function_calling_engine.py  # 工具调用循环
│   └── pyproject.toml
├── frontend/             # React + Vite + Tailwind
├── NeoFish/              # 子模块：浏览器 Agent
├── MiniFish/             # 子模块：GraphRAG 人设生成
├── InfoFish/             # 子模块：舆情面板
└── package.json          # 根 npm 脚本
```

---

## npm 脚本

| 命令 | 作用 |
|------|------|
| `npm run setup` | 安装前后端全部依赖 |
| `npm run dev` | 并发启动后端（:7860）+ 前端（:5173）|
| `npm run build` | 构建前端产物 |
| `npm run clean` | 清理 `.venv` / `node_modules` / `dist` |

---

## 数据流

```
用户输入
   │
   ▼
[profile_update]  ← 从 DB 同步用户画像
   │
   ▼
[intent_router]   ← Router Agent 识别意图 + 路由 XY 坐标
   │
   ▼
[risk_check]      ← 过激行为检测（All-in / 全仓）
   │
   ├─ 高风险 ──→ [X5 博弈专家]  情绪安抚 + 博弈分析
   ├─ 委员会 ──→ [Swarm Committee]  X1+X2+X4 并行会诊
   └─ 常规   ──→ [X1/X2/X3/X4]  对应维度专家
              │
              ▼ （技能包注入 + Function Calling 循环）
           [respond]
              │
              ▼
         SSE 推送前端（每节点实时）
```

---

## 参与贡献

欢迎提交 Issue 和 Pull Request。贡献前请阅读以下约定：

- 新的矩阵技能放在 `backend/skills/` 目录下
- 每个技能包需包含 `metadata.json`（声明适用 XY 节点和意图类型）
- 前端组件用 Tailwind utility class，不新增自定义 CSS 文件

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=LangQi99/OpenSucker&type=Date)](https://star-history.com/#LangQi99/OpenSucker&Date)

---

<div align="center">
  <sub>Built with ❤️ by <a href="https://github.com/LangQi99">LangQi99</a> · <a href="https://github.com/LangQi99/OpenSucker/issues">反馈问题</a> · <a href="https://github.com/LangQi99/OpenSucker/stargazers">给个 Star ⭐</a></sub>
</div>
