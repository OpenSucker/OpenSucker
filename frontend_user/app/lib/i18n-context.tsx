'use client';

import React, { createContext, useContext, useState } from 'react';
import { translations, Locale } from './translations';

type TranslationShape = typeof translations.zh;

const SUPPORTED_LOCALES: Locale[] = ['en', 'zh'];

function resolveLocale(value: string | null | undefined): Locale {
  if (value && SUPPORTED_LOCALES.includes(value as Locale)) {
    return value as Locale;
  }

  if (typeof navigator !== 'undefined') {
    return navigator.language.toLowerCase().startsWith('zh') ? 'zh' : 'en';
  }

  return 'zh';
}

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: TranslationShape;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => {
    if (typeof window === 'undefined') {
      return 'zh';
    }

    return resolveLocale(window.localStorage.getItem('locale'));
  });

  const handleSetLocale = (newLocale: Locale) => {
    const nextLocale = resolveLocale(newLocale);
    setLocale(nextLocale);
    localStorage.setItem('locale', nextLocale);
  };

  const value = {
    locale,
    setLocale: handleSetLocale,
    t: translations[locale] ?? translations.zh
  };

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}
