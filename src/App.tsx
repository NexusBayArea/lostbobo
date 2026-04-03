import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { OnboardingProvider } from './components/onboarding/OnboardingProvider';
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';
import { DemoBanner } from './components/DemoBanner';

function DashboardPage() {
  return (
    <div className="min-h-screen bg-slate-950">
      <DemoBanner />
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-white mb-6">Dashboard</h1>
        <p className="text-slate-400">Welcome to SimHPC — Mercury AI Simulation Platform</p>
      </div>
    </div>
  );
}

function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-cyan-400 mb-4">SimHPC Login</h1>
        <p className="text-slate-400">Authentication via Supabase</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <OnboardingProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute requireAdmin>
              <AdminAnalyticsPage />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </OnboardingProvider>
  );
}
