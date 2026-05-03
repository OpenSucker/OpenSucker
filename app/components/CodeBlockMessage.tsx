'use client';

import styles from './dialoguePage.module.css';

type CodeBlockMessageProps = {
  title: string;
  status: string;
  language: string;
  code: string;
};

export default function CodeBlockMessage({ title, status, language, code }: CodeBlockMessageProps) {
  return (
    <div className={styles.codeBlockCard}>
      <div className={styles.codeHeader}>
        <div className={styles.codeHeaderLeft}>
          <span className={styles.codeDot} />
          <span className={styles.codeTitle}>{title}</span>
          <span className={styles.codeStatus}>{status}</span>
        </div>
        <span className={styles.codeLang}>{language}</span>
      </div>
      <pre className={styles.codeContent}>
        <code>{code}</code>
      </pre>
    </div>
  );
}
