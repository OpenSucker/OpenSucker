'use client';

import React, { useState, useRef, useEffect } from 'react';
import styles from './peepInputPanel.module.css';

interface PeepInputPanelProps {
  peepId: string;
  onSubmit: (value: string) => void;
  onClose: () => void;
}

export default function PeepInputPanel({ peepId, onSubmit, onClose }: PeepInputPanelProps) {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <span className={styles.label}>Character ID</span>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>
        <div className={styles.peepId}>{peepId}</div>
        <form onSubmit={handleSubmit} className={styles.form}>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的名字..."
            className={styles.input}
          />
          <button type="submit" className={styles.submitBtn} disabled={!input.trim()}>
            确认
          </button>
        </form>
      </div>
    </div>
  );
}