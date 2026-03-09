import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/hooks/useTheme';
import { Hero } from '@/sections/Hero';
import { Stack } from '@/sections/Stack';
import { ValueDifferentiator } from '@/sections/ValueDifferentiator';
import { WhoItsFor } from '@/sections/WhoItsFor';

import { Dashboard } from '@/pages/Dashboard';
import ExperimentNotebook from '@/pages/ExperimentNotebook';
import { Benchmarks } from '@/pages/Benchmarks';
import { Pricing } from '@/pages/Pricing';
import { About } from '@/pages/About';
import { Docs } from '@/pages/Docs';
import { APIReference } from '@/pages/APIReference';
import { CCPA } from '@/pages/CCPA';
import { DPA } from '@/pages/DPA';
import { CookiePolicy } from '@/pages/CookiePolicy';
import { SignIn } from '@/pages/SignIn';
import { SignUp } from '@/pages/SignUp';
import { Terms } from '@/pages/Terms';
import { Privacy } from '@/pages/Privacy';
import { Contact } from '@/pages/Contact';

import { CookieConsent } from '@/components/CookieConsent';
import { PageLayout } from '@/components/PageLayout';

console.log('SimHPC: App.tsx loaded.');

function HomePage() {
  return (
    <PageLayout>
      <Hero />
      <Stack />
      <ValueDifferentiator />
      <WhoItsFor />
    </PageLayout>
  );
}

function App() {
  console.log('SimHPC: App component rendering...');
  return (
    <ThemeProvider>
      <BrowserRouter basename="/lostbobo">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/signup" element={<SignUp />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/dashboard/notebook" element={<ExperimentNotebook />} />
          <Route path="/benchmarks" element={<Benchmarks />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/about" element={<About />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/api-reference" element={<APIReference />} />
          <Route path="/ccpa" element={<CCPA />} />
          <Route path="/dpa" element={<DPA />} />
          <Route path="/cookies" element={<CookiePolicy />} />
          <Route path="/contact" element={<Contact />} />
        </Routes>
        <CookieConsent />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
