'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import ComicPage from './components/ComicPage';
import DialoguePage from './components/DialoguePage';
import PeepsCrowd from './components/PeepsCrowd';
import PeepsCard from './components/PeepsCard';
import OnboardingFlow from './components/OnboardingFlow';
import LanguageSwitcher from './components/LanguageSwitcher';
import type { Slot } from './lib/peeps-middleware';
import styles from './page.module.css';
import { useI18n } from './lib/i18n-context';

export default function Home() {
  const { t } = useI18n();
  const [isScattered, setIsScattered] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
  const [selectedPeep, setSelectedPeep] = useState<Slot | null>(null);
  const [isInteractionReady, setIsInteractionReady] = useState(false);
  const [quoteIndex, setQuoteIndex] = useState(0);
  const [transformedIds, setTransformedIds] = useState<Set<string>>(new Set());
  const [availableSlots, setAvailableSlots] = useState<Slot[]>([]);
  const [isBurning, setIsBurning] = useState(false);
  const [showDialoguePage, setShowDialoguePage] = useState(false);
  const [showSelectionHint, setShowSelectionHint] = useState(false);
  const hasCompletedOnboardingRef = useRef(false);
  const isSelectionMode = hasCompletedOnboarding && !showOnboarding;

  useEffect(() => {
    const readyTimer = setTimeout(() => {
      setIsInteractionReady(true);
    }, 5000);
    return () => clearTimeout(readyTimer);
  }, []);

  useEffect(() => {
    const quoteInterval = setInterval(() => {
      if (!hasCompletedOnboardingRef.current) {
        setQuoteIndex((prev) => (prev + 1) % t.quotes.length);
      }
    }, 5000);

    const burnTimeout = setTimeout(() => {
      if (!hasCompletedOnboardingRef.current) {
        setIsBurning(true);
      }
    }, 5000);

    let peepsInterval: NodeJS.Timeout;
    const startPeepsRed = setTimeout(() => {
      peepsInterval = setInterval(() => {
        if (hasCompletedOnboardingRef.current) {
          return;
        }

        setTransformedIds((prev) => {
          if (availableSlots.length === 0) {
            return prev;
          }

          const next = new Set(prev);
          const remaining = availableSlots.filter((slot) => !next.has(slot.id));
          if (remaining.length === 0) {
            return prev;
          }

          const countToChange = Math.min(remaining.length, Math.floor(Math.random() * 3) + 1);
          for (let index = 0; index < countToChange; index += 1) {
            const selectedIndex = Math.floor(Math.random() * remaining.length);
            next.add(remaining[selectedIndex].id);
            remaining.splice(selectedIndex, 1);
          }

          return next;
        });
      }, 2000);
    }, 5000);

    return () => {
      clearInterval(quoteInterval);
      clearTimeout(burnTimeout);
      clearTimeout(startPeepsRed);
      if (peepsInterval) {
        clearInterval(peepsInterval);
      }
    };
  }, [availableSlots, t.quotes.length]);

  useEffect(() => {
    if (!isSelectionMode || selectedPeep) {
      setShowSelectionHint(false);
      return;
    }

    setShowSelectionHint(true);
    const timer = window.setTimeout(() => {
      setShowSelectionHint(false);
    }, 10000);

    return () => window.clearTimeout(timer);
  }, [isSelectionMode, selectedPeep]);

  const handlePeepClick = useCallback((peep: Slot) => {
    setSelectedPeep(peep);
  }, []);

  const handleSlotsCreated = useCallback((slots: Slot[]) => {
    setAvailableSlots(slots);
  }, []);

  const handleStart = useCallback(() => {
    if (!isInteractionReady) {
      return;
    }

    setIsScattered(true);
    setTimeout(() => setShowOnboarding(true), 900);
  }, [isInteractionReady]);

  const handleOnboardingComplete = useCallback((data: Record<string, string>) => {
    console.info('[Onboarding] complete', data);
    hasCompletedOnboardingRef.current = true;
    setHasCompletedOnboarding(true);
    setShowOnboarding(false);
    setIsScattered(false);
    setIsBurning(false);
    setTransformedIds(new Set());
  }, []);

  const currentQuote = t.quotes[quoteIndex];
  const showTitleBurning = transformedIds.size >= 20;

  return (
    <div className={`${styles.page} ${isBurning ? styles.isBurning : ''}`}>
      {!isInteractionReady && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            cursor: 'default',
            pointerEvents: 'all',
          }}
        />
      )}

      <div className={`${styles.burningOverlay} ${isBurning ? styles.active : ''}`} />
      <LanguageSwitcher />

      <div className={styles.crowd}>
        <PeepsCrowd
          isScattered={isScattered}
          onPeepClick={handlePeepClick}
          isSelectable={isSelectionMode && !selectedPeep}
          transformedIds={transformedIds}
          onSlotsCreated={handleSlotsCreated}
        />
      </div>

      {selectedPeep && <ComicPage peep={selectedPeep} onClose={() => setSelectedPeep(null)} />}
      {showDialoguePage && <DialoguePage onClose={() => setShowDialoguePage(false)} />}

      {!selectedPeep && !isSelectionMode && (
        <PeepsCard
          isScattered={isScattered}
          slogan={currentQuote.text}
          source={currentQuote.source}
          isBurning={showTitleBurning}
        />
      )}

      {isSelectionMode && !selectedPeep && (
        <>
          {showSelectionHint && t?.selectionHint && (
            <div className={styles.selectionHintWrap}>
              <div className={styles.selectionHint}>{t.selectionHint}</div>
            </div>
          )}
          <div className={styles.selectionDialogueWrap}>
            <button
              type="button"
              onClick={() => setShowDialoguePage(true)}
              className={styles.dialogueTrigger}
              aria-label="Open dialogue page"
            >
              <span className={styles.dialogueTriggerLabel}>输入问题，打开新的对话页</span>
              <span className={styles.dialogueTriggerHint}>试试输入“知识图谱”</span>
            </button>
          </div>
        </>
      )}

      <OnboardingFlow isVisible={showOnboarding} onComplete={handleOnboardingComplete} />

      {!selectedPeep && !isSelectionMode && (
        <div
          className={styles.bottomBar}
          style={{
            opacity: isScattered ? 0 : 1,
            transform: isScattered ? 'translateY(100px) rotate(5deg) scale(0.9)' : 'translateY(0)',
            filter: isScattered ? 'blur(10px)' : 'none',
            transition: 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
            pointerEvents: isScattered ? 'none' : 'auto',
          }}
        >
          <button
            onClick={handleStart}
            className={`${styles.btnPrimary} ${isBurning ? styles.isBurning : ''}`}
            style={{ opacity: isInteractionReady ? 1 : 0.5, cursor: isInteractionReady ? 'pointer' : 'not-allowed' }}
          >
            {t.getStarted}
          </button>
        </div>
      )}
    </div>
  );
}
