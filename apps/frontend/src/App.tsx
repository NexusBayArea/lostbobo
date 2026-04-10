import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/hooks/useTheme';
import { Hero } from '@/sections/Hero';
import { Stack } from '@/sections/Stack';
import { ValueDifferentiator } from '@/sections/ValueDifferentiator';
import { WhoItsFor } from '@/sections/WhoItsFor';

// Lazy load heavy pages
const Dashboard = lazy(() => import('@/pages/Dashboard').then(module => ({ default: module.Dashboard })));
const ExperimentNotebook = lazy(() => import('@/pages/ExperimentNotebook'));
const AlphaControlRoom = lazy(() => import('@/pages/AlphaControlRoom').then(module => ({ default: module.AlphaControlRoom })));
const AdminAnalyticsPage = lazy(() => import('./pages/admin/AdminAnalyticsPage').then(module => ({ default: module.AdminAnalyticsPage })));
const Benchmarks = lazy(() => import('@/pages/Benchmarks').then(module => ({ default: module.Benchmarks })));
const Pricing = lazy(() => import('@/pages/Pricing').then(module => ({ default: module.Pricing })));
const About = lazy(() => import('@/pages/About').then(module => ({ default: module.About })));
const Docs = lazy(() => import('@/pages/Docs').then(module => ({ default: module.Docs })));
const APIReference = lazy(() => import('@/pages').then(module => ({ default: module.APIReference })));
const CCPA = lazy(() => import('@/pages/CCPA').then(module => ({ default: module.CCPA })));
const DPA = lazy(() => import('@/pages/DPA').then(module => ({ default: module.DPA })));
const CookiePolicy = lazy(() => import('@/pages/CookiePolicy').then(module => ({ default: module.CookiePolicy })));
const SignIn = lazy(() => import('@/pages/SignIn').then(module => ({ default: module.SignIn })));
const SignUp = lazy(() => import('@/pages/SignUp').then(module => ({ default: module.SignUp })));
const Terms = lazy(() => import('@/pages/Terms').then(module => ({ default: module.Terms })));
const Privacy = lazy(() => import('@/pages/Privacy').then(module => ({ default: module.Privacy })));
const Contact = lazy(() => import('@/pages/Contact').then(module => ({ default: module.Contact })));

import { CookieConsent } from '@/components/CookieConsent';
import { PageLayout } from '@/components/PageLayout';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

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

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-background text-foreground">
    <div className="flex flex-col items-center gap-4">
      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
      <p className="text-sm font-medium animate-pulse">Loading Mission Control...</p>
    </div>
  </div>
);

function App() {
  console.log('SimHPC: App component rendering...');
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/signup" element={<SignUp />} />
            <Route path="/signin" element={<SignIn />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/pricing" element={<Pricing />} />
            <Route path="/benchmarks" element={<Benchmarks />} />
            <Route path="/docs" element={<Docs />} />
            <Route path="/api-reference" element={<APIReference />} />
            <Route path="/ccpa" element={<CCPA />} />
            <Route path="/dpa" element={<DPA />} />
            <Route path="/cookies" element={<CookiePolicy />} />

            {/* Protected Dashboard Routes */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard/notebook"
              element={
                <ProtectedRoute>
                  <ExperimentNotebook />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard/alpha"
              element={
                <ProtectedRoute>
                  <AlphaControlRoom />
                </ProtectedRoute>
              }
            />

            {/* Admin Routes */}
            <Route
              path="/admin/analytics"
              element={
                <ProtectedRoute requireAdmin>
                  <AdminAnalyticsPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </Suspense>
        <CookieConsent />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
