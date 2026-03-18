import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  BarChart3,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  Cpu,
  Loader2,
} from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';
import { JobProgress } from '@/components/JobProgress';
import { NotebookNavButton } from '@/components/NotebookNavButton';
import { cn } from '@/lib/utils';
import { ConfigurationPanel, type Parameter } from '@/sections/dashboard/ConfigurationPanel';
import { RunControlPanel } from '@/sections/dashboard/RunControlPanel';
import { ResultsPanel } from '@/sections/dashboard/ResultsPanel';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { DemoBanner } from '@/components/DemoBanner';
import { toast } from 'sonner';
import { SystemStatus } from '@/components/SystemStatus';

const sidebarItems = [
  { id: 'simulations', label: 'Simulations', icon: Play },
  { id: 'robustness', label: 'Robustness', icon: BarChart3 },
  { id: 'reports', label: 'Reports', icon: FileText },
  { id: 'settings', label: 'Settings', icon: Settings },
];

const DEFAULT_PARAMETERS: Parameter[] = [
  { name: 'boundary_flux', baseValue: 1000, unit: 'W/m²', perturbable: true, min: 500, max: 1500 },
  { name: 'thermal_conductivity', baseValue: 1.0, unit: 'W/(m·K)', perturbable: true, min: 0.5, max: 2.0 },
  { name: 'ambient_temp', baseValue: 300, unit: 'K', perturbable: true, min: 250, max: 350 },
  { name: 'mesh_refinement', baseValue: 2.0, unit: 'level', perturbable: false },
];

export function Dashboard() {
  const { getToken, user } = useAuth();
  const [activeTab, setActiveTab] = useState('robustness');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [currentRun, setCurrentRun] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [currentStatus, setCurrentStatus] = useState<'pending' | 'running' | 'completed' | 'failed' | 'queued' | 'processing'>('queued');
  const [progress, setProgress] = useState(0);
  const [userBalance] = useState(5000);

  // Robustness Config State
  const [robustnessEnabled, setRobustnessEnabled] = useState(true);
  const [numRuns, setNumRuns] = useState(15);
  const [samplingMethod, setSamplingMethod] = useState('±10%');
  const [parameters, setParameters] = useState(DEFAULT_PARAMETERS);
  const [timeout, setTimeoutVal] = useState(300);
  const [seed, setSeed] = useState<number | undefined>(undefined);

  // Demo state
  const isDemoUser = localStorage.getItem('demo_active') === 'true';
  const [demoRemaining, setDemoRemaining] = useState<number>(
    parseInt(localStorage.getItem('demo_remaining') || '0', 10)
  );
  const [demoLimit, setDemoLimit] = useState<number>(
    parseInt(localStorage.getItem('demo_limit') || '0', 10)
  );

  // Refresh demo usage on mount
  useEffect(() => {
    if (!isDemoUser) return;
    api.getDemoUsage().then((usage) => {
      setDemoRemaining(usage.remaining);
      setDemoLimit(usage.limit);
      localStorage.setItem('demo_remaining', String(usage.remaining));
      localStorage.setItem('demo_limit', String(usage.limit));
    });
  }, [isDemoUser]);

  const startPolling = async (runId: string) => {
    try {
      const token = getToken();
      const finalStatus = await api.pollStatus(runId, token, (p) => {
        setProgress(p);
        setCurrentStatus('processing');
      });

      setIsRunning(false);
      setCurrentStatus(finalStatus.status as any);
      
      if (finalStatus.status === 'completed') {
        setCurrentRun({
          run_id: finalStatus.run_id,
          results: finalStatus.results,
          ai_report: finalStatus.ai_report,
          config_summary: finalStatus.config_summary,
          progress: finalStatus.progress
        });
        toast.success('Simulation analysis completed!');
      } else {
        toast.error(`Simulation analysis failed: ${finalStatus.error || 'Unknown error'}`);
      }
    } catch (error: any) {
      setIsRunning(false);
      toast.error(`Polling failed: ${error.message}`);
    }
  };

  const handleStartRun = async (overrides?: { method: string; numRuns: number }) => {
    try {
      setIsRunning(true);
      setCurrentRun(null);
      setCurrentRunId(null);
      setProgress(0);
      setCurrentStatus('queued');

      const activeMethod = overrides?.method || samplingMethod;
      const activeNumRuns = overrides?.numRuns || numRuns;

      const config = {
        numRuns: activeNumRuns,
        samplingMethod: activeMethod,
        parameters,
        timeout,
        seed
      };

      const token = getToken();
      const response = await api.startRobustnessRun(config, token);
      setCurrentRunId(response.run_id);

      // Decrement demo usage if in demo mode
      if (isDemoUser) {
        const usage = await api.decrementDemoUsage();
        setDemoRemaining(usage.remaining);
        if (!usage.success) {
          toast.error('Demo limit reached. Please upgrade your plan.');
          setIsRunning(false);
          return;
        }
      }

      startPolling(response.run_id);
    } catch (error: any) {
      setIsRunning(false);
      toast.error(error.message || 'Failed to start simulation.');
      console.error(error);
    }
  };

  const handleCancelRun = async () => {
    if (!currentRunId) return;
    try {
      const token = getToken();
      await api.cancelRobustnessRun(currentRunId, token);
      setIsRunning(false);
      setCurrentRunId(null);
      toast.success('Simulation cancelled. Credits refunded.');
    } catch (error) {
      toast.error('Failed to cancel simulation.');
      console.error(error);
    }
  };

  const handleSignOut = async () => {
    const { supabase } = await import('@/lib/supabase');
    await supabase.auth.signOut();
    window.location.href = '/';
  };

  return (
    <div className="min-h-screen bg-background dark:bg-slate-900 flex">
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: isSidebarOpen ? 280 : 80,
          x: (typeof window !== 'undefined' && window.innerWidth < 1024)
            ? (isSidebarOpen ? 0 : -280)
            : 0,
        }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className={cn(
          'fixed left-0 top-0 bottom-0 z-40 bg-background dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 overflow-hidden',
          !isSidebarOpen && 'items-center'
        )}
      >
        {/* Logo */}
        <div className="h-[72px] flex items-center px-6 border-b border-slate-200 dark:border-slate-700">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 flex-shrink-0">
              <svg viewBox="0 0 48 48" fill="none" className="w-full h-full">
                <path d="M24 2L44 13.5V36.5L24 48L4 36.5V13.5L24 2Z" className="stroke-slate-900 dark:stroke-white" strokeWidth="2" />
                <path d="M24 2V48M4 13.5L44 36.5M44 13.5L4 36.5" className="stroke-slate-900 dark:stroke-white" strokeWidth="1.5" strokeOpacity="0.6" />
                <circle cx="24" cy="25" r="4" className="fill-blue-500" />
              </svg>
            </div>
            <AnimatePresence>
              {isSidebarOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="font-bold text-xl text-black dark:text-white whitespace-nowrap"
                >
                  Sim<span className="text-blue-500">HPC</span>
                </motion.span>
              )}
            </AnimatePresence>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {sidebarItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={cn(
                'w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all',
                activeTab === item.id
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700',
                !isSidebarOpen && 'justify-center px-2'
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              <AnimatePresence>
                {isSidebarOpen && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="font-medium whitespace-nowrap"
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
            </button>
          ))}
          <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
            <NotebookNavButton isSidebarOpen={isSidebarOpen} />
          </div>
          
          {isSidebarOpen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <SystemStatus />
            </motion.div>
          )}
        </nav>

        {/* Bottom Actions */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-3 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-all',
              !isSidebarOpen && 'justify-center px-2'
            )}
          >
            {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            <AnimatePresence>
              {isSidebarOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="font-medium whitespace-nowrap"
                >
                  Collapse
                </motion.span>
              )}
            </AnimatePresence>
          </button>
          <button
            onClick={handleSignOut}
            className={cn(
              'w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all mt-2',
              !isSidebarOpen && 'justify-center px-2'
            )}
          >
            <LogOut className="w-5 h-5" />
            <AnimatePresence>
              {isSidebarOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="font-medium whitespace-nowrap"
                >
                  Sign Out
                </motion.span>
              )}
            </AnimatePresence>
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main
        className={cn(
          'flex-1 min-h-screen transition-all duration-300 w-full',
          isSidebarOpen ? 'lg:pl-[280px]' : 'lg:pl-[80px]'
        )}
      >
        {/* Header */}
        <header className="h-[72px] bg-background/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-700 sticky top-0 z-30 px-4 sm:px-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="lg:hidden p-2 -ml-2 text-slate-600 dark:text-slate-400"
            >
              {isSidebarOpen ? <X /> : <Menu />}
            </button>
            <h1 className="text-xl font-semibold text-slate-900 dark:text-white capitalize truncate">
              {activeTab}
            </h1>
            {isRunning && (
              <div className="hidden lg:block ml-8 w-64">
                <JobProgress status={currentStatus} progress={progress} />
              </div>
            )}
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-medium">
              {user?.user_metadata?.full_name?.split(' ').map((n: string) => n[0]).join('') || 'JD'}
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-8">
          {/* Demo Banner */}
          {isDemoUser && (
            <DemoBanner remaining={demoRemaining} limit={demoLimit} />
          )}

          {activeTab === 'robustness' && (
            <div className="space-y-8">
              {/* Model Configuration */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6"
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-500">
                    <Cpu className="w-6 h-6" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Model Configuration</h2>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Select geometry and mesh parameters</p>
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Target Geometry</label>
                    <div className="flex gap-2">
                      <select className="flex-1 px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white">
                        <option>Battery_Cell_V4.step</option>
                        <option>Heatsink_Complex.iges</option>
                        <option>Pressure_Vessel.x_t</option>
                      </select>
                      <button className="px-4 py-3 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-xl font-medium border border-slate-200 dark:border-slate-600 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
                        Upload
                      </button>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Supported: STEP, IGES, Parasolid (.x_t), STL, MFEM (.mesh)
                    </p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Physics Solver</label>
                    <select className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white">
                      <option>SUNDIALS CVODE (Thermal-Transient)</option>
                      <option>MFEM Linear Static (Elasticity)</option>
                      <option>SUNDIALS KINSOL (Non-linear Steady)</option>
                    </select>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      GPU-accelerated solvers optimized for NVIDIA A40
                    </p>
                  </div>
                </div>
              </motion.div>

              <ConfigurationPanel
                enabled={robustnessEnabled}
                onEnabledChange={(val) => setRobustnessEnabled(val)}
                numRuns={numRuns}
                onNumRunsChange={(val) => setNumRuns(val)}
                samplingMethod={samplingMethod}
                onSamplingMethodChange={(val) => setSamplingMethod(val)}
                parameters={parameters}
                onParametersChange={(val) => setParameters(val)}
                timeout={timeout}
                onTimeoutChange={(val) => setTimeoutVal(val)}
                seed={seed}
                onSeedChange={(val) => setSeed(val)}
              />
              <RunControlPanel
                onStartRun={handleStartRun}
                onCancelRun={handleCancelRun}
                isRunning={isRunning}
                numRuns={numRuns}
                samplingMethod={samplingMethod}
                activeParams={parameters.filter(p => p.perturbable).length}
                userBalance={userBalance}
              />

              {isRunning && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-lg shadow-blue-500/5"
                >
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                    Live Simulation Status
                  </h3>
                  <JobProgress status={currentStatus} progress={progress} />
                  <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
                    Your simulation is being processed on a dedicated NVIDIA A40 GPU instance. 
                    Calculations are deterministic and verified against SUNDIALS solver benchmarks.
                  </p>
                </motion.div>
              )}

              {currentRun && <ResultsPanel run={currentRun} />}
            </div>
          )}

          {activeTab === 'simulations' && (
            <div className="text-center py-16">
              <Cpu className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                Simulation Library
              </h2>
              <p className="text-slate-500 dark:text-slate-400">
                Your saved simulations will appear here.
              </p>
            </div>
          )}

          {activeTab === 'reports' && (
            <div className="text-center py-16">
              <FileText className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
                AI Reports
              </h2>
              <p className="text-slate-500 dark:text-slate-400">
                Your generated reports will appear here.
              </p>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="max-w-2xl">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-6">
                Account Settings
              </h2>
              <div className="bg-background dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Display Name
                  </label>
                  <input
                    type="text"
                    defaultValue={user?.user_metadata?.full_name || "John Doe"}
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    defaultValue={user?.email || "john@company.com"}
                    disabled
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white opacity-60"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Company
                  </label>
                  <input
                    type="text"
                    defaultValue="Acme Engineering"
                    className="w-full px-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <button className="px-6 py-3 bg-slate-900 dark:bg-blue-600 text-white font-medium rounded-xl hover:bg-slate-800 dark:hover:bg-blue-700 transition-colors">
                 Save Changes
                </button>              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
