import { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, BarChart3, FileText, Settings, Cpu, Loader2 } from 'lucide-react';
import { Navigation } from '@/components/Navigation';
import { ConfigurationPanel, type Parameter } from '@/sections/dashboard/ConfigurationPanel';
import { RunControlPanel } from '@/sections/dashboard/RunControlPanel';
import { ResultsPanel } from '@/sections/dashboard/ResultsPanel';
import { useAuth } from '@/hooks/useAuth';

const DEFAULT_PARAMS: Parameter[] = [
  { name: 'Thermal Conductivity', baseValue: 45.2, unit: 'W/m·K', perturbable: true, min: 30, max: 60 },
  { name: "Young's Modulus", baseValue: 210, unit: 'GPa', perturbable: true, min: 180, max: 240 },
  { name: 'Heat Flux', baseValue: 1500, unit: 'W/m²', perturbable: true, min: 1000, max: 2000 },
  { name: 'Cooling Coefficient', baseValue: 0.85, unit: 'W/m²·K', perturbable: false, min: 0.5, max: 1.2 },
];

const sidebarItems = [
  { id: 'simulations', label: 'Simulations', icon: Play },
  { id: 'robustness', label: 'Robustness', icon: BarChart3 },
  { id: 'reports', label: 'Reports', icon: FileText },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export function Dashboard() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('robustness');
  const [isRunning, setIsRunning] = useState(false);
  const [numRuns, setNumRuns] = useState(10);
  const [samplingMethod, setSamplingMethod] = useState('±10% Range (Random)');
  const [parameters, setParameters] = useState<Parameter[]>(DEFAULT_PARAMS);
  const [timeout, setRequestTimeout] = useState(300);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [completedRun, setCompletedRun] = useState<{ run_id: string; results: unknown; progress: number } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleStartRun = () => {
    setIsRunning(true);
    const runId = crypto.randomUUID();
    setTimeout(() => {
      setIsRunning(false);
      setCompletedRun({ run_id: runId, results: {}, progress: 100 });
    }, 3000);
  };

  const handleCancelRun = () => {
    setIsRunning(false);
  };

  const activeParams = parameters.filter((p) => p.perturbable).length;

  return (
    <div className="min-h-screen bg-slate-950">
      <Navigation />
      <div className="pt-16 flex">
        {/* Sidebar */}
        <motion.aside
          animate={{ width: sidebarOpen ? 240 : 64 }}
          className="fixed left-0 top-16 bottom-0 bg-slate-900 border-r border-slate-800 overflow-hidden"
        >
          <div className="p-4 space-y-2">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="w-full flex items-center gap-3 px-3 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            >
              <Cpu className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="text-sm font-medium">SimHPC</span>}
            </button>
            {sidebarItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  activeTab === item.id
                    ? 'bg-cyan-500/10 text-cyan-400'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
              </button>
            ))}
          </div>
        </motion.aside>

        {/* Main Content */}
        <main className={`flex-1 ${sidebarOpen ? 'ml-60' : 'ml-16'} p-6`}>
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-white capitalize">{activeTab}</h1>
                <p className="text-slate-400 text-sm mt-1">Mercury AI — Monte Carlo Robustness Analysis</p>
              </div>
              {isRunning && (
                <div className="flex items-center gap-2 text-cyan-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm font-medium">Running...</span>
                </div>
              )}
            </div>

            {activeTab === 'simulations' && (
              <RunControlPanel
                onStartRun={handleStartRun}
                onCancelRun={handleCancelRun}
                isRunning={isRunning}
                numRuns={numRuns}
                samplingMethod={samplingMethod}
                activeParams={activeParams}
                userBalance={100}
              />
            )}

            {activeTab === 'robustness' && (
              <>
                <RunControlPanel
                  onStartRun={handleStartRun}
                  onCancelRun={handleCancelRun}
                  isRunning={isRunning}
                  numRuns={numRuns}
                  samplingMethod={samplingMethod}
                  activeParams={activeParams}
                  userBalance={100}
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
                  onTimeoutChange={setRequestTimeout}
                  seed={seed}
                  onSeedChange={setSeed}
                />
              </>
            )}

            {activeTab === 'reports' && (
              completedRun ? (
                <ResultsPanel run={completedRun} />
              ) : (
                <div className="text-center py-20 text-slate-500">
                  <p className="text-lg">No reports yet. Run a simulation first.</p>
                </div>
              )
            )}

            {activeTab === 'settings' && (
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8">
                <h2 className="text-xl font-bold text-white mb-4">Settings</h2>
                <p className="text-slate-400">Logged in as {user?.email}</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
