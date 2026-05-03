'use client';

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import type { AccessoryType, BustPoseType, FaceType, FacialHairType, HairType } from 'react-peeps';
import { CROWD_SETTINGS } from '../lib/peeps-middleware';
import css from './onboarding.module.css';
import { Peep } from '../lib/react-peeps';
import { useI18n } from '../lib/i18n-context';
import { playTradingTest, ApiResponse, ApiQuestion } from '../lib/trading-api';

interface TradingTestProps {
  userId: string;
  onComplete: (result: any) => void;
  isVisible: boolean;
}

const GUIDE_HAIR: HairType = 'DocBouffant';
const GUIDE_BODY: BustPoseType = 'Coffee';
const GUIDE_FACE: FaceType = 'OldAged';
const GUIDE_FH: FacialHairType = 'None';
const GUIDE_ACC: AccessoryType = 'None';

function sanitizeDisplayText(value: string | null | undefined) {
  return (value ?? '')
    .replace(/\bundefined\b/gi, '')
    .replace(/\bnull\b/gi, '')
    .replace(/[|｜]{2,}/g, '|')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export default function TradingTest({ userId, onComplete, isVisible }: TradingTestProps) {
  const { t } = useI18n();
  const [apiResponse, setApiResponse] = useState<ApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [input, setInput] = useState('');
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const currentQuestion = apiResponse?.question;

  // Initial load
  useEffect(() => {
    if (isVisible && !apiResponse && !isLoading) {
      handleStep([]);
    }
  }, [isVisible, apiResponse, isLoading]);

  const handleStep = async (answer: string[]) => {
    setIsLoading(true);
    try {
      const data = await playTradingTest(userId, answer);
      setApiResponse(data);
      
      if (data.status === 'finished' && data.result) {
        onComplete(data.result);
      }
    } catch (error) {
      console.error('Trading test error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = useCallback((val?: string) => {
    const finalVal = (val ?? input).trim();
    if (!finalVal || isTyping || isLoading) return;

    handleStep([finalVal]);
    setInput('');
  }, [input, isTyping, isLoading]);

  const displaySourceText = useMemo(() => {
    if (currentQuestion) {
      const diffStr = '●'.repeat(currentQuestion.difficulty) + '○'.repeat(Math.max(0, 3 - currentQuestion.difficulty));
      return sanitizeDisplayText(
        `Q ${currentQuestion.id.replace(/^q/i, '')}｜${diffStr}\n${currentQuestion.stem}`
      );
    }
    return isLoading ? t.onboarding.evaluating : '';
  }, [currentQuestion, isLoading, t.onboarding.evaluating]);

  // Typewriter effect
  useEffect(() => {
    if (!isVisible || !displaySourceText) return;

    let i = 0;
    let tickTimer: ReturnType<typeof setTimeout> | undefined;

    const tick = () => {
      if (i < displaySourceText.length) {
        setDisplayedText(displaySourceText.slice(0, i + 1));
        i++;
        tickTimer = setTimeout(tick, 15);
      } else {
        setIsTyping(false);
      }
    };

    const startTimer = window.setTimeout(() => {
      setDisplayedText('');
      setIsTyping(true);
      tick();
    }, 100);

    return () => {
      if (startTimer) window.clearTimeout(startTimer);
      if (tickTimer) window.clearTimeout(tickTimer);
    };
  }, [displaySourceText, isVisible]);

  if (!isVisible || !apiResponse || apiResponse.status === 'finished') return null;

  return (
    <>
      <div className={css.speechBubble}>
        <p className={css.speechText}>
          {displayedText}
          <span className={`${css.cursor} ${isTyping ? css.cursorVisible : ''}`}>|</span>
        </p>
      </div>

      <div className={css.peepWrap}>
        <Peep
          style={{ width: 260, height: 320, display: 'block' }}
          hair={GUIDE_HAIR}
          body={GUIDE_BODY}
          face={GUIDE_FACE}
          facialHair={GUIDE_FH}
          accessory={GUIDE_ACC}
          strokeColor="#000000"
          backgroundColor="transparent"
          viewBox={CROWD_SETTINGS.VIEWBOX}
        />
      </div>

      <div className={`${css.inputArea} ${isTyping ? css.inputFaded : css.inputVisible}`}>
        <div className={css.stepInput}>
          <div className={css.inputLabel}>
            <span>{apiResponse.progress ? `Q ${apiResponse.progress.current} / ${apiResponse.progress.total}` : 'Trading Test'}</span>
          </div>

          {currentQuestion?.options?.length ? (
            <div className={css.optionGrid}>
              {currentQuestion.options.map(opt => (
                <button 
                  key={opt.key} 
                  className={css.optionChip} 
                  onClick={() => handleSend(opt.key)}
                  disabled={isLoading}
                >
                  {opt.text}
                </button>
              ))}
            </div>
          ) : (
            <div className={css.inputRow}>
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder={t.onboarding.finalThought.placeholder}
                className={css.textInput}
                autoFocus
                disabled={isLoading}
              />
              <button onClick={() => handleSend()} className={css.sendBtn} disabled={isLoading || !input.trim()}>
                ➤
              </button>
            </div>
          )}
          
          {apiResponse.message && (
            <div className={css.inputLabel} style={{ color: '#c00', marginTop: '8px' }}>
              {apiResponse.message}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
