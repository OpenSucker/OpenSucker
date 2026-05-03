'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useI18n } from '../lib/i18n-context';
import styles from './page.module.css';

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
            <Image
              src="/team-hero.svg"
              alt={t.teamPage.compositionText}
              width={1518}
              height={720}
              className={styles.teamArtwork}
              priority
            />
          </section>
        </header>

        <section className={styles.detailGrid}>
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

        <section className={styles.membersSection}>
          <div className={styles.membersHeader}>
            <p className={styles.cardEyebrow}>{t.teamPage.membersTitle}</p>
          </div>
          <div className={styles.membersGrid}>
            {t.teamPage.members.map((member) => (
              <article key={member.name} className={styles.memberCard}>
                <h2 className={styles.memberName}>{member.name}</h2>
                <p className={styles.memberRole}>{member.role}</p>
                <p className={styles.memberBio}>{member.bio}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}