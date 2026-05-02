'use client';

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { Slot, calculateCrowdLayout, buildCrowdSlots, CROWD_SETTINGS } from './peeps-middleware';

interface CrowdContextType {
  slots: Slot[];
  layout: any;
  scatterVectors: Record<string, { x: number; y: number }>;
  rowYJitters: number[];
  isInitialized: boolean;
  initialize: (width: number, height: number) => void;
}

const CrowdContext = createContext<CrowdContextType | null>(null);

export function CrowdProvider({ children }: { children: React.ReactNode }) {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [layout, setLayout] = useState<any>(null);
  const [scatterVectors, setScatterVectors] = useState<Record<string, { x: number; y: number }>>({});
  const [rowYJitters, setRowYJitters] = useState<number[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Track previous dimensions to avoid re-calculating on tiny changes
  const lastDimensions = useRef({ width: 0, height: 0 });

  const initialize = useCallback((width: number, height: number) => {
    // Prevent unnecessary re-initialization if dimensions are similar
    if (
      isInitialized && 
      Math.abs(lastDimensions.current.width - width) < 50 && 
      Math.abs(lastDimensions.current.height - height) < 50
    ) {
      return;
    }

    lastDimensions.current = { width, height };
    
    const newLayout = calculateCrowdLayout(width, height);
    const newSlots = buildCrowdSlots(newLayout.numRows, CROWD_SETTINGS.COLS_PER_ROW_BASE);
    
    const vectors: Record<string, { x: number; y: number }> = {};
    newSlots.forEach(s => {
      const angle = Math.random() * Math.PI * 2;
      const dist  = 80 + Math.random() * 60;
      vectors[s.id] = { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist };
    });

    const jitters = Array.from({ length: newLayout.numRows }, () => (Math.random() - 0.5) * 28);

    setLayout(newLayout);
    setSlots(newSlots);
    setScatterVectors(vectors);
    setRowYJitters(jitters);
    setIsInitialized(true);
  }, [isInitialized]);

  return (
    <CrowdContext.Provider value={{
      slots,
      layout,
      scatterVectors,
      rowYJitters,
      isInitialized,
      initialize
    }}>
      {children}
    </CrowdContext.Provider>
  );
}

export function useCrowd() {
  const context = useContext(CrowdContext);
  if (!context) {
    throw new Error('useCrowd must be used within a CrowdProvider');
  }
  return context;
}
