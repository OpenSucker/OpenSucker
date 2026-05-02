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
import { requestOpenAIStyleChatCompletion } from '../lib/openai-chat-middleware';

interface DialoguePageProps {
  onClose: () => void;
}

function createId(prefix: string) {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export default function DialoguePage({ onClose }: DialoguePageProps) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<DialogueMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

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
  }, [messages, isLoading]);

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

    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setIsLoading(true);

    try {
      const completion = await requestOpenAIStyleChatCompletion('/api/dialogue', {
        model: 'mock-dialogue-model',
        messages: nextMessages.map((message) => ({
          role: message.role,
          content: message.kind === 'text' ? message.content : message.kind,
        })),
      });

      const components = completion.choices[0]?.message.components ?? [];
      setMessages((prev) => [...prev, ...components]);
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
      return '正在通过 OpenAI 风格接口装配结构化回复...';
    }

    if (!hasMessages) {
      return '支持 Markdown、知识图谱、K 线图、数据可视化、代码块和交易终端卡片。';
    }

    return '继续输入关键词可以触发不同卡片，也方便后续直接切换真实 API 返回。';
  }, [hasMessages, isLoading]);

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
                <p className={comicStyles.emptyStateTitle}>新的结构化对话页已经就绪</p>
                <p className={comicStyles.emptyStateText}>
                  输入“知识图谱”会优先加载 public 下的画像图谱文件，输入“TSLA 压力测试”可以触发 K 线与回测卡片，输入“矩阵”或“交易终端”可以渲染新的终端大卡片。
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
                    <div className={`${comicStyles.messageBubble} ${comicStyles.messageAssistant} ${styles.messageCard}`}>
                      <span className={styles.typingDot}></span>
                      <span className={styles.typingDot}></span>
                      <span className={styles.typingDot}></span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className={comicStyles.inputArea}>
          <div className={comicStyles.chatMeta}>
            <p className={comicStyles.chatTitle}>结构化对话页</p>
            <p className={comicStyles.chatHint}>{statusText}</p>
          </div>
          <form onSubmit={(event) => void handleSubmit(event)} className={comicStyles.inputForm}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder="例如：知识图谱、TSLA 压力测试、矩阵、交易终端"
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
