import { appendFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { inspect } from 'node:util';
import OpenAI from 'openai';
import { NextResponse } from 'next/server';
import { LEEK_CHARACTERS, LEEK_SCENARIOS } from '../../lib/leek-lore';

type IncomingMessage = {
  role: 'user' | 'assistant';
  content: string;
};

type IncomingPeep = {
  id?: string;
  hair?: string;
  body?: string;
  face?: string;
  facialHair?: string;
  accessory?: string;
};

type StoryPanel = {
  panelId: string;
  text: string;
  dark?: boolean;
};

type StoryPage = {
  id: string;
  summary: string;
  panels: StoryPanel[];
};

type StoryResponse = {
  reply: string;
  pages: StoryPage[];
};

const PANEL_IDS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'] as const;
const DEBUG_PREFIX = '[api/chat]';
const DEBUG_LOG_DIR = join(process.cwd(), 'debug');
const DEBUG_LOG_FILE = join(DEBUG_LOG_DIR, 'chat-api.log');

function normalizeOpenAIBaseURL(value: string | undefined): string | undefined {
  if (!value) {
    return value;
  }

  const trimmed = value.trim().replace(/\/+$/, '');
  if (!trimmed) {
    return undefined;
  }

  try {
    const url = new URL(trimmed);
    if (url.pathname === '' || url.pathname === '/') {
      url.pathname = '/v1';
      return url.toString().replace(/\/+$/, '');
    }

    return trimmed;
  } catch {
    return trimmed.endsWith('/v1') ? trimmed : `${trimmed}/v1`;
  }
}

function previewText(value: string | null | undefined, length = 220): string {
  if (!value) {
    return '<empty>';
  }

  return value.replace(/\s+/g, ' ').trim().slice(0, length);
}

function logDebug(message: string, details?: Record<string, unknown>) {
  if (details) {
    console.info(`${DEBUG_PREFIX} ${message}`, details);
    return;
  }

  console.info(`${DEBUG_PREFIX} ${message}`);
}

function previewJson(value: unknown, length = 500): string {
  try {
    return previewText(JSON.stringify(value), length);
  } catch {
    return '<unserializable>';
  }
}

function inspectValue(value: unknown): string {
  return inspect(value, {
    depth: 8,
    maxArrayLength: 200,
    maxStringLength: 20000,
    breakLength: 120,
    compact: false,
    sorted: true,
  });
}

async function writeDebugDump(label: string, payload: Record<string, unknown>) {
  try {
    await mkdir(DEBUG_LOG_DIR, { recursive: true });
    await appendFile(
      DEBUG_LOG_FILE,
      [
        `\n===== ${new Date().toISOString()} ${label} =====`,
        inspectValue(payload),
        '',
      ].join('\n'),
      'utf8',
    );
  } catch (error) {
    console.error(`${DEBUG_PREFIX} failed to write debug dump`, { error });
  }
}

function extractCompletionContent(completion: unknown): {
  content: string | null;
  finishReason: string | null;
  shape: string;
  topLevelKeys: string[];
  ownPropertyNames: string[];
  constructorName: string;
  rawPreview: string;
} {
  const record = completion && typeof completion === 'object' ? (completion as Record<string, unknown>) : null;
  const topLevelKeys = record ? Object.keys(record) : [];
  const ownPropertyNames = record ? Object.getOwnPropertyNames(record) : [];
  const constructorName = completion && typeof completion === 'object' && (completion as { constructor?: { name?: string } }).constructor?.name
    ? (completion as { constructor: { name: string } }).constructor.name
    : typeof completion;
  const rawPreview = previewJson(completion);

  const readMessageContent = (value: unknown): string | null => {
    if (typeof value === 'string') {
      return value;
    }

    if (Array.isArray(value)) {
      const textParts = value
        .map((item) => {
          if (typeof item === 'string') {
            return item;
          }

          if (item && typeof item === 'object') {
            const piece = item as Record<string, unknown>;
            if (typeof piece.text === 'string') {
              return piece.text;
            }
          }

          return '';
        })
        .filter(Boolean);

      return textParts.length ? textParts.join('\n') : null;
    }

    return null;
  };

  const choices = Array.isArray(record?.choices) ? record.choices : null;
  if (choices?.length) {
    const firstChoice = choices[0] as Record<string, unknown>;
    const message = firstChoice?.message as Record<string, unknown> | undefined;
    return {
      content: readMessageContent(message?.content),
      finishReason: typeof firstChoice?.finish_reason === 'string' ? firstChoice.finish_reason : null,
      shape: 'choices',
      topLevelKeys,
      ownPropertyNames,
      constructorName,
      rawPreview,
    };
  }

  const dataChoices = record?.data && typeof record.data === 'object' && Array.isArray((record.data as Record<string, unknown>).choices)
    ? ((record.data as Record<string, unknown>).choices as unknown[])
    : null;
  if (dataChoices?.length) {
    const firstChoice = dataChoices[0] as Record<string, unknown>;
    const message = firstChoice?.message as Record<string, unknown> | undefined;
    return {
      content: readMessageContent(message?.content),
      finishReason: typeof firstChoice?.finish_reason === 'string' ? firstChoice.finish_reason : null,
      shape: 'data.choices',
      topLevelKeys,
      ownPropertyNames,
      constructorName,
      rawPreview,
    };
  }

  if (typeof record?.output_text === 'string') {
    return {
      content: record.output_text,
      finishReason: null,
      shape: 'output_text',
      topLevelKeys,
      ownPropertyNames,
      constructorName,
      rawPreview,
    };
  }

  const output = Array.isArray(record?.output) ? record.output : null;
  if (output?.length) {
    const textParts = output
      .flatMap((entry) => {
        if (!entry || typeof entry !== 'object') {
          return [] as string[];
        }

        const piece = entry as Record<string, unknown>;
        const content = Array.isArray(piece.content) ? piece.content : [];
        return content
          .map((item) => {
            if (!item || typeof item !== 'object') {
              return '';
            }

            const contentPiece = item as Record<string, unknown>;
            if (typeof contentPiece.text === 'string') {
              return contentPiece.text;
            }

            return '';
          })
          .filter(Boolean);
      })
      .filter(Boolean);

    return {
      content: textParts.length ? textParts.join('\n') : null,
      finishReason: null,
      shape: 'output',
      topLevelKeys,
      ownPropertyNames,
      constructorName,
      rawPreview,
    };
  }

  return {
    content: null,
    finishReason: null,
    shape: 'unknown',
    topLevelKeys,
    ownPropertyNames,
    constructorName,
    rawPreview,
  };
}

function buildPage(pageNumber: number, baseText: string, prompt: string): StoryPage {
  return {
    id: `page-${pageNumber}`,
    summary: baseText,
    panels: PANEL_IDS.map((panelId, index) => ({
      panelId,
      text: `${baseText} 第${index + 1}拍：${prompt || '他开始复盘那次被套的全过程。'}`,
      dark: panelId === '2' || panelId === '7',
    })),
  };
}

function buildFallbackStory(prompt: string, currentStory?: Partial<StoryResponse>): StoryResponse {
  const existingPages = Array.isArray(currentStory?.pages) ? currentStory.pages : [];
  const nextPageNumber = existingPages.length + 1;
  const storyline = prompt || '他回忆自己为什么会在高位接盘';
  const nextPage = buildPage(nextPageNumber, `第${nextPageNumber}页，他继续回忆：${storyline}`, storyline);

  return {
    reply: `我先按你的追问把这段经历继续展开到了第${nextPageNumber}页，你可以继续追问更细的节点，比如补仓、爆仓、割肉、回本幻觉。`,
    pages: [...existingPages, nextPage],
  };
}

function normalizeStoryPayload(payload: unknown, fallback: StoryResponse): StoryResponse {
  if (!payload || typeof payload !== 'object') {
    return fallback;
  }

  const candidate = payload as Partial<StoryResponse>;
  if (!Array.isArray(candidate.pages) || typeof candidate.reply !== 'string') {
    return fallback;
  }

  const pages = candidate.pages
    .map((page, pageIndex) => {
      if (!page || typeof page !== 'object' || !Array.isArray(page.panels)) {
        return null;
      }

      const panels = page.panels
        .filter((panel): panel is StoryPanel => Boolean(panel && typeof panel === 'object' && typeof panel.panelId === 'string' && typeof panel.text === 'string'))
        .map((panel) => ({
          panelId: PANEL_IDS.includes(panel.panelId as (typeof PANEL_IDS)[number]) ? panel.panelId : PANEL_IDS[0],
          text: panel.text.trim(),
          dark: Boolean(panel.dark),
        }));

      if (!panels.length) {
        return null;
      }

      return {
        id: typeof page.id === 'string' && page.id ? page.id : `page-${pageIndex + 1}`,
        summary: typeof page.summary === 'string' && page.summary ? page.summary : `第${pageIndex + 1}页`,
        panels,
      };
    })
    .filter((page): page is StoryPage => page !== null);

  if (!pages.length) {
    return fallback;
  }

  return {
    reply: candidate.reply,
    pages,
  };
}

export async function POST(request: Request) {
  const startedAt = Date.now();
  const configuredBaseURL = process.env.OPENAI_BASE_URL;
  const effectiveBaseURL = normalizeOpenAIBaseURL(configuredBaseURL);

  try {
    const body = await request.json();
    const configIndex = typeof body.configIndex === 'number' ? body.configIndex : 0;
    
    // Multi-config support
    let configs: { key: string; url?: string; model?: string }[] = [];
    try {
      if (process.env.OPENAI_CONFIGS) {
        configs = JSON.parse(process.env.OPENAI_CONFIGS);
      }
    } catch (e) {
      logDebug('failed to parse OPENAI_CONFIGS', { error: e });
    }

    // Default fallback
    if (configs.length === 0 && process.env.OPENAI_API_KEY) {
      configs.push({
        key: process.env.OPENAI_API_KEY,
        url: normalizeOpenAIBaseURL(process.env.OPENAI_BASE_URL),
        model: process.env.OPENAI_MODEL || 'gpt-4o-mini'
      });
    }

    const activeConfig = configs[configIndex] || configs[0];

    const messages = Array.isArray(body.messages) ? (body.messages as IncomingMessage[]) : [];
    const peep = (body.peep ?? {}) as IncomingPeep;
    const persona = body.persona as LeekPersona | undefined;
    const currentStory = body.currentStory as Partial<StoryResponse> | undefined;
    const lastUserMessage = [...messages].reverse().find((message) => message.role === 'user')?.content?.trim() ?? '';
    const fallback = buildFallbackStory(lastUserMessage, currentStory);

    logDebug('request received', {
      configIndex,
      usedModel: activeConfig?.model,
      messageCount: messages.length,
      currentStoryPages: Array.isArray(currentStory?.pages) ? currentStory.pages.length : 0,
      lastUserMessage: previewText(lastUserMessage, 120),
      peepId: peep.id ?? '<none>',
      hasPersona: Boolean(persona),
      hasApiKey: Boolean(activeConfig?.key),
    });

    if (!activeConfig?.key) {
      logDebug('missing API key for config index, returning fallback story', {
        index: configIndex,
        durationMs: Date.now() - startedAt,
      });
      return NextResponse.json(fallback);
    }

    try {
      const client = new OpenAI({
        apiKey: activeConfig.key,
        baseURL: activeConfig.url,
      });

      const completion = await client.chat.completions.create({
        model: activeConfig.model || 'gpt-4o-mini',
        response_format: { type: 'json_object' },
        messages: [
          {
            role: 'system',
            content: [
              '你是一个冷静、克制但内心充满波动的资深散户（韭菜）。',
              '你的任务是将散户被市场收割的真实经历，转化为一组黑白漫画分镜。',
              '【核心风格】：',
              '1. 视角：必须以第一人称或极其贴近散户心理的视角叙述。',
              '2. 语气：短句为主。冷峻、自嘲、克制。不要有“AI 助手”式的礼貌或建议。',
              '3. 细节：要包含具体的心理博弈（如：再拿一下就回本、这是主力在洗盘）和物理细节（如：香烟灰缸满了、深夜屏幕的蓝光）。',
              '4. 黑话：熟练使用散户圈黑话（如：梭哈、割肉、格局、抄底、回本幻觉）。',
              '【输出格式】：',
              '返回 JSON 对象，结构必须是 {"reply": string, "pages": [{"id": string, "summary": string, "panels": [{"panelId": "1"-"10", "text": string, "dark": boolean}]}] }。',
              '每页最多 10 格，panelId 只能用 1 到 10。要在已有故事基础上续写，保持连贯。',
            ].join('\n'),
          },
          {
            role: 'user',
            content: JSON.stringify({
              context: {
                archetypes: LEEK_CHARACTERS,
                suggested_scenarios: LEEK_SCENARIOS,
                active_persona: persona, // Inject the detailed persona if available
              },
              peep,
              conversation: messages,
              currentStory,
              request: lastUserMessage,
            }),
          },
        ],
      });

      const extracted = extractCompletionContent(completion);
      await writeDebugDump('upstream completion', {
        requestSummary: {
          durationMs: Date.now() - startedAt,
          model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
          configuredBaseURL: configuredBaseURL ?? '<default>',
          effectiveBaseURL: effectiveBaseURL ?? '<default>',
          lastUserMessage,
          messageCount: messages.length,
          currentStoryPages: Array.isArray(currentStory?.pages) ? currentStory.pages.length : 0,
          peepId: peep.id ?? '<none>',
        },
        extracted,
        completionJson: completion,
        completionInspect: inspectValue(completion),
      });

      logDebug('openai response received', {
        durationMs: Date.now() - startedAt,
        finishReason: extracted.finishReason ?? '<unknown>',
        responseShape: extracted.shape,
        topLevelKeys: extracted.topLevelKeys,
        ownPropertyNames: extracted.ownPropertyNames,
        constructorName: extracted.constructorName,
        debugLogFile: DEBUG_LOG_FILE,
        rawPreview: extracted.rawPreview,
        contentPreview: previewText(extracted.content),
      });

      if (!extracted.content) {
        logDebug('empty model content, returning fallback story', {
          durationMs: Date.now() - startedAt,
          responseShape: extracted.shape,
          topLevelKeys: extracted.topLevelKeys,
        });
        return NextResponse.json(fallback);
      }

      const parsed = JSON.parse(extracted.content) as StoryResponse;
      const normalized = normalizeStoryPayload(parsed, fallback);

      logDebug('normalized story payload', {
        durationMs: Date.now() - startedAt,
        replyPreview: previewText(normalized.reply, 120),
        pageCount: normalized.pages.length,
        pageIds: normalized.pages.map((page) => page.id),
        panelCounts: normalized.pages.map((page) => page.panels.length),
      });

      return NextResponse.json(normalized);
    } catch (error) {
      await writeDebugDump('request failed', {
        durationMs: Date.now() - startedAt,
        errorInspect: inspectValue(error),
        lastUserMessage,
        model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
        configuredBaseURL: configuredBaseURL ?? '<default>',
        effectiveBaseURL: effectiveBaseURL ?? '<default>',
      });

      console.error(`${DEBUG_PREFIX} request failed, returning fallback story`, {
        durationMs: Date.now() - startedAt,
        error,
        lastUserMessage: previewText(lastUserMessage, 120),
        debugLogFile: DEBUG_LOG_FILE,
      });
      return NextResponse.json(fallback);
    }
  } catch (error) {
    await writeDebugDump('invalid request body', {
      durationMs: Date.now() - startedAt,
      errorInspect: inspectValue(error),
    });

    console.error(`${DEBUG_PREFIX} invalid request body`, {
      durationMs: Date.now() - startedAt,
      error,
      debugLogFile: DEBUG_LOG_FILE,
    });
    return NextResponse.json(buildFallbackStory(''));
  }
}
