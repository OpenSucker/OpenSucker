# OpenSucker Backend

OpenSucker 是一个基于 FastAPI 的证券风险分析后端服务。

当前版本聚焦于安全、可运行、可扩展的 MVP，不提供真实交易下单能力，而是提供以下分析型接口：

- 市场微观结构风险分析
- 新闻舆情风险分析
- 综合风险评分
- 样例场景输出
- 健康检查与自动接口文档

## 1. 技术栈

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic v2
- NumPy
- LangGraph

## 2. 项目结构

```text
OpenSucker/
├─ app/
│  ├─ api/
│  │  ├─ v1/
│  │  │  ├─ endpoints/
│  │  │  │  ├─ analysis.py
│  │  │  │  ├─ health.py
│  │  │  │  ├─ orders.py
│  │  │  │  ├─ terminals.py
│  │  │  │  ├─ counters.py
│  │  │  │  ├─ monitoring.py
│  │  │  │  └─ intelligence.py
│  │  │  └─ router.py
│  │  └─ dependencies.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ events.py
│  │  └─ security.py
│  ├─ db/
│  │  ├─ base.py
│  │  └─ session.py
│  ├─ domains/
│  │  ├─ orders/
│  │  │  ├─ schemas.py
│  │  │  └─ service.py
│  │  ├─ terminals/
│  │  │  ├─ schemas.py
│  │  │  └─ service.py
│  │  ├─ counters/
│  │  │  ├─ schemas.py
│  │  │  └─ service.py
│  │  ├─ monitoring/
│  │  │  ├─ schemas.py
│  │  │  └─ service.py
│  │  └─ intelligence/
│  │     ├─ schemas.py
│  │     └─ service.py
│  ├─ graphs/
│  │  └─ risk_workflow.py
│  ├─ models/
│  │  └─ schemas.py
│  ├─ services/
│  │  ├─ risk_engine.py
│  │  └─ sample_data.py
│  ├─ utils/
│  │  ├─ datetime_utils.py
│  │  └─ validators.py
│  ├─ __init__.py
│  └─ main.py
├─ tests/
│  ├─ conftest.py
│  ├─ test_api/
│  │  └─ test_health.py
│  ├─ test_services/
│  │  └─ test_risk_engine.py
│  └─ test_domains/
├─ docs/
│  └─ architecture.md
├─ scripts/
│  └─ init_db.py
├─ requirements.txt
├─ .env.example
├─ README.md
└─ 要求.md
```

## 3. 功能说明

### 3.1 市场风险分析

接口会根据以下输入做启发式评分：

- 分时价格序列
- 分时成交量序列
- 盘口快照
- 撤单占比
- 大单占比
- 买卖盘失衡
- 买卖价差扩张

输出结果包含：

- 总风险分数 `risk_score`
- 风险等级 `risk_level`
- 摘要 `summary`
- 分项因子 `factors`

### 3.2 新闻风险分析

接口会对新闻标题与摘要做关键词风险匹配，识别例如：

- 问询
- 处罚
- 违约
- 造假
- 停牌
- 减持
- 风险
- 暴跌

输出结果包含：

- 新闻风险分数
- 风险等级
- 命中关键词说明
- 负面关键词集中度

### 3.3 综合风险分析

综合评分规则：

- 市场信号权重 60%
- 新闻信号权重 40%

综合分析链路通过 `LangGraph` 编排执行，当前工作流包含以下节点：

- `market_analysis`
- `news_analysis`
- `merge_analysis`

适合作为后续风控面板、告警引擎或研究系统的基础能力。

## 4. 快速启动

### 4.1 安装依赖

```bash
pip install -r requirements.txt
```

### 4.2 启动服务

```bash
uvicorn app.main:app --reload
```

默认启动地址：

```text
http://127.0.0.1:8000
```

### 4.3 查看接口文档

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

## 5. API 一览

### 5.1 根路径

- `GET /`

返回服务名、版本号和文档地址。

### 5.2 健康检查

- `GET /health`

### 5.3 市场风险分析

- `POST /api/v1/analysis/market`

请求体示例：

```json
{
  "symbol": "SZ300750",
  "price_series": [
    {"timestamp": "2026-05-01T09:30:00", "price": 182.5, "volume": 210000},
    {"timestamp": "2026-05-01T09:31:00", "price": 181.9, "volume": 225000},
    {"timestamp": "2026-05-01T09:32:00", "price": 180.6, "volume": 318000},
    {"timestamp": "2026-05-01T09:33:00", "price": 179.8, "volume": 452000},
    {"timestamp": "2026-05-01T09:34:00", "price": 177.2, "volume": 780000}
  ],
  "order_book": [
    {
      "timestamp": "2026-05-01T09:32:00",
      "best_bid": 180.5,
      "best_ask": 180.8,
      "bid_volume": 45000,
      "ask_volume": 68000,
      "cancel_ratio": 0.43,
      "large_order_ratio": 0.31
    },
    {
      "timestamp": "2026-05-01T09:33:00",
      "best_bid": 179.7,
      "best_ask": 180.1,
      "bid_volume": 38000,
      "ask_volume": 92000,
      "cancel_ratio": 0.58,
      "large_order_ratio": 0.4
    },
    {
      "timestamp": "2026-05-01T09:34:00",
      "best_bid": 177.0,
      "best_ask": 177.6,
      "bid_volume": 21000,
      "ask_volume": 105000,
      "cancel_ratio": 0.65,
      "large_order_ratio": 0.47
    }
  ]
}
```

### 5.4 新闻风险分析

- `POST /api/v1/analysis/news`

请求体示例：

```json
{
  "symbol": "SZ300750",
  "news": [
    {
      "timestamp": "2026-05-01T08:40:00",
      "title": "公司收到交易所问询函",
      "source": "交易所",
      "summary": "涉及业绩异常波动与信息披露风险"
    },
    {
      "timestamp": "2026-05-01T08:55:00",
      "title": "核心股东计划减持",
      "source": "公告",
      "summary": "减持规模较大，市场情绪承压"
    }
  ]
}
```

### 5.5 综合风险分析

- `POST /api/v1/analysis/composite`

请求体结构：

```json
{
  "market": {},
  "news": {}
}
```

### 5.6 样例高风险场景

- `GET /api/v1/analysis/scenarios/high-risk`

可直接用该接口返回的样例数据调用综合分析接口。

### 5.7 订单管理

#### 手工自主下单

- `POST /api/v1/orders/manual`

#### 量化交易下单

- `POST /api/v1/orders/quant`

### 5.8 交易终端

- `GET /api/v1/terminals/` - 终端对比
- `GET /api/v1/terminals/{terminal_type}` - 单个终端详情

### 5.9 券商柜台

- `GET /api/v1/counters/` - 柜台对比
- `GET /api/v1/counters/{counter_type}` - 单个柜台详情

### 5.10 异常监控

- `POST /api/v1/monitoring/abnormal` - 盘口异常扫描

### 5.11 情报舆情

- `POST /api/v1/intelligence/sentiment` - 舆情监控分析

## 6. 适用场景

这个后端适合以下方向的 MVP 或后续扩展：

- 散户风险提示系统
- 证券异动监控平台
- 新闻驱动型预警服务
- 量化行为研究辅助系统
- 研究型风控中台

## 7. 当前版本边界

当前版本没有实现以下能力：

- 实时行情接入
- WebSocket 推送
- 数据库存储
- 用户认证鉴权
- 真正的 NLP 情感模型
- 真实券商柜台接入
- 自动下单与交易执行

## 8. 后续建议

下一阶段建议优先增加：

- SQLite 或 PostgreSQL 持久化
- Redis 缓存与限流
- WebSocket 实时告警
- 更细粒度的新闻打分模型
- 多股票批量分析
- 回测数据导入
- 用户与权限系统

## 9. 交付说明

本次已完成：

- 完整 FastAPI 后端骨架（分层架构：Presentation / Application / Domain / Infrastructure）
- 5 个业务域模块（orders / terminals / counters / monitoring / intelligence）
- 风险分析核心服务 + LangGraph 工作流编排
- 数据库层（SQLAlchemy ORM 基础）
- 安全层（JWT Bearer 认证框架）
- 工具层（时间处理、输入校验）
- 测试框架（pytest + conftest + 示例用例）
- 架构文档（docs/architecture.md）
- 数据库初始化脚本（scripts/init_db.py）
- 环境变量模板（.env.example）
- 请求/响应数据模型（Pydantic v2）
- 示例场景数据
- 自动化 API 文档
- 清晰 README

你现在可以直接安装依赖并启动服务进行联调。
