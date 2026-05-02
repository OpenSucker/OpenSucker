'use client';

import styles from './dialoguePage.module.css';
import type { MatrixInsightCard, MatrixTerminalPayload } from '../lib/dialogue-types';

type TradingMatrixMessageProps = {
  payload: MatrixTerminalPayload;
};

function toneClass(tone: MatrixInsightCard['tone']) {
  if (tone === 'green') return styles.matrixInsightGreen;
  if (tone === 'yellow') return styles.matrixInsightYellow;
  return styles.matrixInsightBlue;
}

export default function TradingMatrixMessage({ payload }: TradingMatrixMessageProps) {
  return (
    <div className={styles.matrixShell}>
      <div className={styles.matrixTopbar}>
        <div className={styles.matrixBrand}>
          <span className={styles.matrixBrandMain}>{payload.title}</span>
          <span className={styles.matrixBrandSub}>{payload.version}</span>
        </div>
        <div className={styles.matrixSync}>SYNC: {payload.sync}</div>
      </div>

      <div className={styles.matrixGridLayout}>
        <aside className={styles.matrixSidebar}>
          <section className={styles.matrixPanel}>
            <p className={styles.matrixPanelTitle}>交易员画像</p>
            <div className={styles.matrixProfileList}>
              {payload.profile.map((item) => (
                <div key={item.label} className={styles.matrixProfileRow}>
                  <span className={styles.matrixProfileLabel}>{item.label}</span>
                  <span className={`${styles.matrixProfileValue} ${styles[`matrixProfile${item.tone[0].toUpperCase()}${item.tone.slice(1)}`]}`}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </section>

          <section className={styles.matrixPanel}>
            <p className={styles.matrixPanelTitle}>20 格专家矩阵</p>
            <div className={styles.matrixLayers}>
              {payload.layers.map((layer) => (
                <div key={layer.label} className={styles.matrixLayer}>
                  <span className={styles.matrixLayerLabel}>{layer.label}</span>
                  <div className={styles.matrixCells}>
                    {layer.cells.map((cell) => (
                      <span
                        key={cell.id}
                        className={`${styles.matrixCell} ${cell.active ? styles.matrixCellActive : ''}`}
                      >
                        {cell.id}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className={styles.matrixPanel}>
            <p className={styles.matrixPanelTitle}>活跃任务链</p>
            <div className={styles.matrixActiveChain}>{payload.activeChain}</div>
          </section>
        </aside>

        <main className={styles.matrixCenter}>
          <div className={styles.matrixConversation}>
            <div className={`${styles.matrixBubble} ${styles.matrixBubbleAssistant}`}>
              <p className={styles.matrixBubbleMeta}>S SUCKER_MATRIX</p>
              <p className={styles.matrixBubbleText}>{payload.assistantGreeting}</p>
            </div>

            <div className={`${styles.matrixBubble} ${styles.matrixBubbleUser}`}>
              <p className={styles.matrixBubbleMeta}>YOU</p>
              <p className={styles.matrixBubbleText}>{payload.userPrompt}</p>
            </div>

            <div className={`${styles.matrixBubble} ${styles.matrixBubbleAssistant}`}>
              <div className={styles.matrixAssistantHeader}>
                <p className={styles.matrixBubbleMeta}>S SUCKER_MATRIX</p>
                <span className={styles.matrixAssistantTag}>{payload.assistantTag}</span>
              </div>
              <p className={styles.matrixBubbleText}>{payload.assistantSummary}</p>
            </div>
          </div>

          <div className={styles.matrixToolList}>
            {payload.toolRuns.map((toolRun) => (
              <div key={toolRun.name} className={styles.matrixToolCard}>
                <div className={styles.matrixToolHeader}>
                  <span>{toolRun.name}</span>
                  <span>{toolRun.status}</span>
                </div>
                <div className={styles.matrixToolSection}>
                  <p className={styles.matrixToolLabel}>ARGS</p>
                  <pre className={styles.matrixToolCode}>{toolRun.args}</pre>
                </div>
                <div className={styles.matrixToolSection}>
                  <p className={styles.matrixToolLabel}>RESULT</p>
                  <pre className={styles.matrixToolCode}>{toolRun.result}</pre>
                </div>
              </div>
            ))}
          </div>
        </main>

        <aside className={styles.matrixRightbar}>
          {payload.insights.map((insight) => (
            <section key={insight.title} className={`${styles.matrixInsightCard} ${toneClass(insight.tone)}`}>
              <p className={styles.matrixInsightTitle}>{insight.title}</p>
              <p className={styles.matrixInsightValue}>{insight.value}</p>
              <p className={styles.matrixInsightDetail}>{insight.detail}</p>
            </section>
          ))}
        </aside>
      </div>
    </div>
  );
}
