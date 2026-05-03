export type KnowledgeGraphNode = {
  id: string;
  label: string;
  x: number;
  y: number;
  color: string;
};

export type KnowledgeGraphEdge = {
  id: string;
  from: string;
  to: string;
  label: string;
};

export type KnowledgeGraphData = {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
};

export type MetricCard = {
  label: string;
  value: string;
  detail: string;
  tone: 'green' | 'yellow' | 'red' | 'blue';
};

export type DistributionBar = {
  label: string;
  value: number;
  color: string;
};

export type KlineCandle = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type MatrixProfileItem = {
  label: string;
  value: string;
  tone: 'green' | 'blue' | 'yellow' | 'neutral';
};

export type MatrixLayer = {
  label: string;
  cells: Array<{
    id: string;
    active?: boolean;
  }>;
};

export type MatrixInsightCard = {
  title: string;
  value: string;
  detail: string;
  tone: 'green' | 'yellow' | 'blue';
};

export type MatrixToolRun = {
  name: string;
  status: string;
  args: string;
  result: string;
};

export type MatrixTerminalPayload = {
  title: string;
  version: string;
  sync: string;
  profile: MatrixProfileItem[];
  layers: MatrixLayer[];
  activeChain: string;
  userPrompt: string;
  assistantGreeting: string;
  assistantSummary: string;
  assistantTag: string;
  insights: MatrixInsightCard[];
  toolRuns: MatrixToolRun[];
};

export type DialogueMessage =
  | {
      id: string;
      role: 'user' | 'assistant';
      kind: 'text';
      content: string;
    }
  | {
      id: string;
      role: 'assistant';
      kind: 'markdown';
      title: string;
      content: string;
    }
  | {
      id: string;
      role: 'assistant';
      kind: 'knowledge-graph';
      title: string;
      content: string;
      badge?: string;
      graph: KnowledgeGraphData;
    }
  | {
      id: string;
      role: 'assistant';
      kind: 'kline';
      title: string;
      subtitle: string;
      candles: KlineCandle[];
    }
  | {
      id: string;
      role: 'assistant';
      kind: 'data-viz';
      title: string;
      metrics: MetricCard[];
      bars: DistributionBar[];
    }
  | {
      id: string;
      role: 'assistant';
      kind: 'code-block';
      title: string;
      status: string;
      language: string;
      code: string;
    }
  | {
      id: string;
      role: 'assistant';
      kind: 'matrix-terminal';
      payload: MatrixTerminalPayload;
    };
