# OpenSucker 架构设计

## 1. 分层架构

```
┌─────────────────────────────────────┐
│           Presentation Layer         │
│         (FastAPI Routers)            │
├─────────────────────────────────────┤
│           Application Layer          │
│     (Services / Use Cases)          │
├─────────────────────────────────────┤
│            Domain Layer              │
│   (Orders / Terminals / Counters   │
│  / Monitoring / Intelligence)       │
├─────────────────────────────────────┤
│         Infrastructure Layer         │
│  (DB / LangGraph / Utils / Config)  │
└─────────────────────────────────────┘
```

## 2. 业务域映射

| 要求.md 概念 | 代码模块 | 职责 |
|-------------|---------|------|
| 手工自主下单 | `domains/orders/` | 订单创建、延迟计算 |
| 量化交易下单 | `domains/orders/` | 量化专用下单通道 |
| 手机APP | `domains/terminals/` | 终端特性与延迟对比 |
| 普通PC | `domains/terminals/` | 终端特性与延迟对比 |
| VIP终端 | `domains/terminals/` | 终端特性与延迟对比 |
| 普通柜台 | `domains/counters/` | 柜台特性与延迟对比 |
| LDP极速柜台 | `domains/counters/` | 柜台特性与延迟对比 |
| UFT极速柜台 | `domains/counters/` | 柜台特性与延迟对比 |
| 盘口异常扫描 | `domains/monitoring/` | 异常信号检测 |
| 舆情监控 | `domains/intelligence/` | 情感分析 |
| 综合风险分析 | `graphs/risk_workflow.py` | LangGraph编排 |

## 3. 技术栈映射

| 技术 | 使用位置 |
|------|---------|
| FastAPI | `app/main.py`, `app/api/` |
| Pydantic v2 | `app/models/`, `app/domains/*/schemas.py` |
| NumPy | `app/services/risk_engine.py` |
| LangGraph | `app/graphs/risk_workflow.py` |
| SQLAlchemy | `app/db/` |
| Uvicorn | 运行入口 |
