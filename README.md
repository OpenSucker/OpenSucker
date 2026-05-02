# OpenSucker: 智能交易矩阵 (Smart Trading Matrix)

OpenSucker 是一个“伴随投资者一生”的全栈式 AI 交易平台。通过 20 个独立运作且高度协同的专家 Agent 矩阵，消除金融市场的认知不对称。

## 核心特性

- **20 子专家矩阵**: 覆盖情绪感知、技术量化、系统策略、机构宏观与顶级博弈五个维度。
- **Router Agent (中枢路由)**: 自动识别用户认知层级 (Lv.1–Lv.5)，提供陪伴式进化体验。
- **白盒化决策**: 所有交易建议均可归因、可回溯。
- **风险隔离**: 遵循“LLM 推理，逻辑代码计算”的原则，确保资金安全。

## 项目结构

```
OpenSucker/
├── backend/          # FastAPI + LangGraph, 由 uv 管理
│   ├── agent.py      # 入口, 默认监听 :7860
│   ├── pyproject.toml
│   └── .env          # 本地密钥 (从 .env.example 复制)
├── frontend/         # React + Vite
├── package.json      # 根 npm 脚本, 驱动前后端
└── README.md
```

## 环境要求

| 组件   | 版本         | 说明                              |
| ------ | ------------ | --------------------------------- |
| Node   | >= 18        | 前端 + 根 npm 脚本                |
| Python | >= 3.11, <4  | 由 uv 自动管理, 无需手动安装      |
| uv     | >= 0.4       | Python 依赖管理器 (`brew install uv`) |

## 快速开始

```bash
# 1. 安装根依赖 (concurrently)
npm install

# 2. 一键安装前后端依赖 (uv sync + frontend npm install)
npm run setup

# 3. 配置后端环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env, 填入 LLM_API_KEY 等

# 4. 同时启动前后端
npm run dev
```

启动后:

- 后端 API: <http://localhost:7860> · 文档 <http://localhost:7860/docs>
- 前端开发服务器: <http://localhost:5173> (Vite 默认)

## npm 脚本总览

| 命令                    | 作用                                              |
| ----------------------- | ------------------------------------------------- |
| `npm run setup`         | 安装前后端所有依赖                                |
| `npm run setup:backend` | 只跑 `uv sync` 安装 Python 依赖                   |
| `npm run setup:frontend`| 只在 `frontend/` 跑 `npm install`                 |
| `npm run dev`           | 并发启动后端 (:7860) + 前端 (Vite :5173)          |
| `npm run dev:backend`   | 仅启动后端 (`uv run python agent.py`)             |
| `npm run dev:frontend`  | 仅启动前端 Vite 开发服务器                        |
| `npm run build`         | 构建前端 (`vite build`)                           |
| `npm run lint:frontend` | 前端 ESLint                                       |
| `npm run clean`         | 清除 `.venv`, `__pycache__`, `node_modules`, `dist` |

## 后端依赖管理 (uv)

- 安装 / 同步: `cd backend && uv sync`
- 添加运行时依赖: `cd backend && uv add <pkg>`
- 添加开发依赖: `cd backend && uv add --group dev <pkg>`
- 运行任意脚本: `uv run python <file>.py`
- **`pyproject.toml` 与 `uv.lock` 均应提交**；`.venv/` 已在 `backend/.gitignore` 中忽略。

## 环境变量

所有后端变量定义在 `backend/.env.example`，关键项:

| 变量                    | 必填 | 说明                                          |
| ----------------------- | ---- | --------------------------------------------- |
| `LLM_API_KEY`           | ✅   | OpenAI-compatible API Key                     |
| `LLM_API_BASE`          | ✅   | API Base URL (不带 `/v1`)                     |
| `LLM_API_MODEL`         | ✅   | 模型名, 例 `gpt-4o` / `Pro/moonshotai/Kimi-K2.5` |
| `PORT`                  | ❌   | 后端端口, 默认 `7860`                         |
| `USE_FUNCTION_CALLING`  | ❌   | `1` = LLM 自主调工具；`0` = 硬编码 state machine |
| `COMFYUI_URL`           | ❌   | 生图工具 ComfyUI 地址                         |

## 架构简述

- **X 轴 (认知层级/领域)**: X1 情绪, X2 技术, X3 策略, X4 宏观, X5 博弈。
- **Y 轴 (执行阶段)**: Y1 侦察, Y2 审计, Y3 执行, Y4 复盘。
