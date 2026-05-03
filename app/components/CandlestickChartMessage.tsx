'use client';

import styles from './dialoguePage.module.css';
import type { KlineCandle } from '../lib/dialogue-types';

type CandlestickChartMessageProps = {
  title: string;
  subtitle: string;
  candles: KlineCandle[];
};

export default function CandlestickChartMessage({
  title,
  subtitle,
  candles,
}: CandlestickChartMessageProps) {
  const width = 720;
  const height = 300;
  const padding = { top: 22, right: 18, bottom: 36, left: 22 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const minPrice = Math.min(...candles.map((candle) => candle.low));
  const maxPrice = Math.max(...candles.map((candle) => candle.high));
  const priceRange = Math.max(maxPrice - minPrice, 1);
  const candleWidth = plotWidth / candles.length;

  const toY = (value: number) => padding.top + ((maxPrice - value) / priceRange) * plotHeight;

  return (
    <div className={styles.marketCard}>
      <div className={styles.marketHeader}>
        <div>
          <p className={styles.marketTitle}>{title}</p>
          <p className={styles.marketSubtitle}>{subtitle}</p>
        </div>
        <span className={styles.marketBadge}>live mock</span>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className={styles.marketSvg} role="img" aria-label={title}>
        {Array.from({ length: 5 }).map((_, index) => {
          const y = padding.top + (plotHeight / 4) * index;
          return <line key={`grid-${index}`} x1={padding.left} y1={y} x2={width - padding.right} y2={y} className={styles.marketGridLine} />;
        })}

        {candles.map((candle, index) => {
          const x = padding.left + candleWidth * index + candleWidth / 2;
          const openY = toY(candle.open);
          const closeY = toY(candle.close);
          const highY = toY(candle.high);
          const lowY = toY(candle.low);
          const bodyY = Math.min(openY, closeY);
          const bodyHeight = Math.max(Math.abs(closeY - openY), 3);
          const isUp = candle.close >= candle.open;

          return (
            <g key={candle.time}>
              <line
                x1={x}
                y1={highY}
                x2={x}
                y2={lowY}
                className={isUp ? styles.marketWickUp : styles.marketWickDown}
              />
              <rect
                x={x - candleWidth * 0.22}
                y={bodyY}
                width={candleWidth * 0.44}
                height={bodyHeight}
                rx={3}
                className={isUp ? styles.marketCandleUp : styles.marketCandleDown}
              />
              <text x={x} y={height - 12} className={styles.marketAxisLabel}>
                {candle.time}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
