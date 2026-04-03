import { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { OnboardingProvider } from './components/onboarding/OnboardingProvider';
import { DemoBanner } from './components/DemoBanner';
import { ConfigurationPanel, type Parameter } from './sections/dashboard/ConfigurationPanel';
import { RunControlPanel } from './sections/dashboard/RunControlPanel';
import { ResultsPanel } from './sections/dashboard/ResultsPanel';
import { DocumentPage } from './sections/dashboard/DocumentPage';
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';

const DEFAULT_PARAMS: Parameter[] = [
  { name: 'Thermal Conductivity', baseValue: 45.2, unit: 'W/m·K', perturbable: true, min: 30, max: 60 },
  { name: 'Young\'s Modulus', baseValue: 210, unit: 'GPa', perturbable: true, min: 180, max: 240 },
  { name: 'Heat Flux', baseValue: 1500, unit: 'W/m²', perturbable: true, min: 1000, max: 2000 },
  { name: 'Cooling Coefficient', baseValue: 0.85, unit: 'W/m²·K', perturbable: false, min: 0.5, max: 1.2 },
];

function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'configure' | 'results' | 'docs'>('configure');
  const [isRunning, setIsRunning] = useState(false);
  const [numRuns, setNumRuns] = useState(10);
  const [samplingMethod, setSamplingMethod] = useState('±10% Range (Random)');
  const [parameters, setParameters] = useState<Parameter[]>(DEFAULT_PARAMS);
  const [timeout, setTimeout] = useState(300);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [userBalance] = useState(100);
  const [completedRun, setCompletedRun] = useState<{
    run_id: string;
    results: unknown;
    progress: number;
  } | null>(null);

  const handleStartRun = () => {
    setIsRunning(true);
    const runId = crypto.randomUUID();
    setTimeout(() => {
      setIsRunning(false);
      setCompletedRun({ run_id: runId, results: {}, progress: 100 });
      setActiveTab('results');
    }, 3000);
  };

  const handleCancelRun = () => {
    setIsRunning(false);
  };

  const activeParams = parameters.filter((p) => p.perturbable).length;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <DemoBanner />
      <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">SimHPC Dashboard</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Mercury AI — Monte Carlo Robustness Analysis</p>
          </div>
          <div className="flex gap-2">
            {(['configure', 'results', 'docs'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'bg-blue-600 text-white'
                    : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:border-blue-500'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {activeTab === 'configure' && (
          <>
            <RunControlPanel
              onStartRun={handleStartRun}
              onCancelRun={handleCancelRun}
              isRunning={isRunning}
              numRuns={numRuns}
              samplingMethod={samplingMethod}
              activeParams={activeParams}
              userBalance={userBalance}
            />
            <ConfigurationPanel
              enabled={true}
              onEnabledChange={() => {}}
              numRuns={numRuns}
              onNumRunsChange={setNumRuns}
              samplingMethod={samplingMethod}
              onSamplingMethodChange={setSamplingMethod}
              parameters={parameters}
              onParametersChange={setParameters}
              timeout={timeout}
              onTimeoutChange={setTimeout}
              seed={seed}
              onSeedChange={setSeed}
            />
          </>
        )}

        {activeTab === 'results' &&
          (completedRun ? (
            <ResultsPanel run={completedRun} />
          ) : (
            <div className="text-center py-20 text-slate-500 dark:text-slate-400">
              <p className="text-lg">No results yet. Run a simulation first.</p>
              <button
                onClick={() => setActiveTab('configure')}
                className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
              >
                Go to Configure
              </button>
            </div>
          ))}

        {activeTab === 'docs' && <DocumentPage />}
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
