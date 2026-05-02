import graphSnapshot from '../data/graph-snapshot.json';
import type {
  DialogueMessage,
  DistributionBar,
  KlineCandle,
  KnowledgeGraphData,
  MatrixTerminalPayload,
  MetricCard,
} from './dialogue-types';

export const PUBLIC_PERSONA_GRAPH_FILE = '/proj_e3a2f7b5ffa0_personas.json';

type RawGraphNode = {
  uuid: string;
  name: string;
  summary?: string;
  labels?: string[];
};

type RawGraphEdge = {
  uuid: string;
  source_node_uuid: string;
  target_node_uuid: string;
  fact_type?: string;
  name?: string;
  fact?: string;
};

type RawGraphSnapshot = {
  node_count: number;
  edge_count: number;
  nodes: RawGraphNode[];
  edges: RawGraphEdge[];
};

type RawPersona = {
  user_id: number;
  name: string;
  bio?: string;
  country?: string;
  profession?: string;
  interested_topics?: string[];
  source_entity_uuid?: string;
  source_entity_type?: string;
};

export type GraphScenarioSource = {
  sourceLabel: string;
  badge: string;
  nodeCount: number;
  edgeCount: number;
  graph: KnowledgeGraphData;
  metrics: MetricCard[];
  bars: DistributionBar[];
  introTitle: string;
  introLines: string[];
  summary: string;
};

export type DialogueTriggerGuide = {
  scenario: string;
  keywords: string[];
  components: string[];
  description: string;
};

const rawSnapshot = graphSnapshot as RawGraphSnapshot;

export const DIALOGUE_TRIGGER_GUIDE: DialogueTriggerGuide[] = [
  {
    scenario: '知识图谱',
    keywords: ['知识图谱', '关系图', 'graph', 'graph snapshot'],
    components: ['markdown', 'knowledge-graph', 'data-viz'],
    description: '加载真实图谱快照，抽取高关联子图并展示统计信息。',
  },
  {
    scenario: '压力测试',
    keywords: ['TSLA', '压力测试', '回测', '风险', 'stress test'],
    components: ['markdown', 'data-viz', 'kline', 'code-block'],
    description: '展示风险结论、K 线走势、指标面板和回测日志。',
  },
  {
    scenario: '交易终端',
    keywords: ['矩阵', '交易终端', '画像', 'matrix', 'dashboard'],
    components: ['markdown', 'matrix-terminal', 'code-block'],
    description: '渲染参考图风格的终端卡片，包括画像、矩阵层级、洞察和任务链。',
  },
  {
    scenario: '默认对话',
    keywords: ['任意自然语言'],
    components: ['text', 'markdown'],
    description: '走普通对话，并提示当前支持的组件类型。',
  },
];

function createId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function clampText(value: string, maxLength: number) {
  return value.length > maxLength ? `${value.slice(0, maxLength - 1)}…` : value;
}

function nodeColor(labels: string[] | undefined) {
  const labelSet = new Set(labels ?? []);
  if (labelSet.has('Person')) return '#ff7b3d';
  if (labelSet.has('Organization')) return '#0f7ad8';
  if (labelSet.has('Event')) return '#d5486f';
  if (labelSet.has('Consumer')) return '#1fb88e';
  return '#7c8aa6';
}

function edgeLabel(edge: RawGraphEdge) {
  return (edge.fact_type ?? edge.name ?? edge.fact ?? 'RELATED_TO').replaceAll('_', ' ');
}

function buildSnapshotGraph(snapshot: RawGraphSnapshot): KnowledgeGraphData {
  const nodeMap = new Map(snapshot.nodes.map((node) => [node.uuid, node]));
  const adjacency = new Map<string, Set<string>>();

  for (const edge of snapshot.edges) {
    if (!adjacency.has(edge.source_node_uuid)) adjacency.set(edge.source_node_uuid, new Set());
    if (!adjacency.has(edge.target_node_uuid)) adjacency.set(edge.target_node_uuid, new Set());
    adjacency.get(edge.source_node_uuid)?.add(edge.target_node_uuid);
    adjacency.get(edge.target_node_uuid)?.add(edge.source_node_uuid);
  }

  let hubNodeId = snapshot.nodes[0]?.uuid ?? '';
  let maxDegree = -1;

  for (const node of snapshot.nodes) {
    const degree = adjacency.get(node.uuid)?.size ?? 0;
    if (degree > maxDegree) {
      maxDegree = degree;
      hubNodeId = node.uuid;
    }
  }

  const selectedIds = new Set<string>();
  const queue = [hubNodeId];

  while (queue.length > 0 && selectedIds.size < 18) {
    const current = queue.shift();
    if (!current || selectedIds.has(current)) continue;
    selectedIds.add(current);

    const neighbors = [...(adjacency.get(current) ?? [])].sort(
      (left, right) => (adjacency.get(right)?.size ?? 0) - (adjacency.get(left)?.size ?? 0),
    );

    for (const neighbor of neighbors) {
      if (!selectedIds.has(neighbor) && queue.length < 40) {
        queue.push(neighbor);
      }
    }
  }

  if (selectedIds.size < 18) {
    const highDegreeIds = [...snapshot.nodes]
      .sort((left, right) => (adjacency.get(right.uuid)?.size ?? 0) - (adjacency.get(left.uuid)?.size ?? 0))
      .map((node) => node.uuid);

    for (const nodeId of highDegreeIds) {
      selectedIds.add(nodeId);
      if (selectedIds.size >= 18) break;
    }
  }

  const selectedEdges = snapshot.edges
    .filter((edge) => selectedIds.has(edge.source_node_uuid) && selectedIds.has(edge.target_node_uuid))
    .slice(0, 24);

  const chosenNodes = [...selectedIds]
    .map((id) => nodeMap.get(id))
    .filter((node): node is RawGraphNode => Boolean(node))
    .sort((left, right) => (adjacency.get(right.uuid)?.size ?? 0) - (adjacency.get(left.uuid)?.size ?? 0));

  const centerX = 380;
  const centerY = 210;

  return {
    nodes: chosenNodes.map((node, index) => {
      const ring = index === 0 ? 0 : Math.floor((index - 1) / 6) + 1;
      const offsetIndex = index === 0 ? 0 : (index - 1) % 6;
      const radius = ring === 0 ? 0 : 88 + (ring - 1) * 78;
      const angle = ring === 0 ? 0 : (Math.PI * 2 * offsetIndex) / 6 + ring * 0.32;

      return {
        id: node.uuid,
        label: node.name,
        x: ring === 0 ? centerX : centerX + Math.cos(angle) * radius,
        y: ring === 0 ? centerY : centerY + Math.sin(angle) * radius,
        color: nodeColor(node.labels),
      };
    }),
    edges: selectedEdges.map((edge) => ({
      id: edge.uuid,
      from: edge.source_node_uuid,
      to: edge.target_node_uuid,
      label: edgeLabel(edge),
    })),
  };
}

export const SNAPSHOT_GRAPH = buildSnapshotGraph(rawSnapshot);

function snapshotMetricCards(snapshot: RawGraphSnapshot): MetricCard[] {
  return [
    { label: '全量节点', value: String(snapshot.node_count), detail: '来自仓库内置快照。', tone: 'green' },
    { label: '全量边', value: String(snapshot.edge_count), detail: '已用于构建关系网络。', tone: 'blue' },
    {
      label: '当前子图',
      value: `${SNAPSHOT_GRAPH.nodes.length} / ${SNAPSHOT_GRAPH.edges.length}`,
      detail: '用于当前会话中的可视化展示。',
      tone: 'yellow',
    },
    {
      label: '图谱中心',
      value: SNAPSHOT_GRAPH.nodes[0]?.label ?? '未知',
      detail: '按连通度选出的高关联节点。',
      tone: 'red',
    },
  ];
}

function personaNodeColor(entityType?: string) {
  if (entityType === 'Person') return '#1e6fd9';
  if (entityType === 'Organization') return '#7f8da8';
  return '#a1acc2';
}

function personaDistributionBars(personas: RawPersona[]): DistributionBar[] {
  const counts = personas.reduce(
    (accumulator, persona) => {
      if (persona.source_entity_type === 'Person') accumulator.person += 1;
      else if (persona.source_entity_type === 'Organization') accumulator.organization += 1;
      else accumulator.other += 1;
      return accumulator;
    },
    { person: 0, organization: 0, other: 0 },
  );

  return [
    { label: '人物', value: counts.person, color: '#1e6fd9' },
    { label: '机构', value: counts.organization, color: '#7f8da8' },
    { label: '其他', value: counts.other, color: '#c4ccd9' },
  ];
}

type PersonaLink = {
  id: string;
  from: string;
  to: string;
  label: string;
  weight: number;
};

function buildPersonaLinks(personas: RawPersona[]) {
  const links: PersonaLink[] = [];

  for (let leftIndex = 0; leftIndex < personas.length; leftIndex += 1) {
    for (let rightIndex = leftIndex + 1; rightIndex < personas.length; rightIndex += 1) {
      const left = personas[leftIndex];
      const right = personas[rightIndex];
      const sharedTopics = (left.interested_topics ?? []).filter((topic) => (right.interested_topics ?? []).includes(topic));

      let label = '';
      let weight = 0;

      if (sharedTopics.length > 0) {
        label = clampText(sharedTopics[0], 16);
        weight = 3 + sharedTopics.length;
      } else if (left.source_entity_type && left.source_entity_type === right.source_entity_type) {
        label = left.source_entity_type === 'Person' ? '同类人物' : '同类机构';
        weight = 2;
      } else if (left.country && right.country && left.country === right.country) {
        label = left.country;
        weight = 1;
      }

      if (!label) continue;

      links.push({
        id: `persona-link-${left.user_id}-${right.user_id}`,
        from: left.source_entity_uuid ?? `persona-${left.user_id}`,
        to: right.source_entity_uuid ?? `persona-${right.user_id}`,
        label,
        weight,
      });
    }
  }

  return links.sort((left, right) => right.weight - left.weight || left.label.localeCompare(right.label));
}

export function buildGraphSourceFromPersonas(personas: RawPersona[]): GraphScenarioSource {
  const normalizedPersonas = personas.filter((persona) => persona.name && persona.source_entity_uuid);
  const allLinks = buildPersonaLinks(normalizedPersonas);
  const selectedIds = new Set<string>();
  const selectedLinks: PersonaLink[] = [];

  for (const link of allLinks) {
    selectedLinks.push(link);
    selectedIds.add(link.from);
    selectedIds.add(link.to);
    if (selectedLinks.length >= 24 && selectedIds.size >= 12) break;
  }

  for (const persona of normalizedPersonas) {
    selectedIds.add(persona.source_entity_uuid ?? `persona-${persona.user_id}`);
    if (selectedIds.size >= 18) break;
  }

  const chosenPersonas = normalizedPersonas
    .filter((persona) => selectedIds.has(persona.source_entity_uuid ?? `persona-${persona.user_id}`))
    .slice(0, 18);

  const centerX = 380;
  const centerY = 210;

  const graph: KnowledgeGraphData = {
    nodes: chosenPersonas.map((persona, index) => {
      const ring = index === 0 ? 0 : Math.floor((index - 1) / 6) + 1;
      const offsetIndex = index === 0 ? 0 : (index - 1) % 6;
      const radius = ring === 0 ? 0 : 86 + (ring - 1) * 74;
      const angle = ring === 0 ? 0 : (Math.PI * 2 * offsetIndex) / 6 + ring * 0.28;

      return {
        id: persona.source_entity_uuid ?? `persona-${persona.user_id}`,
        label: clampText(persona.name, 12),
        x: ring === 0 ? centerX : centerX + Math.cos(angle) * radius,
        y: ring === 0 ? centerY : centerY + Math.sin(angle) * radius,
        color: personaNodeColor(persona.source_entity_type),
      };
    }),
    edges: selectedLinks
      .filter((link) => selectedIds.has(link.from) && selectedIds.has(link.to))
      .slice(0, 24)
      .map((link) => ({
        id: link.id,
        from: link.from,
        to: link.to,
        label: link.label.toUpperCase(),
      })),
  };

  return {
    sourceLabel: 'proj_e3a2f7b5ffa0_personas.json',
    badge: 'personas',
    nodeCount: normalizedPersonas.length,
    edgeCount: allLinks.length,
    graph,
    metrics: [
      { label: '画像条目', value: String(normalizedPersonas.length), detail: '来自 public 下的 personas 文件。', tone: 'green' },
      { label: '推导关系', value: String(allLinks.length), detail: '按共同话题、实体类型和国家推导。', tone: 'blue' },
      {
        label: '当前视图',
        value: `${graph.nodes.length} / ${graph.edges.length}`,
        detail: '当前展示的子图节点与关系数量。',
        tone: 'yellow',
      },
      {
        label: '中心画像',
        value: graph.nodes[0]?.label ?? '未知',
        detail: '优先选择关联更强的节点进入中心区。',
        tone: 'red',
      },
    ],
    bars: personaDistributionBars(normalizedPersonas),
    introTitle: '画像图谱模式',
    introLines: [
      '已优先载入 public 下的 personas JSON，而不是仓库内置 snapshot。',
      '当前边关系由共同兴趣、同类实体和同国家规则推导生成。',
      '节点和边会继续按流式方式逐步出现，便于模拟分析过程。',
    ],
    summary: `已从 personas 文件中加载 ${normalizedPersonas.length} 条画像记录，并推导出 ${allLinks.length} 条关系，当前展示核心子图视图。`,
  };
}

export const DEFAULT_GRAPH_SOURCE: GraphScenarioSource = {
  sourceLabel: 'graph-snapshot.json',
  badge: 'snapshot',
  nodeCount: rawSnapshot.node_count,
  edgeCount: rawSnapshot.edge_count,
  graph: SNAPSHOT_GRAPH,
  metrics: snapshotMetricCards(rawSnapshot),
  bars: graphTypeBars(rawSnapshot),
  introTitle: '图谱模式',
  introLines: [
    '已载入真实图谱快照，而不是前面的手写 mock。',
    '当前展示的是从全量关系里抽取出的高关联子图。',
    '节点和边会以流式方式逐步出现，方便模拟实时分析过程。',
  ],
  summary: `已从 graph-snapshot.json 中加载 ${rawSnapshot.node_count} 个节点、${rawSnapshot.edge_count} 条边，当前展示核心子图视图。`,
};

export const TSLA_KLINE: KlineCandle[] = [
  { time: '09:30', open: 241.2, high: 243.8, low: 239.6, close: 242.9, volume: 1200 },
  { time: '10:00', open: 242.9, high: 244.1, low: 241.8, close: 243.5, volume: 980 },
  { time: '10:30', open: 243.5, high: 245.2, low: 242.1, close: 244.8, volume: 1100 },
  { time: '11:00', open: 244.8, high: 246.3, low: 243.4, close: 243.9, volume: 890 },
  { time: '11:30', open: 243.9, high: 244.6, low: 240.8, close: 241.4, volume: 1320 },
  { time: '13:00', open: 241.4, high: 242.7, low: 239.9, close: 240.6, volume: 1480 },
  { time: '13:30', open: 240.6, high: 241.9, low: 238.7, close: 239.1, volume: 1670 },
  { time: '14:00', open: 239.1, high: 240.4, low: 236.8, close: 237.4, volume: 1710 },
  { time: '14:30', open: 237.4, high: 239.2, low: 236.5, close: 238.6, volume: 1400 },
  { time: '15:00', open: 238.6, high: 240.7, low: 237.8, close: 240.1, volume: 1180 },
  { time: '15:30', open: 240.1, high: 242.2, low: 239.7, close: 241.6, volume: 960 },
  { time: '16:00', open: 241.6, high: 243.1, low: 240.8, close: 242.4, volume: 840 },
];

export const PRESSURE_METRICS: MetricCard[] = [
  { label: '健康评分', value: '85 / 100', detail: '风险偏好良好，但集中度偏高。', tone: 'green' },
  { label: '仓位暴露', value: 'TSLA 18%', detail: '高于建议的单标的上限。', tone: 'yellow' },
  { label: '最大回撤', value: '12.5%', detail: '压力情景下仍需留意波动。', tone: 'red' },
  { label: '组合分散度', value: '良好', detail: '行业覆盖尚可，需压缩科技权重。', tone: 'blue' },
];

export const PRESSURE_BARS: DistributionBar[] = [
  { label: '科技', value: 54, color: '#16e07f' },
  { label: '消费', value: 18, color: '#19d3c5' },
  { label: '工业', value: 14, color: '#f7c948' },
  { label: '现金', value: 14, color: '#8a93a7' },
];

export const BACKTEST_SNIPPET = `RUN_BACKTEST / OK

ARGS
{
  "start_date": "2023-09-30",
  "end_date": "2023-10-30",
  "codes": [
    "TSLA"
  ],
  "signal_code": "stress_test_v2"
}

RESULT
{
  "status": "ok",
  "metrics": {
    "final_value": 793457.31,
    "total_return": -0.2065,
    "annual_return": -0.9377,
    "max_drawdown": -0.2513,
    "sharpe": -5.3640,
    "sortino": -6.3603
  }
}`;

export const MATRIX_TERMINAL_MOCK: MatrixTerminalPayload = {
  title: 'OPEN MATRIX',
  version: 'v2.0.1 / REACT STACK ONLINE',
  sync: '8ms',
  profile: [
    { label: '风险偏好', value: 'moderate', tone: 'green' },
    { label: '投资风格', value: 'growth', tone: 'green' },
    { label: '资金规模', value: '中型', tone: 'blue' },
  ],
  layers: [
    { label: '情绪', cells: [{ id: 'X1Y1' }, { id: 'X1Y2' }, { id: 'X1Y3' }, { id: 'X1Y4' }] },
    { label: '技术面', cells: [{ id: 'X2Y1' }, { id: 'X2Y2' }, { id: 'X2Y3' }, { id: 'X2Y4' }] },
    { label: '战术', cells: [{ id: 'X3Y1' }, { id: 'X3Y2', active: true }, { id: 'X3Y3' }, { id: 'X3Y4' }] },
    { label: '宏观', cells: [{ id: 'X4Y1' }, { id: 'X4Y2' }, { id: 'X4Y3' }, { id: 'X4Y4' }] },
    { label: '博弈进化', cells: [{ id: 'X5Y1' }, { id: 'X5Y2', active: true }, { id: 'X5Y3' }, { id: 'X5Y4' }] },
  ],
  activeChain: 'X5Y2',
  userPrompt: '你回测一下，如果我全仓买入 TSLA，帮我做一份压力测试。',
  assistantGreeting: 'Hello! 我是 Sucker，你的智能交易矩阵助手。',
  assistantSummary:
    '压力测试已完成。组合健康度尚可，但 TSLA 暴露偏高，需要压缩单标的权重，并注意高波动时段的回撤风险。',
  assistantTag: 'BUFFETT-PERSPECTIVE',
  insights: [
    { title: '实时情绪比率', value: 'BULLISH (0.75)', detail: '较上周提升 2.4%', tone: 'green' },
    { title: '风险屏障', value: 'PORTFOLIO DIVERSIFIED', detail: '阈值：最大回撤 12.5%', tone: 'yellow' },
    { title: '矩阵定位', value: '系统延迟 0ms', detail: '[ROUTING] 稳定在线', tone: 'blue' },
  ],
  toolRuns: [
    {
      name: 'RUN_BACKTEST',
      status: 'OK',
      args: '{ "start_date": "2023-09-30", "end_date": "2023-10-30", "codes": ["TSLA"] }',
      result: '{ "final_value": 793457.31, "total_return": -0.2065, "max_drawdown": -0.2513 }',
    },
    {
      name: 'AUDIT_PORTFOLIO',
      status: 'OK',
      args: '{ "tech_weight": 0.54, "cash_ratio": 0.14 }',
      result: '{ "health_score": 85, "diversification": "Good", "recommendation": "Reduce TSLA exposure" }',
    },
  ],
};

function graphTypeBars(snapshot: RawGraphSnapshot): DistributionBar[] {
  const counts = snapshot.nodes.reduce(
    (accumulator, node) => {
      const labels = new Set(node.labels ?? []);
      if (labels.has('Person')) accumulator.person += 1;
      else if (labels.has('Organization')) accumulator.organization += 1;
      else if (labels.has('Event')) accumulator.event += 1;
      else accumulator.other += 1;
      return accumulator;
    },
    { person: 0, organization: 0, event: 0, other: 0 },
  );

  return [
    { label: '人物', value: counts.person, color: '#ff7b3d' },
    { label: '组织', value: counts.organization, color: '#0f7ad8' },
    { label: '事件', value: counts.event, color: '#d5486f' },
    { label: '其他', value: counts.other, color: '#7c8aa6' },
  ];
}

function buildGraphScenario(graphSource: GraphScenarioSource): DialogueMessage[] {
  return [
    {
      id: createId('assistant-md'),
      role: 'assistant',
      kind: 'markdown',
      title: graphSource.introTitle,
      content: `### 已切换到知识图谱模式\n\n- ${graphSource.introLines.join('\n- ')}`,
    },
    {
      id: createId('assistant-graph'),
      role: 'assistant',
      kind: 'knowledge-graph',
      title: graphSource.badge === 'personas' ? 'Persona Graph / Live Subgraph' : 'Graph Snapshot / Live Subgraph',
      content: graphSource.summary,
      badge: graphSource.badge,
      graph: graphSource.graph,
    },
    {
      id: createId('assistant-panel'),
      role: 'assistant',
      kind: 'data-viz',
      title: '图谱统计面板',
      metrics: graphSource.metrics,
      bars: graphSource.bars,
    },
  ];
}

function buildRiskScenario(): DialogueMessage[] {
  return [
    {
      id: createId('assistant-md'),
      role: 'assistant',
      kind: 'markdown',
      title: '策略助手',
      content:
        '### 压力测试结果\n\n1. 健康评分维持在较高区间，但单标的暴露偏高。\n2. 当前组合的主要脆弱点在于科技仓位集中。\n3. 如果继续押注 TSLA，需要同步考虑回撤和替代配置。',
    },
    {
      id: createId('assistant-viz'),
      role: 'assistant',
      kind: 'data-viz',
      title: '风险与分散度面板',
      metrics: PRESSURE_METRICS,
      bars: PRESSURE_BARS,
    },
    {
      id: createId('assistant-kline'),
      role: 'assistant',
      kind: 'kline',
      title: 'TSLA / Intraday Stress Window',
      subtitle: '盘中 K 线演示，模拟压力时段价格与成交量变化。',
      candles: TSLA_KLINE,
    },
    {
      id: createId('assistant-code'),
      role: 'assistant',
      kind: 'code-block',
      title: '回测执行日志',
      status: 'OK',
      language: 'json',
      code: BACKTEST_SNIPPET,
    },
  ];
}

function buildMatrixScenario(): DialogueMessage[] {
  return [
    {
      id: createId('assistant-md'),
      role: 'assistant',
      kind: 'markdown',
      title: '终端模式',
      content:
        '### 已切换到矩阵终端视图\n\n- 会渲染交易画像、20 格矩阵、实时洞察和任务链。\n- 当前全部数据都来自统一 mock 注册表，后面可直接切到 API 返回。\n- 这个卡片就是为承接你给的终端参考图准备的。',
    },
    {
      id: createId('assistant-matrix'),
      role: 'assistant',
      kind: 'matrix-terminal',
      payload: MATRIX_TERMINAL_MOCK,
    },
    {
      id: createId('assistant-code'),
      role: 'assistant',
      kind: 'code-block',
      title: '终端任务链日志',
      status: 'READY',
      language: 'json',
      code: `{
  "active_chain": "${MATRIX_TERMINAL_MOCK.activeChain}",
  "assistant_tag": "${MATRIX_TERMINAL_MOCK.assistantTag}",
  "tool_runs": ${MATRIX_TERMINAL_MOCK.toolRuns.length},
  "sync": "${MATRIX_TERMINAL_MOCK.sync}"
}`,
    },
  ];
}

function buildDefaultScenario(input: string): DialogueMessage[] {
  return [
    {
      id: createId('assistant-text'),
      role: 'assistant',
      kind: 'text',
      content: `已收到“${input}”。这个新对话页现在支持文本、Markdown、知识图谱、K 线、数据面板、代码块和交易终端卡片。`,
    },
    {
      id: createId('assistant-md'),
      role: 'assistant',
      kind: 'markdown',
      title: '可用组件',
      content:
        '### 你可以这样触发\n\n- 输入“知识图谱”查看真实快照子图与统计面板。\n- 输入“TSLA 压力测试”查看 K 线、指标卡和代码块。\n- 输入“矩阵”或“交易终端”查看终端式卡片。\n- 其他问题先走普通对话，后面我们可以继续挂更多业务组件。',
    },
  ];
}

export function buildAssistantReplyBundle(input: string, graphSource: GraphScenarioSource = DEFAULT_GRAPH_SOURCE): DialogueMessage[] {
  if (/知识图谱|关系图|graph/i.test(input)) {
    return buildGraphScenario(graphSource);
  }

  if (/TSLA|压力测试|回测|风险|stress/i.test(input)) {
    return buildRiskScenario();
  }

  if (/矩阵|交易终端|画像|matrix|dashboard/i.test(input)) {
    return buildMatrixScenario();
  }

  return buildDefaultScenario(input);
}
