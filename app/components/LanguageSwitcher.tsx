'use client';

import React from 'react';
import { useI18n } from '../lib/i18n-context';
import styles from '../page.module.css';

export default function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  const toggleLanguage = () => {
    setLocale(locale === 'en' ? 'zh' : 'en');
  };

  return (
    <div className={styles.langSwitcherWrap}>
      <button onClick={toggleLanguage} className={styles.langBtn}>
        {locale === 'en' ? 'CN' : 'EN'}
      </button>
    </div>
  );
}
