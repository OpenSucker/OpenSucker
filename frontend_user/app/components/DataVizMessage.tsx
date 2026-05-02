'use client';

import styles from './dialoguePage.module.css';
import type { DistributionBar, MetricCard } from '../lib/dialogue-types';

type DataVizMessageProps = {
  title: string;
  metrics: MetricCard[];
  bars: DistributionBar[];
};

function metricToneClass(tone: MetricCard['tone']) {
  if (tone === 'green') return styles.metricToneGreen;
  if (tone === 'yellow') return styles.metricToneYellow;
  if (tone === 'red') return styles.metricToneRed;
  return styles.metricToneBlue;
}

export default function DataVizMessage({ title, metrics, bars }: DataVizMessageProps) {
  const maxBarValue = Math.max(...bars.map((bar) => bar.value), 1);

  return (
    <div className={styles.dashboardCard}>
      <p className={styles.richMessageTitle}>{title}</p>

      <div className={styles.metricGrid}>
        {metrics.map((metric) => (
          <div key={metric.label} className={`${styles.metricCard} ${metricToneClass(metric.tone)}`}>
            <p className={styles.metricLabel}>{metric.label}</p>
            <p className={styles.metricValue}>{metric.value}</p>
            <p className={styles.metricDetail}>{metric.detail}</p>
          </div>
        ))}
      </div>

      <div className={styles.barSection}>
        {bars.map((bar) => (
          <div key={bar.label} className={styles.barRow}>
            <div className={styles.barMeta}>
              <span>{bar.label}</span>
              <span>{bar.value}</span>
            </div>
            <div className={styles.barTrack}>
              <div
                className={styles.barFill}
                style={{ width: `${(bar.value / maxBarValue) * 100}%`, background: bar.color }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
