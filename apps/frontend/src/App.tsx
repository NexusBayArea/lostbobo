import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@/hooks/useTheme';
import { OnboardingProvider } from '@/components/onboarding/OnboardingProvider';
import { HomePage } from '@/pages/HomePage';
import { SignIn } from '@/pages/SignIn';
import { SignUp } from '@/pages/SignUp';
import { Dashboard } from '@/pages/Dashboard';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminAnalyticsPage } from '@/pages/admin/AdminAnalyticsPage';
import { AlphaControlRoom } from '@/pages/AlphaControlRoom';
import { EngineerNotebook } from '@/pages/EngineerNotebook';
import Terms from '@/pages/legal/Terms';
import Privacy from '@/pages/legal/Privacy';
import Cookies from '@/pages/legal/Cookies';

export default function App() {
  return (
    <ThemeProvider>
      <OnboardingProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/signup" element={<SignUp />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
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
          <Route
            path="/notebook"
            element={
              <ProtectedRoute>
                <EngineerNotebook />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/analytics"
            element={
              <ProtectedRoute requireAdmin>
                <AdminAnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/cookies" element={<Cookies />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </OnboardingProvider>
    </ThemeProvider>
  );
}

