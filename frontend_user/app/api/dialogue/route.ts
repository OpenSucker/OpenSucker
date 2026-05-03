import { NextResponse } from 'next/server';
import {
  getLastUserMessage,
  type OpenAIStyleChatRequest,
  type OpenAIStyleChatResponse,
} from '../../lib/openai-chat-middleware';
import { buildGraphSourceFromSnapshot, type GraphScenarioSource } from '../../lib/dialogue-demo';
import type { DialogueMessage, DistributionBar } from '../../lib/dialogue-types';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8866';
const MINIFISH_URL = process.env.MINIFISH_URL ?? 'http://localhost:5101';
const INFOFISH_URL = process.env.INFOFISH_URL ?? 'http://127.0.0.1:47822';

const FETCH_TIMEOUT_MS = 6000;

async function timedFetch(url: string, init?: RequestInit) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    return await fetch(url, { ...init, signal: controller.signal, cache: 'no-store' });
  } finally {
    clearTimeout(timer);
  }
}

type BackendChatResponse = {
  message: string;
  intent?: string;
  x_axis?: string;
  y_axis?: string;
  skill_used?: string;
  tools?: Array<{ name: string; args?: unknown; result?: unknown }>;
  debug?: { steps?: string[] };
};

async function callBackendChat(
  message: string,
  metadata: Record<string, unknown> | undefined,
): Promise<BackendChatResponse | null> {
  const sessionId =
    (metadata?.session_id as string | undefined) ?? `web-${Math.random().toString(36).slice(2, 10)}`;
  const userId = (metadata?.user_id as string | undefined) ?? 'web-user';
  try {
    const res = await timedFetch(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId, user_id: userId }),
    });
    if (!res.ok) return null;
    return (await res.json()) as BackendChatResponse;
  } catch {
    return null;
  }
}

async function fetchMinifishGraph(): Promise<GraphScenarioSource | null> {
  try {
    const listRes = await timedFetch(`${MINIFISH_URL}/api/graph/project/list?limit=20`);
    if (!listRes.ok) return null;
    const listJson = (await listRes.json()) as { success: boolean; data?: Array<Record<string, unknown>> };
    if (!listJson.success || !listJson.data?.length) return null;

    for (const project of listJson.data) {
      const graphId = (project.graph_id ?? project.last_graph_id ?? project.id) as string | undefined;
      const projectId = project.project_id as string | undefined;
      const candidates = [graphId, projectId].filter(Boolean) as string[];
      for (const id of candidates) {
        const dataRes = await timedFetch(`${MINIFISH_URL}/api/graph/data/${id}`);
        if (!dataRes.ok) continue;
        const dataJson = (await dataRes.json()) as {
          success: boolean;
          data?: { nodes: unknown[]; edges: unknown[]; node_count?: number; edge_count?: number };
        };
        if (!dataJson.success || !dataJson.data?.nodes?.length) continue;
        const snapshot = {
          nodes: dataJson.data.nodes as never,
          edges: dataJson.data.edges as never,
          node_count: dataJson.data.node_count ?? dataJson.data.nodes.length,
          edge_count: dataJson.data.edge_count ?? dataJson.data.edges.length,
        };
        return buildGraphSourceFromSnapshot(snapshot, {
          sourceLabel: `MiniFish · ${(project.project_name as string) ?? id}`,
          badge: 'MiniFish',
          introTitle: 'MiniFish 实时图谱',
          introLines: [
            `已从 MiniFish 项目 ${(project.project_name as string) ?? id} 拉取实时图谱。`,
            '当前展示按连通度抽取的高关联子图。',
            'Neo4j 中的节点和边将以流式方式逐步呈现。',
          ],
        });
      }
    }
    return null;
  } catch {
    return null;
  }
}

type InfoFishHot = {
  total_items: number;
  source_count: number;
  blocks: Array<{ source_id: string; source_name: string; count: number; items: Array<{ rank: number; title: string }> }>;
};

async function fetchInfoFishHot(limit = 5): Promise<InfoFishHot | null> {
  try {
    const res = await timedFetch(`${INFOFISH_URL}/api/hot?limit=${limit}`);
    if (!res.ok) return null;
    return (await res.json()) as InfoFishHot;
  } catch {
    return null;
  }
}

function infofishToBars(hot: InfoFishHot): DistributionBar[] {
  const palette = ['#16e07f', '#19d3c5', '#f7c948', '#ff7b3d', '#1fb88e', '#0f7ad8', '#d5486f', '#7c8aa6'];
  return hot.blocks.slice(0, palette.length).map((block, index) => ({
    label: block.source_name,
    value: block.count,
    color: palette[index],
  }));
}

function buildInfoFishMarkdown(hot: InfoFishHot, baseTitle = 'InfoFish · 全网舆情速览'): DialogueMessage {
  const lines: string[] = [`### ${baseTitle}`, '', `共 ${hot.source_count} 个源 / ${hot.total_items} 条热点`, ''];
  for (const block of hot.blocks.slice(0, 4)) {
    lines.push(`**${block.source_name}**`);
    for (const item of block.items.slice(0, 3)) {
      lines.push(`- ${item.rank}. ${item.title}`);
    }
    lines.push('');
  }
  return {
    id: `infofish-md-${Math.random().toString(36).slice(2, 8)}`,
    role: 'assistant',
    kind: 'markdown',
    title: 'InfoFish 数据源',
    content: lines.join('\n'),
  };
}

function shouldQueryInfoFish(input: string) {
  return /舆情|热点|新闻|news|hot|资讯|infofish/i.test(input);
}

function shouldQueryGraph(input: string) {
  return /知识图谱|关系图|graph|画像|persona/i.test(input);
}

function buildResponseEnvelope(
  payload: OpenAIStyleChatRequest,
  components: DialogueMessage[],
  summaryText: string,
): OpenAIStyleChatResponse {
  return {
    id: `chatcmpl_${Math.random().toString(36).slice(2, 10)}`,
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: payload.model ?? 'opensucker-router',
    choices: [
      {
        index: 0,
        finish_reason: 'stop',
        message: { role: 'assistant', content: summaryText, components },
      },
    ],
    usage: {
      prompt_tokens: JSON.stringify(payload.messages).length,
      completion_tokens: JSON.stringify(components).length,
      total_tokens: JSON.stringify(payload.messages).length + JSON.stringify(components).length,
    },
  };
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as OpenAIStyleChatRequest;
    if (!payload?.messages || !Array.isArray(payload.messages)) {
      return NextResponse.json({ error: 'Invalid messages payload.' }, { status: 400 });
    }

    const userMessage = getLastUserMessage(payload.messages);
    const wantGraph = shouldQueryGraph(userMessage);
    const wantNews = shouldQueryInfoFish(userMessage);

    const [backendReply, graphFromMinifish, infoFishHot] = await Promise.all([
      callBackendChat(userMessage, payload.metadata),
      wantGraph ? fetchMinifishGraph() : Promise.resolve(null),
      wantNews ? fetchInfoFishHot() : Promise.resolve(null),
    ]);

    const components: DialogueMessage[] = [];

    const replyText = backendReply?.message ?? '后端暂时无法响应，请稍后再试。';
    components.push({
      id: `backend-text-${Math.random().toString(36).slice(2, 8)}`,
      role: 'assistant',
      kind: 'text',
      content: replyText,
    });

    if (graphFromMinifish) {
      components.push({
        id: `minifish-graph-${Math.random().toString(36).slice(2, 8)}`,
        role: 'assistant',
        kind: 'knowledge-graph',
        title: graphFromMinifish.introTitle,
        content: graphFromMinifish.summary,
        badge: graphFromMinifish.badge,
        graph: graphFromMinifish.graph,
      });
    }

    if (infoFishHot && infoFishHot.blocks.length > 0) {
      components.push(buildInfoFishMarkdown(infoFishHot));
      components.push({
        id: `infofish-bars-${Math.random().toString(36).slice(2, 8)}`,
        role: 'assistant',
        kind: 'data-viz',
        title: 'InfoFish · 各源热度分布',
        metrics: [
          { label: '采集源', value: String(infoFishHot.source_count), detail: '当前在线源数量', tone: 'blue' },
          { label: '热点条数', value: String(infoFishHot.total_items), detail: '本次聚合返回的总条目', tone: 'green' },
        ],
        bars: infofishToBars(infoFishHot),
      });
    }

    return NextResponse.json(buildResponseEnvelope(payload, components, replyText));
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Failed to build dialogue completion.',
        detail: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 },
    );
  }
}
