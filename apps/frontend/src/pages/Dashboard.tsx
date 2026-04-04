import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, BarChart3, FileText, Settings, Cpu, Loader2, ShieldAlert, Zap, Layers, RefreshCw, AlertTriangle, MonitorPlay } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { Navigation } from '@/components/Navigation';
import { ConfigurationPanel, type Parameter } from '@/sections/dashboard/ConfigurationPanel';
import { RunControlPanel } from '@/sections/dashboard/RunControlPanel';
import { SimulationHistory } from '@/sections/dashboard/SimulationHistory';
import { ResultsPanel } from '@/sections/dashboard/ResultsPanel';
import { useAuth } from '@/hooks/useAuth';
import { useSimulations } from '@/hooks/useSimulations';
import { api } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

const DEFAULT_PARAMS: Parameter[] = [
  { name: 'Thermal Conductivity', baseValue: 45.2, unit: 'W/m·K', perturbable: true, min: 30, max: 60 },
  { name: "Young's Modulus", baseValue: 210, unit: 'GPa', perturbable: true, min: 180, max: 240 },
  { name: 'Heat Flux', baseValue: 1500, unit: 'W/m²', perturbable: true, min: 1000, max: 2000 },
  { name: 'Cooling Coefficient', baseValue: 0.85, unit: 'W/m²·K', perturbable: false, min: 0.5, max: 1.2 },
];

export function Dashboard() {
  const { user, isAdmin, getToken } = useAuth();
  const { simulations, loading: simsLoading } = useSimulations(user?.id);
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('simulations');
  const [isRunning, setIsRunning] = useState(false);
  const [numRuns, setNumRuns] = useState(10);
  const [samplingMethod, setSamplingMethod] = useState('±10% Range (Random)');
  const [parameters, setParameters] = useState<Parameter[]>(DEFAULT_PARAMS);
  const [timeout, setRequestTimeout] = useState(300);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Sync state with active run if any
  useEffect(() => {
    const hasRunning = simulations.some(s => s.status === 'running' || s.status === 'auditing');
    setIsRunning(hasRunning);
  }, [simulations]);

  const handleStartRun = async () => {
    try {
      setIsRunning(true);
      const token = await getToken();
      
      const config = {
        parameters: parameters.map(p => ({
          name: p.name,
          base_value: p.baseValue,
          unit: p.unit,
          perturbable: p.perturbable,
          min_value: p.min,
          max_value: p.max
        })),
        sampling: {
          method: samplingMethod,
          num_runs: numRuns,
          seed: seed
        }
      };

      await api.startSimulation(token, {
        scenario_name: `Robustness Run (${numRuns}x)`,
        config: config
      });

      toast.success('Simulation job dispatched to GPU fleet cluster.');
    } catch (error: any) {
      toast.error(error.message || 'Failed to start simulation');
      setIsRunning(false);
    }
  };

  const handleCancelRun = async () => {
    // Current limitation: we would need a specific jobId to cancel
    // Find the first running job if possible
    const runningJob = simulations.find(s => s.status === 'running' || s.status === 'auditing');
    if (!runningJob) {
      setIsRunning(false);
      return;
    }

    try {
      const token = await getToken();
      await api.cancelSimulation(token, runningJob.id);
      toast.info('Job cancellation command sent.');
    } catch (error: any) {
      toast.error(error.message || 'Failed to cancel job');
    }
  };

  const activeParams = parameters.filter((p) => p.perturbable).length;

  const sidebarItems = [
    { id: 'simulations', label: 'Command Deck', icon: MonitorPlay },
    { id: 'robustness', label: 'Solver Config', icon: Layers },
    { id: 'reports', label: 'Artifacts', icon: FileText },
    { id: 'settings', label: 'Preferences', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <Navigation />
      <div className="flex-1 flex pt-16">
        {/* Sidebar */}
        <motion.aside
          animate={{ width: sidebarOpen ? 240 : 80 }}
          className="fixed left-0 top-16 bottom-0 bg-slate-900/50 border-r border-slate-800 backdrop-blur-xl z-20"
        >
          <div className="p-4 space-y-6">
            <div className="space-y-1">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="w-full h-10 flex items-center gap-3 px-3 rounded-lg text-slate-500 hover:text-white hover:bg-slate-800 transition-all"
              >
                <Cpu className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span className="text-sm font-bold uppercase tracking-widest text-[10px]">SimHPC Engine</span>}
              </button>
              {sidebarItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setSelectedRun(null);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all ${
                    activeTab === item.id && !selectedRun
                      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_15px_rgba(34,211,238,0.1)]'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  <item.icon className="w-5 h-5 flex-shrink-0" />
                  {sidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
                </button>
              ))}
            </div>

            <Separator className="bg-slate-800" />

            <div className="space-y-1">
              <Link
                to="/dashboard/alpha"
                className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/5 transition-all group`}
              >
                <Zap className="w-5 h-5 flex-shrink-0 group-hover:animate-pulse" />
                {sidebarOpen && <span className="text-sm font-medium">Alpha Cockpit</span>}
              </Link>
              
              {isAdmin && (
                <Link
                  to="/admin/analytics"
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl text-slate-400 hover:text-red-400 hover:bg-red-500/5 transition-all group`}
                >
                  <ShieldAlert className="w-5 h-5 flex-shrink-0 group-hover:scale-110" />
                  {sidebarOpen && <span className="text-sm font-medium">Mission Control</span>}
                </Link>
              )}
            </div>
          </div>
          
          {sidebarOpen && (
             <div className="absolute bottom-6 left-6 right-6 p-4 bg-slate-950/50 border border-slate-800 rounded-xl">
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Fleet Status</p>
                <div className="flex items-center gap-2">
                   <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                   <span className="text-xs text-white font-mono lowercase">pod:simhpc_p_01</span>
                </div>
             </div>
          )}
        </motion.aside>

        {/* Main Content */}
        <main className={`flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-60' : 'ml-20'} p-8`}>
          <div className="max-w-7xl mx-auto space-y-8">
            <header className="flex items-center justify-between">
              <div className="space-y-1">
                <h1 className="text-3xl font-black text-white uppercase tracking-tight flex items-center gap-3">
                   {selectedRun ? 'Artifact Inspection' : activeTab === 'simulations' ? 'Command Deck' : activeTab === 'robustness' ? 'Solver Configuration' : activeTab}
                </h1>
                <p className="text-slate-400 font-mono text-xs uppercase tracking-widest">
                  {selectedRun ? `Run Hash: ${selectedRun.id.substring(0, 16)}` : 'Mercury AI — Multi-Cluster Physics Orchestration'}
                </p>
              </div>
              <div className="flex items-center gap-4">
                 {isRunning && (
                   <div className="flex items-center gap-3 px-4 py-2 bg-cyan-500/5 border border-cyan-500/20 rounded-full">
                      <RefreshCw className="w-3 h-3 text-cyan-400 animate-spin" />
                      <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest">Job Inflight</span>
                   </div>
                 )}
                 <Button variant="outline" className="border-slate-800 bg-slate-900" onClick={() => window.location.reload()}>
                    <RefreshCw className="w-4 h-4 mr-2" /> REFRESH
                 </Button>
              </div>
            </header>

            {selectedRun ? (
               <div className="space-y-6">
                  <Button 
                    variant="ghost" 
                    onClick={() => setSelectedRun(null)}
                    className="text-slate-400 hover:text-white pl-0"
                  >
                    ← Back to Dashboard
                  </Button>
                  <ResultsPanel run={selectedRun} />
               </div>
            ) : (
              <>
                {(activeTab === 'simulations' || activeTab === 'robustness') && (
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                    <div className="lg:col-span-4 h-full">
                       <RunControlPanel
                          onStartRun={handleStartRun}
                          onCancelRun={handleCancelRun}
                          isRunning={isRunning || simsLoading}
                          numRuns={numRuns}
                          samplingMethod={samplingMethod}
                          activeParams={activeParams}
                          userBalance={100}
                        />
                    </div>
                    
                    <div className="lg:col-span-8 flex flex-col gap-8">
                       {activeTab === 'robustness' ? (
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
                       ) : (
                          <SimulationHistory 
                             simulations={simulations} 
                             loading={simsLoading}
                             onViewDetails={setSelectedRun}
                          />
                       )}
                    </div>
                  </div>
                )}

                {activeTab === 'reports' && (
                  <SimulationHistory 
                     simulations={simulations} 
                     loading={simsLoading}
                     onViewDetails={setSelectedRun}
                  />
                )}

                {activeTab === 'settings' && (
                  <Card className="bg-slate-900 border-slate-800 p-12 text-center">
                    <Settings className="w-12 h-12 text-slate-800 mx-auto mb-4" />
                    <h2 className="text-xl font-bold text-white mb-2">Account Control</h2>
                    <p className="text-slate-400 mb-6">Configuration for {user?.email} — Tier: {isAdmin ? 'Administrator' : 'Beta Pilot'}</p>
                    <Button variant="outline" className="border-slate-800 text-slate-400">Manage Subscription</Button>
                  </Card>
                )}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
