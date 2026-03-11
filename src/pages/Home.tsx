import { PageLayout } from '@/components/PageLayout';
import { Hero } from '@/sections/Hero';
import { Stack } from '@/sections/Stack';
import { ValueDifferentiator } from '@/sections/ValueDifferentiator';
import { WhoItsFor } from '@/sections/WhoItsFor';

export function Home() {
  return (
    <PageLayout>
      <Hero />
      <Stack />
      <ValueDifferentiator />
      <WhoItsFor />
    </PageLayout>
  );
}
