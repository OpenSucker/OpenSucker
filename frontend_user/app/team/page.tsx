'use client';

import Link from 'next/link';
import type { CSSProperties } from 'react';
import { Peep } from '../lib/react-peeps';
import { useI18n } from '../lib/i18n-context';
import styles from './page.module.css';

type TeamFigure = {
  id: string;
  body: string;
  hair: string;
  face: string;
  accessory: string;
  className: string;
  wrapperClassName?: string;
  scale?: number;
  viewBox?: { x: string; y: string; width: string; height: string };
  circleStyle?: CSSProperties;
};

const teamFigures: TeamFigure[] = [
  {
    id: 'left-standing',
    body: 'RestingBW',
    hair: 'MediumBangs',
    face: 'Calm',
    accessory: 'GlassRound',
    className: styles.leftStanding,
    scale: 1.02,
  },
  {
    id: 'left-seat',
    body: 'WheelChair',
    hair: 'LongAfro',
    face: 'Serious',
    accessory: 'None',
    className: styles.leftSeat,
    wrapperClassName: styles.figureWheel,
    scale: 1.06,
    viewBox: { x: '-180', y: '-40', width: '1100', height: '1200' },
    circleStyle: { fill: '#fff' },
  },
  {
    id: 'center-kneel',
    body: 'HandsBackWB',
    hair: 'LongAfro',
    face: 'SmileBig',
    accessory: 'GlassRoundThick',
    className: styles.centerKneel,
    scale: 1.05,
  },
  {
    id: 'center-seat',
    body: 'OneLegUpWB',
    hair: 'LongAfro',
    face: 'Calm',
    accessory: 'None',
    className: styles.centerSeat,
    scale: 1.08,
  },
  {
    id: 'right-seat',
    body: 'ClosedLegBW',
    hair: 'LongAfro',
    face: 'SmileTeeth',
    accessory: 'None',
    className: styles.rightSeat,
    scale: 1.06,
  },
  {
    id: 'right-standing',
    body: 'BlazerWB',
    hair: 'Long',
    face: 'Smile',
    accessory: 'None',
    className: styles.rightStanding,
    scale: 1.02,
  },
];

export default function TeamPage() {
  const { t } = useI18n();

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <header className={styles.hero}>
          <div className={styles.heroCopy}>
            <span className={styles.badge}>{t.teamPage.badge}</span>
            <h1 className={styles.title}>{t.teamPage.title}</h1>
            <p className={styles.summary}>{t.teamPage.summary}</p>
            <div className={styles.actions}>
              <Link href="/" className={styles.secondaryAction}>
                {t.teamPage.backHome}
              </Link>
              <Link href="/" className={styles.primaryAction}>
                {t.teamPage.startNow}
              </Link>
            </div>
          </div>

          <section className={styles.stage} aria-label={t.teamPage.compositionTitle}>
            <div className={styles.teamScene}>
              {teamFigures.map((figure) => (
                <div
                  key={figure.id}
                  className={`${styles.figure} ${figure.className} ${figure.wrapperClassName ?? ''}`.trim()}
                >
                  <Peep
                    body={figure.body as never}
                    hair={figure.hair as never}
                    face={figure.face as never}
                    accessory={figure.accessory as never}
                    facialHair={'None' as never}
                    strokeColor="#070707"
                    backgroundColor="#ffffff"
                    viewBox={figure.viewBox ?? { x: '-350', y: '-150', width: '1500', height: '1500' }}
                    circleStyle={figure.circleStyle}
                    style={{ width: '100%', height: '100%', transform: `scale(${figure.scale ?? 1})` }}
                  />
                </div>
              ))}
            </div>
          </section>
        </header>

        <section className={styles.detailGrid}>
          <article className={styles.detailCard}>
            <p className={styles.cardEyebrow}>{t.teamPage.compositionTitle}</p>
            <p className={styles.cardText}>{t.teamPage.compositionText}</p>
          </article>

          <article className={styles.detailCard}>
            <p className={styles.cardEyebrow}>{t.teamPage.principlesTitle}</p>
            <div className={styles.principlesList}>
              {t.teamPage.principles.map((item) => (
                <div key={item.title} className={styles.principleItem}>
                  <h2 className={styles.principleTitle}>{item.title}</h2>
                  <p className={styles.principleText}>{item.description}</p>
                </div>
              ))}
            </div>
          </article>
        </section>
      </div>
    </main>
  );
}