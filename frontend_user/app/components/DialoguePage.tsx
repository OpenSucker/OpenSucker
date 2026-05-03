'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import comicStyles from './comicPage.module.css';
import styles from './dialoguePage.module.css';
import KnowledgeGraphMessage from './KnowledgeGraphMessage';
import MarkdownMessage from './MarkdownMessage';
import CodeBlockMessage from './CodeBlockMessage';
import CandlestickChartMessage from './CandlestickChartMessage';
import DataVizMessage from './DataVizMessage';
import TradingMatrixMessage from './TradingMatrixMessage';
import type { DialogueMessage } from '../lib/dialogue-types';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8866';

interface DialoguePageProps {
  onClose: () => void;
}

function createId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function generateShortId() {
  return Math.random().toString(36).slice(2, 12);
}

export default function DialoguePage({ onClose }: DialoguePageProps) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<DialogueMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [stepLabel, setStepLabel] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sessionIdRef = useRef(generateShortId());
  const userIdRef = useRef(generateShortId());

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = '0px';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [input]);

  useEffect(() => {
    const viewport = scrollRef.current;
    if (!viewport) return;
    viewport.scrollTop = viewport.scrollHeight;
  }, [messages, isLoading, stepLabel]);

  const hasMessages = messages.length > 0;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMessage: DialogueMessage = {
      id: createId('user'),
      role: 'user',
      kind: 'text',
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setStepLabel('📡 接入矩阵...');

    try {
      const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          session_id: sessionIdRef.current,
          user_id: userIdRef.current,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`后端响应异常: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          const line = part.trim();
          if (!line.startsWith('data: ')) continue;
          let event: Record<string, unknown>;
          try {
            event = JSON.parse(line.slice(6)) as Record<string, unknown>;
          } catch {
            continue;
          }

          if (event.type === 'step' || event.type === 'node') {
            setStepLabel((event.label as string) ?? '');
          } else if (event.type === 'done') {
            const msg = (event.message as string) ?? '';
            const intentCn = (event.intent_cn as string) || (event.intent as string) || '回复';
            setMessages((prev) => [
              ...prev,
              {
                id: createId('assistant'),
                role: 'assistant',
                kind: 'markdown',
                title: intentCn,
                content: msg,
              },
            ]);
          } else if (event.type === 'error') {
            setMessages((prev) => [
              ...prev,
              {
                id: createId('assistant-error'),
                role: 'assistant',
                kind: 'text',
                content: `错误: ${event.error as string}`,
              },
            ]);
          }
        }
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: createId('assistant-error'),
          role: 'assistant',
          kind: 'text',
          content: error instanceof Error ? error.message : '对话接口暂时不可用。',
        },
      ]);
    } finally {
      setIsLoading(false);
      setStepLabel('');
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      onClose();
      return;
    }

    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit(event as unknown as React.FormEvent);
    }
  };

  const statusText = useMemo(() => {
    if (isLoading) {
      return stepLabel || '正在连接 OpenSucker 矩阵后端...';
    }

    if (!hasMessages) {
      return '支持 Markdown、知识图谱、K 线图、数据可视化、代码块和交易终端卡片。';
    }

    return '对接 OpenSucker 矩阵后端，实时流式响应。';
  }, [hasMessages, isLoading, stepLabel]);

  const renderMessage = (message: DialogueMessage) => {
    if (message.kind === 'text') {
      return (
        <div
          className={`${comicStyles.messageBubble} ${
            message.role === 'user' ? comicStyles.messageUser : comicStyles.messageAssistant
          } ${styles.messageCard}`}
        >
          {message.content}
        </div>
      );
    }

    if (message.kind === 'knowledge-graph') {
      return (
        <div className={`${comicStyles.messageBubble} ${comicStyles.messageAssistant} ${styles.richCard}`}>
          <div className={styles.graphHeader}>
            <div>
              <p className={styles.graphTitle}>{message.title}</p>
              <p className={styles.graphSummary}>{message.content}</p>
            </div>
            <span className={styles.graphBadge}>{message.badge ?? 'graph'}</span>
          </div>
          <KnowledgeGraphMessage graph={message.graph} />
        </div>
      );
    }

    if (message.kind === 'markdown') {
      return (
        <div className={`${comicStyles.messageBubble} ${comicStyles.messageAssistant} ${styles.richCard}`}>
          <MarkdownMessage title={message.title} content={message.content} />
        </div>
      );
    }

    if (message.kind === 'kline') {
      return (
        <div className={`${comicStyles.messageBubble} ${comicStyles.messageAssistant} ${styles.richCard}`}>
          <CandlestickChartMessage title={message.title} subtitle={message.subtitle} candles={message.candles} />
        </div>
      );
    }

    if (message.kind === 'data-viz') {
      return (
        <div className={`${comicStyles.messageBubble} ${comicStyles.messageAssistant} ${styles.richCard}`}>
          <DataVizMessage title={message.title} metrics={message.metrics} bars={message.bars} />
        </div>
      );
    }

    if (message.kind === 'matrix-terminal') {
      return (
        <div className={`${comicStyles.messageBubble} ${comicStyles.messageAssistant} ${styles.richCard}`}>
          <TradingMatrixMessage payload={message.payload} />
        </div>
      );
    }

    return (
      <div className={`${comicStyles.messageBubble} ${comicStyles.messageAssistant} ${styles.richCard}`}>
        <CodeBlockMessage
          title={message.title}
          status={message.status}
          language={message.language}
          code={message.code}
        />
      </div>
    );
  };

  return (
    <div className={comicStyles.comicOverlay}>
      <div className={comicStyles.comicContainer}>
        <button className={comicStyles.closeBtn} onClick={onClose} aria-label="Close">
          ×
        </button>

        <div className={comicStyles.comicViewport}>
          <div ref={scrollRef} className={`${comicStyles.comicScroll} ${styles.dialogueScroll}`}>
            {!hasMessages ? (
              <div className={comicStyles.emptyState}>
                <p className={comicStyles.emptyStateTitle}>OpenSucker 矩阵对话</p>
                <p className={comicStyles.emptyStateText}>
                  输入任何问题，实时对接后端 Agent，支持意图识别、风险检查、多节点推理。
                </p>
              </div>
            ) : (
              <div className={styles.thread}>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`${styles.threadRow} ${message.role === 'user' ? styles.threadRowUser : styles.threadRowAssistant}`}
                  >
                    {renderMessage(message)}
                  </div>
                ))}
                {isLoading && (
                  <div className={`${styles.threadRow} ${styles.threadRowAssistant}`}>
                    <div className={`${comicStyles.messageBubble} ${comicStyles.messageAssistant} ${styles.messageCard} ${styles.typingBubble}`}>
                      <span className={styles.typingDot}></span>
                      <span className={styles.typingDot}></span>
                      <span className={styles.typingDot}></span>
                      {stepLabel ? <span className={styles.stepLabelInline}>{stepLabel}</span> : null}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className={comicStyles.inputArea}>
          <div className={comicStyles.chatMeta}>
            <p className={comicStyles.chatTitle}>OpenSucker 矩阵对话</p>
            <p className={comicStyles.chatHint}>{statusText}</p>
          </div>
          <form onSubmit={(event) => void handleSubmit(event)} className={comicStyles.inputForm}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder="输入任何问题，对接 OpenSucker 矩阵后端..."
              className={comicStyles.comicInput}
            />
            <button type="submit" className={comicStyles.comicSubmitBtn} disabled={!input.trim() || isLoading}>
              {isLoading ? '生成中...' : '发送'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
