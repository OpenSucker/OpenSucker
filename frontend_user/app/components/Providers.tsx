'use client';

import { I18nProvider } from '../lib/i18n-context';
import { CrowdProvider } from '../lib/crowd-context';

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <CrowdProvider>
        {children}
      </CrowdProvider>
    </I18nProvider>
  );
}
