import PeepsCrowd from '../components/PeepsCrowd';
import PeepsCard from '../components/PeepsCard';
import Link from 'next/link';
import styles from '../page.module.css';

export const metadata = {
  title: 'Open Sucker | Peeps',
  description: 'The crowd of hand-drawn characters.',
};

export default function PeepsPage() {
  return (
    <div className={styles.page}>
      <div className={styles.crowd}>
        <PeepsCrowd />
      </div>
      <PeepsCard title="Open Sucker" slogan="Your character awaits." />
      <div className={styles.bottomBar}>
        <Link href="/peeps/generator" className={styles.btnPrimary}>Customize</Link>
        <Link href="/" className={styles.btnSecondary}>Back</Link>
      </div>
    </div>
  );
}
