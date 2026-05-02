'use client';

import styles from './dialoguePage.module.css';

type MarkdownMessageProps = {
  title?: string;
  content: string;
};

function renderInlineBold(text: string) {
  return text.split(/(\*\*.*?\*\*)/g).map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }

    return <span key={`${part}-${index}`}>{part}</span>;
  });
}

export default function MarkdownMessage({ title, content }: MarkdownMessageProps) {
  const lines = content.split('\n');

  return (
    <div className={styles.markdownBody}>
      {title ? <p className={styles.richMessageTitle}>{title}</p> : null}
      {lines.map((line, index) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return <div key={`spacer-${index}`} className={styles.markdownSpacer} />;
        }

        if (trimmed.startsWith('### ')) {
          return (
            <h3 key={`h3-${index}`} className={styles.markdownHeading}>
              {renderInlineBold(trimmed.slice(4))}
            </h3>
          );
        }

        if (trimmed.startsWith('- ')) {
          return (
            <p key={`bullet-${index}`} className={styles.markdownBullet}>
              <span className={styles.markdownBulletMark}>•</span>
              <span>{renderInlineBold(trimmed.slice(2))}</span>
            </p>
          );
        }

        return (
          <p key={`p-${index}`} className={styles.markdownParagraph}>
            {renderInlineBold(trimmed)}
          </p>
        );
      })}
    </div>
  );
}
