import Link from 'next/link';
import PeepsCrowd from './components/PeepsCrowd';
import PeepsCard from './components/PeepsCard';
import styles from './page.module.css';

export default function Home() {
  return (
    <div className={styles.page}>
      {/* Full-screen crowd */}
      <div className={styles.crowd}>
        <PeepsCrowd />
      </div>

      {/* Centered card */}
      <PeepsCard />

      {/* Buttons pinned to bottom of viewport */}

      {/* Buttons pinned to bottom of viewport */}
      <div className={styles.bottomBar}>
        <Link href="/peeps" className={styles.btnPrimary}>
          Get Started
        </Link>
        <a href="#" className={styles.btnSecondary}>
          Learn More
        </a>
      </div>
    </div>
  );
}
