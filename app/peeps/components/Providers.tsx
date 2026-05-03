'use client';

import { MantineProvider, createTheme } from '@mantine/core';
import { Provider } from '../utils/contextProvider';
import type { ReactNode } from 'react';

const theme = createTheme({
  fontFamily: 'Itim, sans-serif',
});

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <MantineProvider theme={theme}>
      <Provider>{children}</Provider>
    </MantineProvider>
  );
}
