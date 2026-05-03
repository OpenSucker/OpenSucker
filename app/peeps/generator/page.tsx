import '@mantine/core/styles.css';
import 'rc-slider/assets/index.css';
import '../peeps.css';
import Providers from '../components/Providers';
import { PeepsGenerator } from '../components/PeepsGenerator';

export const metadata = {
  title: 'Open Sucker | Avatar Generator',
  description: 'Build and customize your unique characters.',
};

export default function GeneratorPage() {
  return (
    <Providers>
      <PeepsGenerator />
    </Providers>
  );
}
