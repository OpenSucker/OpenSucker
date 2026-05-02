'use client';

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import PeepInstance from './PeepInstance';
import styles from '../page.module.css';
import { useCrowd } from '../lib/crowd-context';
import { Slot } from '../lib/peeps-middleware';

interface PeepsCrowdProps {
  isScattered?: boolean;
  isSelectable?: boolean;
  onPeepClick?: (peep: Slot) => void;
  transformedIds?: Set<string>;
  onSlotsCreated?: (slots: Slot[]) => void;
}

export default function PeepsCrowd({ 
  isScattered, 
  isSelectable, 
  onPeepClick, 
  transformedIds = new Set(),
  onSlotsCreated
}: PeepsCrowdProps) {
  const ref = useRef<HTMLDivElement>(null);
  const { slots, layout, scatterVectors, rowYJitters, isInitialized, initialize } = useCrowd();
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    // Initial measure
    initialize(el.offsetWidth, el.offsetHeight);

    // Throttled ResizeObserver
    let timeout: NodeJS.Timeout;
    const ro = new ResizeObserver((entries) => {
      if (timeout) clearTimeout(timeout);
      timeout = setTimeout(() => {
        const entry = entries[0];
        if (entry) {
          initialize(entry.contentRect.width, entry.contentRect.height);
        }
      }, 200); // 200ms throttle
    });

    ro.observe(el);
    return () => {
      ro.disconnect();
      if (timeout) clearTimeout(timeout);
    };
  }, [initialize]);

  // Sync slots to parent if needed
  useEffect(() => {
    if (isInitialized && onSlotsCreated) {
      onSlotsCreated(slots);
    }
  }, [isInitialized, slots, onSlotsCreated]);

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code !== 'Space') return;
      const target = event.target as HTMLElement | null;
      if (target?.isContentEditable || ['INPUT', 'TEXTAREA', 'BUTTON'].includes(target?.tagName || '')) return;
      event.preventDefault();
      setIsPaused((current) => !current);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const slotMap = useMemo(() => new Map(slots.map((slot) => [slot.id, slot])), [slots]);

  const rowData = useMemo(() => {
    if (!layout) return [];
    const rows = Array.from({ length: layout.numRows }, () => [] as Slot[]);
    slots.forEach(s => {
      if (s.row < rows.length) rows[s.row].push(s);
    });
    return rows;
  }, [slots, layout]);

  const findSelectablePeep = useCallback((clientX: number, clientY: number) => {
    const container = ref.current;
    if (!container) return null;

    const peepNodes = container.querySelectorAll<HTMLElement>('[data-peep-id]');
    let bestMatch: { id: string; score: number } | null = null;

    peepNodes.forEach((node) => {
      const peepId = node.dataset.peepId;
      if (!peepId) return;

      const rect = node.getBoundingClientRect();
      if (!rect.width || !rect.height) return;

      const dx = (clientX - (rect.left + rect.width * 0.5)) / (rect.width * 0.34);
      const dy = (clientY - (rect.top + rect.height * 0.37)) / (rect.height * 0.28);
      const score = dx * dx + dy * dy;

      if (score > 1) return;
      if (!bestMatch || score < bestMatch.score) {
        bestMatch = { id: peepId, score };
      }
    });

    return bestMatch ? slotMap.get(bestMatch.id) ?? null : null;
  }, [slotMap]);

  const handleSelectionPointerDown = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    if (!isSelectable || !onPeepClick || isScattered) return;
    const selectedSlot = findSelectablePeep(event.clientX, event.clientY);
    if (!selectedSlot) return;
    event.preventDefault();
    onPeepClick(selectedSlot);
  }, [findSelectablePeep, isScattered, isSelectable, onPeepClick]);

  if (!isInitialized || !layout) {
    return <div ref={ref} style={{ width: '100%', height: '100%', background: '#fff' }} />;
  }

  const { pw, ph, step, driftDuration } = layout;

  return (
    <div
      ref={ref}
      onPointerDown={handleSelectionPointerDown}
      style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', background: '#fff' }}
    >
      {rowData.map((rowSlots, rIdx) => {
        if (rowSlots.length === 0) return null;

        const y = rIdx * step - ph * 0.4 + (rowYJitters[rIdx] ?? 0);
        const isReverse = rIdx % 2 === 1;

        return (
          <div
            key={rIdx}
            className={styles.rowContainer}
            style={{ top: y, zIndex: rIdx }}
          >
            <div
              className={isReverse ? styles.rowInnerReverse : styles.rowInner}
              style={{
                '--drift-duration': `${driftDuration}s`,
                animationPlayState: isPaused ? 'paused' : 'running',
              } as React.CSSProperties}
            >
              {rowSlots.map(s => (
                <PeepInstance
                  key={s.id}
                  data={s}
                  pw={pw}
                  ph={ph}
                  isScattered={isScattered}
                  isSelectable={isSelectable}
                  isPaused={isPaused}
                  isRed={transformedIds.has(s.id)}
                  scatterVector={scatterVectors[s.id]}
                  className={styles.peepWrapper}
                  style={{
                    marginRight: pw * s.horizontalJitter,
                    paddingTop: `${s.verticalJitter}px`,
                    '--walk-duration': s.walkDuration,
                    '--delay': s.delay,
                  } as React.CSSProperties}
                />
              ))}
              {/* Clones */}
              {rowSlots.map((s, idx) => (
                <PeepInstance
                  key={`${s.id}-clone-${idx}`}
                  data={s}
                  pw={pw}
                  ph={ph}
                  isScattered={isScattered}
                  isSelectable={isSelectable}
                  isPaused={isPaused}
                  isRed={transformedIds.has(s.id)}
                  scatterVector={scatterVectors[s.id]}
                  className={styles.peepWrapper}
                  style={{
                    marginRight: pw * s.horizontalJitter,
                    paddingTop: `${s.verticalJitter}px`,
                    '--walk-duration': s.walkDuration,
                    '--delay': s.delay,
                  } as React.CSSProperties}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
