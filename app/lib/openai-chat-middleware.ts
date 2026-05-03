import { buildAssistantReplyBundle, type GraphScenarioSource } from './dialogue-demo';
import type { DialogueMessage } from './dialogue-types';

export type OpenAIStyleChatMessage = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

export type OpenAIStyleChatRequest = {
  model?: string;
  messages: OpenAIStyleChatMessage[];
  temperature?: number;
  stream?: boolean;
  metadata?: Record<string, unknown>;
};

export type OpenAIStyleChatResponse = {
  id: string;
  object: 'chat.completion';
  created: number;
  model: string;
  choices: Array<{
    index: number;
    finish_reason: 'stop';
    message: {
      role: 'assistant';
      content: string;
      components: DialogueMessage[];
    };
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
};

function createCompletionId() {
  return `chatcmpl_mock_${Math.random().toString(36).slice(2, 10)}`;
}

export function getLastUserMessage(messages: OpenAIStyleChatMessage[]) {
  return [...messages].reverse().find((message) => message.role === 'user')?.content.trim() ?? '';
}

function summarizeComponents(components: DialogueMessage[]) {
  const summary = components.find((component) => component.kind === 'text');
  if (summary?.kind === 'text') {
    return summary.content;
  }

  const titled = components.find((component) => 'title' in component);
  if (titled && 'title' in titled) {
    return `已生成 ${titled.title} 相关内容。`;
  }

  return '已生成结构化回复。';
}

export function createMockOpenAIStyleChatCompletion(
  payload: OpenAIStyleChatRequest,
  graphSource?: GraphScenarioSource,
): OpenAIStyleChatResponse {
  const input = getLastUserMessage(payload.messages);
  const components = buildAssistantReplyBundle(input, graphSource);
  const content = summarizeComponents(components);
  const promptTokens = JSON.stringify(payload.messages).length;
  const completionTokens = JSON.stringify(components).length;

  return {
    id: createCompletionId(),
    object: 'chat.completion',
    created: Math.floor(Date.now() / 1000),
    model: payload.model ?? 'mock-dialogue-model',
    choices: [
      {
        index: 0,
        finish_reason: 'stop',
        message: {
          role: 'assistant',
          content,
          components,
        },
      },
    ],
    usage: {
      prompt_tokens: promptTokens,
      completion_tokens: completionTokens,
      total_tokens: promptTokens + completionTokens,
    },
  };
}

export async function requestOpenAIStyleChatCompletion(
  endpoint: string,
  payload: OpenAIStyleChatRequest,
): Promise<OpenAIStyleChatResponse> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Dialogue API request failed with status ${response.status}`);
  }

  return (await response.json()) as OpenAIStyleChatResponse;
}
