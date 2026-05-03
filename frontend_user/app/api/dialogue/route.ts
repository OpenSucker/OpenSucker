import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { NextResponse } from 'next/server';
import {
  createMockOpenAIStyleChatCompletion,
  type OpenAIStyleChatRequest,
} from '../../lib/openai-chat-middleware';
import {
  buildGraphSourceFromPersonas,
  DEFAULT_GRAPH_SOURCE,
  PUBLIC_PERSONA_GRAPH_FILE,
} from '../../lib/dialogue-demo';

async function loadGraphSource() {
  try {
    const publicFilePath = path.join(process.cwd(), 'public', PUBLIC_PERSONA_GRAPH_FILE.replace(/^\//, ''));
    const rawFile = await readFile(publicFilePath, 'utf8');
    const parsed = JSON.parse(rawFile) as unknown;

    if (Array.isArray(parsed)) {
      const graphSource = buildGraphSourceFromPersonas(parsed);
      if (graphSource.graph.nodes.length > 0) {
        return graphSource;
      }
    }
  } catch {
    // Fall back to the bundled snapshot when the public personas file is unavailable.
  }

  return DEFAULT_GRAPH_SOURCE;
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as OpenAIStyleChatRequest;

    if (!payload?.messages || !Array.isArray(payload.messages)) {
      return NextResponse.json({ error: 'Invalid messages payload.' }, { status: 400 });
    }

    const graphSource = await loadGraphSource();
    const completion = createMockOpenAIStyleChatCompletion(payload, graphSource);
    return NextResponse.json(completion);
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
