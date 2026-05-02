'use client';

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import type { AccessoryType, BustPoseType, FaceType, FacialHairType, HairType } from 'react-peeps';
import { CROWD_SETTINGS } from '../lib/peeps-middleware';
import css from './onboarding.module.css';
import { LEEK_CHARACTERS } from '../lib/leek-lore';
import { TRADING_TEST_QUESTIONS } from '../lib/trading-test';
import { useI18n } from '../lib/i18n-context';
import { Peep } from '../lib/react-peeps';

interface OnboardingFlowProps {
  onComplete: (data: Record<string, string>) => void;
  isVisible: boolean;
}

type OnboardingStep = {
  key: string;
  speech: string;
  label: string;
  placeholder: string;
  options?: string[];
};

type TestAnswer = {
  questionId: string;
  answer: string;
};

type ScoreResult = {
  score: number;
  judgment: string;
  subStatus: string;
  isLeek: boolean;
};

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

export default function OnboardingFlow({ onComplete, isVisible }: OnboardingFlowProps) {
  const { t } = useI18n();
  const onboarding = t.onboarding;
  const [stepIndex, setStepIndex] = useState(0);
  const [input, setInput] = useState('');
  const [userData, setUserData] = useState<Record<string, string>>({});
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showPersonaSelect, setShowPersonaSelect] = useState(true);

  const steps = useMemo<OnboardingStep[]>(() => [
    {
      key: 'username',
      speech: onboarding.username.speech,
      label: onboarding.username.label,
      placeholder: onboarding.username.placeholder,
    },
    {
      key: 'gender',
      speech: onboarding.gender.speech,
      label: onboarding.gender.label,
      placeholder: onboarding.gender.placeholder,
      options: onboarding.gender.options,
    },
    {
      key: 'profession',
      speech: onboarding.profession.speech,
      label: onboarding.profession.label,
      placeholder: onboarding.profession.placeholder,
      options: onboarding.profession.options,
    },
    {
      key: 'doTest',
      speech: onboarding.doTest.speech,
      label: onboarding.doTest.label,
      placeholder: onboarding.doTest.placeholder,
      options: onboarding.doTest.options,
    },
    {
      key: 'finalThought',
      speech: onboarding.finalThought.speech,
      label: onboarding.finalThought.label,
      placeholder: onboarding.finalThought.placeholder,
    },
  ], [onboarding]);

  const finalThoughtStepIndex = useMemo(
    () => steps.findIndex((step) => step.key === 'finalThought'),
    [steps]
  );

  // Test state
  const [isTesting, setIsTesting] = useState(false);
  const [testIndex, setTestIndex] = useState(0);
  const [testAnswers, setTestAnswers] = useState<TestAnswer[]>([]);
  const [scoreResult, setScoreResult] = useState<ScoreResult | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const currentStep = steps[stepIndex];
  const testQuestion = isTesting ? TRADING_TEST_QUESTIONS[testIndex] : null;
  const displaySourceText = useMemo(() => {
    if (isTesting && testQuestion) {
      return sanitizeDisplayText(
        `Q ${testQuestion.id}｜${'●'.repeat(testQuestion.difficulty)}${'○'.repeat(3 - testQuestion.difficulty)}\n${testQuestion.question}`
      );
    }

    return sanitizeDisplayText(currentStep?.speech);
  }, [currentStep?.speech, isTesting, testQuestion]);

  // Handle persona select
  const handleSelectPersona = (id: string) => {
    const char = LEEK_CHARACTERS.find(c => c.id === id);
    if (char) {
      onComplete({
        username: char.name,
        gender: char.gender,
        profession: char.profession,
        persona: JSON.stringify(char)
      });
    }
  };

  const handleSkipToQuestions = () => {
    setShowPersonaSelect(false);
  };

  // Typewriter effect
  useEffect(() => {
    if (!isVisible || showPersonaSelect || scoreResult) return;

    let i = 0;
    let tickTimer: ReturnType<typeof setTimeout> | undefined;

    const tick = () => {
      if (i < displaySourceText.length) {
        setDisplayedText(displaySourceText.slice(0, i + 1));
        i++;
        tickTimer = setTimeout(tick, 30);
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
      if (startTimer) {
        window.clearTimeout(startTimer);
      }
      if (tickTimer) {
        window.clearTimeout(tickTimer);
      }
    };
  }, [displaySourceText, isVisible, scoreResult, showPersonaSelect]);

  // Mutation helper
  const mutateCharacter = useCallback(async (allData: Record<string, string>, configIndex: number = 0): Promise<Partial<Record<string, string>>> => {
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          configIndex,
          messages: [
            { role: 'user', content: `gender: ${allData.gender || ''}, profession: ${allData.profession || ''}, finalThought: ${allData.finalThought || ''}` },
          ],
        }),
      });
      if (res.ok) {
        const data = await res.json();
        return data.pages?.[0]?.summary ? { storyHint: data.pages[0].summary } : {};
      }
      return {};
    } catch {
      return {};
    }
  }, []);

  const finishOnboarding = useCallback(async (allData: Record<string, string>, answers: TestAnswer[] = [], configIndex: number = 0) => {
    setIsTyping(true);
    setDisplayedText(onboarding.evaluating);

    try {
      // 1. If we have test answers, get the score
      let finalScoreData = scoreResult;
      if (answers.length > 0 && !scoreResult) {
        const scoreRes = await fetch('/api/score-test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answers })
        });
        finalScoreData = await scoreRes.json();
        setScoreResult(finalScoreData);
      }

      // 2. Call chat API for story/character DNA (using dynamic config index)
      const dna = await mutateCharacter(allData, configIndex);
      setUserData(prev => ({
        ...prev,
        ...allData,
        ...(dna.storyHint ? { storyHint: dna.storyHint } : {})
      }));

      // If we didn't have a score screen to show, we can just complete
      if (!finalScoreData) {
        onComplete({
          ...allData,
          ...(dna.storyHint ? { storyHint: dna.storyHint } : {}),
        });
      }
    } catch (error) {
      console.error('Finalizing failed', error);
      onComplete(allData);
    } finally {
      setIsTyping(false);
    }
  }, [mutateCharacter, onComplete, onboarding.evaluating, scoreResult]);

  const handleFinalComplete = () => {
    onComplete({
      ...userData,
      tradingTest: JSON.stringify(testAnswers),
      testScore: scoreResult?.score.toString() || "0"
    });
  };

  const handleSend = useCallback(async (nextValue?: string) => {
    const val = (nextValue ?? input).trim();
    if (!val || isTyping) return;

    // Handle Test Questions
    if (isTesting && testQuestion) {
      const newAnswer = { questionId: testQuestion.id, answer: val };
      const nextAnswers = [...testAnswers, newAnswer];
      setTestAnswers(nextAnswers);
      setInput('');
      if (testIndex < TRADING_TEST_QUESTIONS.length - 1) {
        setTestIndex(prev => prev + 1);
      } else {
        // Test finished, go to final thought
        setIsTesting(false);
        setStepIndex(finalThoughtStepIndex);
      }
      return;
    }

    const newData = { ...userData, [currentStep.key]: val };
    setUserData(newData);
    setInput('');

    // Branching logic for 'doTest'
    if (currentStep.key === 'doTest') {
      if (val === onboarding.doTest.options[0]) {
        setIsTesting(true);
        return;
      } else {
        // Skip test, go to final thought
        setStepIndex(finalThoughtStepIndex);
        return;
      }
    }

    // Final Step
    if (currentStep.key === 'finalThought') {
      // Call API (using index 1 to show flexibility)
      finishOnboarding(newData, testAnswers, 1);
      return;
    }

    if (stepIndex < steps.length - 1) {
      setStepIndex(prev => prev + 1);
    }
  }, [currentStep, finalThoughtStepIndex, finishOnboarding, input, isTesting, isTyping, onboarding.doTest.options, stepIndex, steps.length, testAnswers, testIndex, testQuestion, userData]);

  if (!isVisible) return null;

  return (
    <div className={css.overlay}>
      <div className={css.content}>

        {!scoreResult ? (
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

              <div className={`${css.inputArea} ${isTyping && !showPersonaSelect ? css.inputHidden : css.inputVisible}`}>
                {showPersonaSelect ? (
                  <div className={css.personaSelection}>
                    <div className={css.inputLabel} style={{ marginBottom: '12px' }}>
                      <span>{onboarding.selectIdentity}</span>
                    </div>
                    <div className={css.personaGrid}>
                      {LEEK_CHARACTERS.map(char => (
                        <button key={char.id} className={css.personaCard} onClick={() => handleSelectPersona(char.id)}>
                          <div className={css.personaName}>{char.name}</div>
                          <div className={css.personaArchetype}>{char.archetype}</div>
                          <div className={css.personaProfession}>{char.profession}</div>
                        </button>
                      ))}
                    </div>
                    <button className={css.skipBtn} onClick={handleSkipToQuestions}>{onboarding.skipToQuestions}</button>
                  </div>
                ) : (
                  <div className={css.stepInput}>
                    <div className={css.inputLabel}>
                      <span>{isTesting ? `Q ${testIndex + 1} / ${TRADING_TEST_QUESTIONS.length}` : currentStep?.label}</span>
                    </div>

                  {(isTesting ? testQuestion?.options : currentStep.options)?.length ? (
                    <div className={css.optionGrid}>
                      {(isTesting ? testQuestion!.options! : currentStep.options!).map(opt => (
                        <button key={opt} className={css.optionChip} onClick={() => handleSend(opt)}>{opt}</button>
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
                          placeholder={currentStep?.placeholder ?? ''}
                          className={css.textInput}
                          autoFocus
                        />
                        <button onClick={() => handleSend()} className={css.sendBtn}>➤</button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className={`${css.scoreScreen} ${scoreResult.isLeek ? css.scoreLeek : css.scorePro}`}>
            <div className={css.scoreHeader}>{onboarding.scoreTitle}</div>
            <div className={css.scoreValue}>{scoreResult.score} <small>{onboarding.scorePoints}</small></div>
            <div className={css.scoreJudgment}>{scoreResult.judgment}</div>
            <div className={css.scoreSubStatus}>{scoreResult.subStatus}</div>
            <div className={css.scoreAction}>
              <button className={css.confirmBtn} onClick={handleFinalComplete}>
                {scoreResult.isLeek ? onboarding.confirmLeek : onboarding.confirmPro}
              </button>
            </div>
            {scoreResult.isLeek && (
              <div className={css.leekSeal}>{onboarding.leekSeal}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
