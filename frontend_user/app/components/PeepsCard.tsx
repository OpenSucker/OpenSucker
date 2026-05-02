import React, { useState, useEffect } from 'react';
import styles from '../page.module.css';

export interface PeepsCardProps {
  title?: string;
  slogan?: string;
  source?: string;
  isScattered?: boolean;
  isBurning?: boolean;
}

export default function PeepsCard({ 
  title = "Open Sucker", 
  slogan = "Bulls make money, bears make money, pigs get slaughtered.",
  source,
  isScattered,
  isBurning
}: PeepsCardProps) {
  const [displaySlogan, setDisplaySlogan] = useState("");
  const [isSloganDone, setIsSloganDone] = useState(false);

  useEffect(() => {
    setDisplaySlogan("");
    setIsSloganDone(false);

    let sloganIndex = 0;
    const sloganInterval = setInterval(() => {
      setDisplaySlogan(slogan.substring(0, sloganIndex + 1));
      sloganIndex++;
      if (sloganIndex >= slogan.length) {
        clearInterval(sloganInterval);
        setIsSloganDone(true);
      }
    }, 30);

    return () => clearInterval(sloganInterval);
  }, [slogan]);

  return (
    <div className={styles.cardWrap} style={{
      opacity: isScattered ? 0 : 1,
      transform: isScattered ? 'scale(0.5) translateY(-200px) rotate(-15deg)' : 'none',
      filter: isScattered ? 'blur(20px)' : 'none',
      transition: 'all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)',
      pointerEvents: isScattered ? 'none' : 'auto'
    }}>
      <div className={`${styles.card} ${isBurning ? styles.isBurning : ''}`}>
        <h1 className={`${styles.title} ${isBurning ? styles.isBurning : ''}`}>
          {title}
        </h1>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <p className={`${styles.slogan} ${isBurning ? styles.isBurning : ''}`}>
            {displaySlogan}
            {!isSloganDone && <span className={styles.cursor}>|</span>}
          </p>
          {source && isSloganDone && (
            <p className={`${styles.source} ${isBurning ? styles.isBurning : ''}`}>
              —— {source}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
