'use client';

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import PeepInstance from './PeepInstance';
import styles from '../page.module.css';
import {
  calculateCrowdLayout,
  buildCrowdSlots,
  CROWD_SETTINGS,
  Slot,
} from '../lib/peeps-middleware';

interface PeepsCrowdProps {
  isScattered?: boolean;
  isSelectable?: boolean;
  onPeepClick?: (peep: Slot) => void;
  transformedIds?: Set<string>;
  poisonedIds?: Set<string>;
  onSlotsCreated?: (slots: Slot[]) => void;
}

export default function PeepsCrowd({ isScattered, isSelectable, onPeepClick, transformedIds, poisonedIds, onSlotsCreated }: PeepsCrowdProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [scatterVectors, setScatterVectors] = useState<Record<string, { x: number; y: number }>>({});
  const [rowYJitters, setRowYJitters] = useState<number[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [layout, setLayout] = useState({
    scale: 1,
    numRows: 15,
    pw: CROWD_SETTINGS.PERSON_W,
    ph: CROWD_SETTINGS.PERSON_H,
    step: CROWD_SETTINGS.ROW_STEP,
    driftDuration: 40,
  });

  const measure = useCallback((el: HTMLDivElement) => {
    const newLayout = calculateCrowdLayout(el.offsetWidth, el.offsetHeight);
    setLayout(newLayout);

    const newSlots = buildCrowdSlots(newLayout.numRows, CROWD_SETTINGS.COLS_PER_ROW_BASE);
    setSlots(newSlots);

    // Freeze scatter vectors once — avoids re-randomizing on re-renders
    const vectors: Record<string, { x: number; y: number }> = {};
    newSlots.forEach(s => {
      const angle = Math.random() * Math.PI * 2;
      const dist  = 80 + Math.random() * 60;
      vectors[s.id] = { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist };
    });
    setScatterVectors(vectors);

    // Freeze row Y-jitter — prevents Math.random() running every render
    setRowYJitters(Array.from({ length: newLayout.numRows }, () => (Math.random() - 0.5) * 28));
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    measure(el);
    const ro = new ResizeObserver(() => measure(el));
    ro.observe(el);
    return () => ro.disconnect();
  }, [measure]);

  useEffect(() => {
    if (onSlotsCreated) {
      onSlotsCreated(slots);
    }
  }, [onSlotsCreated, slots]);

  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code !== 'Space') {
        return;
      }

      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName;
      const isEditable =
        target?.isContentEditable ||
        tagName === 'INPUT' ||
        tagName === 'TEXTAREA' ||
        tagName === 'BUTTON';

      if (isEditable) {
        return;
      }

      event.preventDefault();
      setIsPaused((current) => !current);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const { pw, ph, step, numRows, driftDuration } = layout;
  const slotMap = useMemo(() => new Map(slots.map((slot) => [slot.id, slot])), [slots]);

  // Memoize row grouping — only recomputes when slots change
  const rowData = useMemo(
    () => Array.from({ length: numRows }, (_, r) => slots.filter(s => s.row === r)),
    [slots, numRows]
  );

  const findSelectablePeep = useCallback((clientX: number, clientY: number) => {
    const container = ref.current;
    if (!container) {
      return null;
    }

    const peepNodes = container.querySelectorAll<HTMLElement>('[data-peep-id]');
    let bestMatch: { id: string; score: number } | null = null;

    peepNodes.forEach((node) => {
      const peepId = node.dataset.peepId;
      if (!peepId) {
        return;
      }

      const rect = node.getBoundingClientRect();
      if (!rect.width || !rect.height) {
        return;
      }

      const isPoisoned = poisonedIds?.has(peepId);
      const hitBoxScale = isPoisoned ? 0.8 : 0.34; // Larger hit area for poisoned
      const dx = (clientX - (rect.left + rect.width * 0.5)) / (rect.width * hitBoxScale);
      const dy = (clientY - (rect.top + rect.height * 0.37)) / (rect.height * hitBoxScale * 0.8);
      const score = dx * dx + dy * dy;

      if (score > 1) {
        return;
      }

      if (!bestMatch || score < bestMatch.score) {
        bestMatch = { id: peepId, score };
      }
    });

    const selectedMatch = bestMatch as { id: string; score: number } | null;

    if (!selectedMatch) {
      return null;
    }

    return slotMap.get(selectedMatch.id) ?? null;
  }, [slotMap]);

  const handleSelectionPointerDown = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    if (!onPeepClick || isScattered) {
      return;
    }

    const selectedSlot = findSelectablePeep(event.clientX, event.clientY);
    if (!selectedSlot) {
      return;
    }

    const canOpenSelection = isSelectable || poisonedIds?.has(selectedSlot.id);
    if (!canOpenSelection) {
      return;
    }

    event.preventDefault();
    onPeepClick(selectedSlot);
  }, [findSelectablePeep, isScattered, isSelectable, onPeepClick, poisonedIds]);

  return (
    <div
      ref={ref}
      onPointerDown={handleSelectionPointerDown}
      style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', background: '#fff' }}
    >
      {rowData.map((rowSlots, rIdx) => {
        if (rowSlots.length === 0) return null;

        // Use frozen jitter — no Math.random() in render path
        const y        = rIdx * step - ph * 0.4 + (rowYJitters[rIdx] ?? 0);
        const isReverse = rIdx % 2 === 1;

        const peeps = rowSlots.map(s => (
          <PeepInstance
            key={s.id}
            data={s}
            pw={pw}
            ph={ph}
            isPoisoned={poisonedIds?.has(s.id)}
            isScattered={isScattered}
            isSelectable={isSelectable}
            isPaused={isPaused}
            scatterVector={scatterVectors[s.id]}
            className={styles.peepWrapper}
            style={{
              marginRight: pw * s.horizontalJitter,
              paddingTop: `${s.verticalJitter}px`,
              filter: transformedIds?.has(s.id) ? 'hue-rotate(-30deg) saturate(1.7) brightness(0.95)' : undefined,
              zIndex: poisonedIds?.has(s.id) ? 25 : undefined,
              '--walk-duration': s.walkDuration,
              '--delay': s.delay,
            } as React.CSSProperties}
          />
        ));

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
              {peeps}
              {peeps.map((peep, index) => React.cloneElement(peep, { key: `${String(peep.key)}-clone-${index}` }))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
