'use client';

import { useEffect, useRef, useState } from 'react';
import styles from './PoisoningModal.module.css';

const PLATFORMS = [
  { id: 'x',      name: 'X (Twitter)',  desc: '推文扩散' },
  { id: 'reddit', name: 'Reddit',        desc: '社区讨论' },
  { id: 'medium', name: 'Medium',        desc: '长文发布' },
  { id: 'google', name: 'Google 索引',   desc: '搜索渗透' },
] as const;

type PlatformId = (typeof PLATFORMS)[number]['id'];
type Phase = 'form' | 'publishing' | 'done';

interface AgentResult {
  status: 'completed' | 'needs_input' | 'error';
  output?: string;
  reason?: string;
  screenshot?: string;
}

interface Props {
  isOpen: boolean;
  targetName?: string;
  onClose: () => void;
}

export default function PoisoningModal({ isOpen, targetName, onClose }: Props) {
  const [platform, setPlatform] = useState<PlatformId>('x');
  const [news, setNews] = useState('');
  const [phase, setPhase] = useState<Phase>('form');
  const [agentResult, setAgentResult] = useState<AgentResult | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (phase !== 'publishing') return;

    const controller = new AbortController();
    abortRef.current = controller;
    setAgentResult(null);

    fetch('/api/poisoning', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ platform, news }),
      signal: controller.signal,
    })
      .then((r) => r.json())
      .then((data: AgentResult) => {
        setAgentResult(data);
        setPhase('done');
      })
      .catch((e: Error) => {
        if (e.name !== 'AbortError') {
          setAgentResult({ status: 'error', output: e.message });
          setPhase('done');
        }
      });

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (!isOpen) abortRef.current?.abort();
  }, [isOpen]);

  const handleReset = () => {
    setPhase('form');
    setAgentResult(null);
  };

  if (!isOpen) return null;

  const title = targetName ? `对准机构: ${targetName}` : '发布工作流';
  const currentPlatform = PLATFORMS.find((p) => p.id === platform);

  return (
    <div className={styles.overlay} onClick={onClose} role="presentation">
      <div className={styles.panel} onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true">
        <div className={styles.header}>
          <div>
            <div className={styles.eyebrow}>
              <span className={styles.pulse}>●</span> NEOFISH AGENT
            </div>
            <h2 className={styles.title}>{title}</h2>
          </div>
          <button type="button" onClick={onClose} className={styles.closeButton}>×</button>
        </div>

        <div className={styles.body}>
          {phase === 'form' && (
            <div className={styles.stepContent}>
              <label className={styles.inputLabel}>选择发布平台</label>
              <div className={styles.grid} style={{ marginBottom: 24 }}>
                {PLATFORMS.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className={`${styles.card} ${platform === p.id ? styles.active : ''}`}
                    onClick={() => setPlatform(p.id)}
                  >
                    <div className={styles.cardName}>{p.name}</div>
                    <div className={styles.cardMeta}>{p.desc}</div>
                  </button>
                ))}
              </div>

              <label className={styles.inputLabel}>新闻原文</label>
              <textarea
                className={styles.contentInput}
                value={news}
                onChange={(e) => setNews(e.target.value)}
                placeholder="粘贴新闻原文，Agent 会自动总结后发布..."
                rows={6}
              />

              <div className={styles.footer}>
                <button
                  type="button"
                  className={styles.primaryButton}
                  disabled={!news.trim()}
                  onClick={() => setPhase('publishing')}
                >
                  发布
                </button>
              </div>
            </div>
          )}

          {phase === 'publishing' && (
            <div className={styles.stepContent}>
              <div className={styles.stepHeader}>
                <div className={styles.stepNumber}>运行中</div>
                <div className={styles.stepTitle}>Agent 正在执行...</div>
              </div>
              <div className={styles.logContainer} style={{ maxHeight: 80 }}>
                <div className={styles.logRow}>
                  <span className={styles.logTime}>[--:--]</span>
                  <span className={styles.logText}>
                    NeoFish 代理已启动，正在连接 {currentPlatform?.name}...
                  </span>
                </div>
              </div>
              <div className={styles.footer}>
                <button type="button" className={styles.ghostButton} onClick={onClose}>取消</button>
              </div>
            </div>
          )}

          {phase === 'done' && agentResult && (
            <div className={styles.stepContent}>
              <div className={styles.agentResult}>
                <div className={styles.agentResultHeader}>
                  <span className={styles.agentResultBadge} data-status={agentResult.status}>
                    NEOFISH · {agentResult.status === 'completed' ? '完成' : agentResult.status === 'needs_input' ? '需要人工操作' : '失败'}
                  </span>
                </div>
                {agentResult.status === 'needs_input' && agentResult.screenshot && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={`data:image/jpeg;base64,${agentResult.screenshot}`}
                    alt="截图"
                    style={{ width: '100%', borderBottom: '2px solid #000' }}
                  />
                )}
                <pre className={styles.agentResultBody}>
                  {agentResult.output ?? agentResult.reason ?? '无输出'}
                </pre>
              </div>
              <div className={styles.footer}>
                <button type="button" className={styles.ghostButton} onClick={handleReset}>再发一条</button>
                <button type="button" className={styles.primaryButton} onClick={onClose}>关闭</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
