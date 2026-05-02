'use client';

import React, { useMemo, useState, useEffect, useRef } from 'react';
import type { PeepConfig } from '../lib/peeps-middleware';
import { CROWD_SETTINGS } from '../lib/peeps-middleware';
import styles from './comicPage.module.css';
import { getCharacterById } from '../lib/character-store';
import { LeekPersona } from '../lib/leek-lore';
import { Peep } from '../lib/react-peeps';

interface ComicPageProps {
  peep: PeepConfig & { persona?: LeekPersona };
  onClose: () => void;
}

const STAGE_WIDTH = 722.2412719726562;
const STAGE_HEIGHT = 748;

type PanelClassName =
  | 'panelTopLeft'
  | 'panelTopMiddle'
  | 'panelTopRight'
  | 'panelMiddleLeft'
  | 'panelMiddleCenter'
  | 'panelMiddleRight'
  | 'panelBottomLeft'
  | 'panelBottomMiddle'
  | 'panelBottomRight'
  | 'panelFooterLeft'
  | 'panelFooterCenter'
  | 'panelFooterRight';

type PanelTemplate = {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  className: PanelClassName;
};

type CharacterPlacement = {
  key: string;
  peep: PeepConfig;
  x: number;
  y: number;
  width: number;
  height: number;
  fillColor?: string;
  mirror?: boolean;
  rotation?: number;
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

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};

const PANEL_TEMPLATES: PanelTemplate[] = [
  { id: '1', x: 0, y: 37, width: 261, height: 178, className: 'panelTopLeft' },
  { id: '2', x: 207, y: 37, width: 281, height: 187, className: 'panelTopMiddle' },
  { id: '3', x: 476, y: 37, width: 235, height: 194, className: 'panelTopRight' },
  { id: '4', x: 0, y: 217, width: 248, height: 220, className: 'panelMiddleLeft' },
  { id: '4c', x: 256, y: 216, width: 184, height: 221, className: 'panelMiddleCenter' },
  { id: '5', x: 448, y: 223, width: 263, height: 205, className: 'panelMiddleRight' },
  { id: '6', x: 0, y: 435, width: 257, height: 166, className: 'panelBottomLeft' },
  { id: '7', x: 235, y: 421, width: 285, height: 180, className: 'panelBottomMiddle' },
  { id: '8', x: 501, y: 412, width: 210, height: 188, className: 'panelBottomRight' },
  { id: '9', x: 0, y: 609, width: 214, height: 139, className: 'panelFooterLeft' },
  { id: '9c', x: 223, y: 606, width: 150, height: 142, className: 'panelFooterCenter' },
  { id: '10', x: 381, y: 609, width: 330, height: 139, className: 'panelFooterRight' },
];

const CHARACTER_PANEL_IDS = new Set(['4c', '9c']);

function buildPlacements(peep: PeepConfig) {
  return new Map(
    PANEL_TEMPLATES.filter((panel) => CHARACTER_PANEL_IDS.has(panel.id)).map((panel) => {
      const isLowerEvenRow = panel.id === '9c';
      const width = panel.width * (panel.height > 180 ? 1.08 : 0.94);
      const height = panel.height * (panel.height > 180 ? 1.18 : 1.12);
      const x = panel.width * (isLowerEvenRow ? -0.06 : -0.04);
      const y = panel.height * (panel.height > 180 ? -0.08 : -0.06);

      return [
        panel.id,
        [
          {
            key: 'main',
            peep,
            x,
            y,
            width,
            height,
            fillColor: '#ffffff',
            mirror: isLowerEvenRow,
          },
        ],
      ] satisfies [string, CharacterPlacement[]];
    })
  );
}

function compactPanelText(text: string): string {
  const compacted = text
    .replace(/^第\d+页[^：:]*[：:]\s*/u, '')
    .replace(/针对这位[^，。]+[，,]开始他在市场中的第一章故事[。.]?/gu, '')
    .replace(/\s+/g, ' ')
    .trim();

  return compacted || text.trim();
}

function getPanelDisplayText(panelId: string, pagePanels: Map<string, StoryPanel>): string | null {
  if (CHARACTER_PANEL_IDS.has(panelId)) {
    return null;
  }

  const parts = [panelId]
    .map((sourceId) => pagePanels.get(sourceId))
    .filter((panel): panel is StoryPanel => Boolean(panel?.text))
    .map((panel) => compactPanelText(panel.text));

  if (parts.length === 0) {
    return null;
  }

  return parts.join('\n\n');
}

function toStageStyle(panel: PanelTemplate): React.CSSProperties {
  return {
    left: `${(panel.x / STAGE_WIDTH) * 100}%`,
    top: `${(panel.y / STAGE_HEIGHT) * 100}%`,
    width: `${(panel.width / STAGE_WIDTH) * 100}%`,
    height: `${(panel.height / STAGE_HEIGHT) * 100}%`,
  };
}

function toPlacementStyle(placement: CharacterPlacement): React.CSSProperties {
  return {
    left: placement.x,
    top: placement.y,
    width: placement.width,
    height: placement.height,
    transform: `${placement.mirror ? 'scaleX(-1) ' : ''}${placement.rotation ? `rotate(${placement.rotation}deg)` : ''}`.trim() || undefined,
    transformOrigin: 'center center',
  };
}

function ComicPeep({ placement }: { placement: CharacterPlacement }) {
  return (
    <div className={styles.peepPlacement} style={toPlacementStyle(placement)}>
      <Peep
        style={{ width: '100%', height: '100%', display: 'block' }}
        hair={placement.peep.hair}
        body={placement.peep.body}
        face={placement.peep.face}
        facialHair={placement.peep.facialHair}
        accessory={placement.peep.accessory}
        strokeColor="#000000"
        backgroundColor={placement.fillColor ?? placement.peep.styles.backgroundColor}
        viewBox={CROWD_SETTINGS.VIEWBOX}
      />
    </div>
  );
}

export default function ComicPage({ peep, onClose }: ComicPageProps) {
  const [input, setInput] = useState('');
  const [story, setStory] = useState<StoryResponse>({
    reply: '正在为你构思专属的散户漫画...',
    pages: [],
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const persona = useMemo<LeekPersona | null>(() => getCharacterById(peep.id)?.persona || peep.persona || null, [peep.id, peep.persona]);
  const panelPlacements = useMemo(() => buildPlacements(peep), [peep]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    textarea.style.height = '0px';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [input]);

  const handleTrigger = async (prompt: string, currentMessages: ChatMessage[]) => {
    setIsLoading(true);
    setError(null);

    const nextMessages: ChatMessage[] = [...currentMessages, { role: 'user', content: prompt }];
    setMessages(nextMessages);

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          peep, 
          messages: nextMessages, 
          currentStory: story.pages.length ? story : undefined,
          persona: persona 
        }),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error('Failed to generate story');

      const data = (await response.json()) as StoryResponse;
      setStory(data);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }]);
    } catch (err) {
      console.error('Trigger failed', err);
      setError(err instanceof DOMException && err.name === 'AbortError'
        ? '请求超过 5 秒，已跳过这次生成。请修改一句更短的追问后重试。'
        : '故事创作暂时中断了，请尝试手动输入追问。');
    } finally {
      window.clearTimeout(timeoutId);
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    const prompt = input.trim();
    setInput('');
    handleTrigger(prompt, messages);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
      return;
    }

    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSubmit(e as unknown as React.FormEvent);
    }
  };

  const hasStory = story.pages.length > 0;

  return (
    <div className={styles.comicOverlay}>
      <div className={styles.comicContainer}>
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close">
          ×
        </button>
        <div className={styles.comicViewport}>
          <div className={styles.comicScroll}>
            {!hasStory && isLoading && !error && (
              <div className={styles.loadingContainer}>
                <div className={styles.loadingSpinner}></div>
                <p className={styles.loadingText}>正在构思专属漫画...</p>
              </div>
            )}

            {!hasStory && !isLoading && (
              <div className={styles.emptyState}>
                <p className={styles.emptyStateTitle}>从你的第一句追问开始</p>
                <p className={styles.emptyStateText}>
                  不会自动帮你填词，也不会自动发请求。输入一句你真正想问的话，漫画再开始往下生成。
                </p>
              </div>
            )}

            {story.pages.map((page) => {
              const pagePanels = new Map(page.panels.map((p) => [p.panelId, p]));
              return (
                <section key={page.id} className={styles.comicStage} aria-label={page.summary}>
                  <div className={styles.comicPageSummary}>
                    <span className={styles.pageBadge}>PAGE {page.id.split('-').pop()}</span>
                    {page.summary}
                  </div>
                  <div className={styles.comicContent}>
                    {PANEL_TEMPLATES.map((panel) => {
                      const storyPanel = pagePanels.get(panel.id);
                      const isDark = storyPanel?.dark ?? (panel.id === '2' || panel.id === '7');
                      const displayText = getPanelDisplayText(panel.id, pagePanels);
                      return (
                        <div
                          key={`${page.id}-${panel.id}`}
                          className={`${styles.panel} ${styles[panel.className]}`}
                          style={toStageStyle(panel)}
                        >
                          <div className={`${styles.panelInner} ${isDark ? styles.panelDark : ''}`}>
                            {displayText && (
                              isDark ? (
                                <div className={styles.darkPanelCopy}>
                                  <p className={styles.darkPanelText}>{displayText}</p>
                                </div>
                              ) : (
                                <div className={styles.panelCopyFull}>
                                  <div className={`${styles.speechBubble} ${styles.bubbleLight}`}>
                                    <p className={styles.speechBubbleText}>{displayText}</p>
                                  </div>
                                </div>
                              )
                            )}
                            {!isDark && (panelPlacements.get(panel.id) ?? []).map((placement) => (
                              <ComicPeep key={`${page.id}-${placement.key}`} placement={placement} />
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        </div>
        <div className={styles.inputArea}>
          <div className={styles.chatMeta}>
            <p className={styles.chatTitle}>{hasStory ? '继续追问这名散户的经历' : '输入第一句，开始这名散户的经历'}</p>
            <p className={styles.chatHint}>
              {hasStory ? '输入新的问题后，分镜会按返回的故事数据继续向下延长。' : '例如从追涨、补仓、爆仓、回本执念里选一个切口，先问第一句。'}
            </p>
            {messages.length > 0 && (
              <div className={styles.messageList}>
                {messages.slice(-4).map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={`${styles.messageBubble} ${message.role === 'user' ? styles.messageUser : styles.messageAssistant}`}
                  >
                    {message.content}
                  </div>
                ))}
              </div>
            )}
            {error ? <p className={styles.errorText}>{error}</p> : null}
          </div>
          <form onSubmit={handleSubmit} className={styles.inputForm}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              placeholder={hasStory ? '继续追问一个更具体的细节...' : '例如：他是怎么从追涨走到爆仓的？'}
              className={styles.comicInput}
            />
            <button type="submit" className={styles.comicSubmitBtn} disabled={!input.trim() || isLoading}>
              {isLoading ? '生成中...' : '发送'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
