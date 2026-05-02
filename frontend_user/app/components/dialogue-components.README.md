# Dialogue Components Guide

这个文件说明新的对话页里，哪些关键词会触发哪些组件，以及 mock 数据和 API 中间层放在哪里。

## 触发规则

- `知识图谱` / `关系图` / `graph`
  - 触发组件：`MarkdownMessage`、`KnowledgeGraphMessage`、`DataVizMessage`
  - 数据来源：`app/data/graph-snapshot.json`

- `TSLA` / `压力测试` / `回测` / `风险`
  - 触发组件：`MarkdownMessage`、`DataVizMessage`、`CandlestickChartMessage`、`CodeBlockMessage`
  - 数据来源：`app/lib/dialogue-demo.ts`

- `矩阵` / `交易终端` / `画像` / `matrix` / `dashboard`
  - 触发组件：`MarkdownMessage`、`TradingMatrixMessage`、`CodeBlockMessage`
  - 数据来源：`app/lib/dialogue-demo.ts`

- 其他自然语言
  - 触发组件：`text`、`MarkdownMessage`

## 统一 mock 管理

- 所有对话页 mock 数据统一放在 [app/lib/dialogue-demo.ts](D:/nan/app/lib/dialogue-demo.ts)
- 共享类型放在 [app/lib/dialogue-types.ts](D:/nan/app/lib/dialogue-types.ts)

如果后面要新增一个组件，推荐顺序：

1. 在 `dialogue-types.ts` 增加消息类型
2. 在 `dialogue-demo.ts` 增加 mock 数据和触发规则
3. 新增对应 React 组件
4. 在 `DialoguePage.tsx` 里补渲染分支
5. 在这个 README 里补关键词说明

## OpenAI 范式中间层

- 服务端中间层： [app/lib/openai-chat-middleware.ts](D:/nan/app/lib/openai-chat-middleware.ts)
- API 路由： [app/api/dialogue/route.ts](D:/nan/app/api/dialogue/route.ts)

当前接口格式参考 OpenAI Chat Completions：

```json
{
  "model": "mock-dialogue-model",
  "messages": [
    { "role": "user", "content": "知识图谱" }
  ]
}
```

返回体会包含：

- `choices[0].message.content`
- `choices[0].message.components`

其中 `components` 就是前端直接渲染的结构化卡片数组。
