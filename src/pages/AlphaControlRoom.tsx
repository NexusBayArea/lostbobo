import { useEffect, useState, useRef } from "react";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { PageLayout } from "@/components/PageLayout";
import { motion, AnimatePresence } from "framer-motion";
import {
  Terminal,
  Activity,
  Zap,
  Play,
  Info,
  AlertTriangle,
  Lightbulb,
  Clock,
  Database,
  Cpu,
  Radio,
  ChevronRight,
  BookOpen,
  Download,
  History,
  TrendingUp,
  Thermometer,
  Sun,
  DollarSign,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

// --- Signal Sparkline Component ---
function Sparkline({ data, color = "#22c55e" }: { data: number[]; color?: string }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const h = 24;
  const w = 80;
  const points = data
    .map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`)
    .join(" ");

  return (
    <svg width={w} height={h} className="opacity-60">
      <polyline fill="none" stroke={color} strokeWidth="1.5" points={points} />
    </svg>
  );
}

// --- UTC Clock Component ---
function UTCClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);
  return (
    <span className="font-mono tabular-nums text-[10px]">
      {time.toUTCString().split(" ").slice(4).join(" ").replace(" GMT", "")} UTC
    </span>
  );
}

// --- Status Badge Component ---
function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const config = {
    running: { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/30", dot: "bg-blue-400 animate-pulse" },
    completed: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30", dot: "bg-emerald-400" },
    failed: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30", dot: "bg-red-400" },
    idle: { bg: "bg-slate-800/50", text: "text-slate-500", border: "border-slate-700/50", dot: "bg-slate-500" },
    queued: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30", dot: "bg-amber-400 animate-pulse" },
  }[s] || { bg: "bg-slate-800/50", text: "text-slate-500", border: "border-slate-700/50", dot: "bg-slate-500" };

  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider ${config.bg} ${config.text} border ${config.border}`}>
      <div className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {status}
    </div>
  );
}

export const AlphaControlRoom = () => {
  const { getToken } = useAuth();
  const [signals, setSignals] = useState<any>({});
  const [sims, setSims] = useState<any[]>([]);
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);
  const insightRef = useRef<HTMLDivElement>(null);

  // Signal history for sparklines
  const [signalHistory, setSignalHistory] = useState<{
    temp: number[];
    grid: number[];
    solar: number[];
    price: number[];
  }>({ temp: [], grid: [], solar: [], price: [] });

  const fetchAlphaData = async () => {
    const token = getToken();
    try {
      const signalData = await api.getAlphaSignals(token);
      setSignals(signalData);

      // Build sparkline history
      setSignalHistory((prev) => {
        const temp = typeof signalData.temperature === "number"
          ? signalData.temperature
          : parseFloat(String(signalData.temperature).replace(/[^0-9.-]/g, "")) || 0;
        const grid = parseFloat(String(signalData.grid_load).replace(/[^0-9.-]/g, "")) || 0;
        const solar = parseFloat(String(signalData.solar_output).replace(/[^0-9.-]/g, "")) || 0;
        const price = parseFloat(String(signalData.energy_price).replace(/[^0-9.$-]/g, "").replace("$", "")) || 0;
        return {
          temp: [...prev.temp.slice(-19), temp],
          grid: [...prev.grid.slice(-19), grid],
          solar: [...prev.solar.slice(-19), solar],
          price: [...prev.price.slice(-19), price],
        };
      });

      const insightData = await api.getAlphaInsights(token);
      setInsights(insightData);

      if (token) {
        const simData = await api.getAlphaSimulations(token);
        setSims(simData);
      }
    } catch (error) {
      console.error("Alpha Control Room fetch error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlphaData();
    const interval = setInterval(fetchAlphaData, 5000);
    return () => clearInterval(interval);
  }, [getToken]);

  // Auto-scroll insight feed
  useEffect(() => {
    if (insightRef.current) {
      insightRef.current.scrollTop = insightRef.current.scrollHeight;
    }
  }, [insights]);

  const handleRunSimulation = async () => {
    const token = getToken();
    if (!token) return;
    setIsTriggering(true);
    try {
      await api.runAlphaSimulation(token);
      toast.success("Grid simulation dispatched to worker mesh");
      fetchAlphaData();
    } catch (error) {
      console.error("Simulation trigger failed:", error);
      toast.error("Simulation dispatch failed");
    } finally {
      setIsTriggering(false);
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case "warning":
        return <AlertTriangle className="w-3.5 h-3.5 text-yellow-500" />;
      case "critical":
        return <AlertTriangle className="w-3.5 h-3.5 text-red-500 animate-pulse" />;
      case "suggestion":
        return <Lightbulb className="w-3.5 h-3.5 text-blue-400" />;
      default:
        return <Info className="w-3.5 h-3.5 text-emerald-400" />;
    }
  };

  const getSignalIcon = (key: string) => {
    switch (key) {
      case "temperature": return <Thermometer className="w-3.5 h-3.5" />;
      case "grid_load": return <Cpu className="w-3.5 h-3.5" />;
      case "energy_price": return <DollarSign className="w-3.5 h-3.5" />;
      case "solar_output": return <Sun className="w-3.5 h-3.5" />;
      default: return <Activity className="w-3.5 h-3.5" />;
    }
  };

  const signalEntries = [
    { key: "temperature", label: "Temperature", value: signals.temperature, history: signalHistory.temp, color: "#ef4444" },
    { key: "grid_load", label: "Grid Load", value: signals.grid_load, history: signalHistory.grid, color: "#3b82f6" },
    { key: "energy_price", label: "Energy Price", value: signals.energy_price, history: signalHistory.price, color: "#f59e0b" },
    { key: "solar_output", label: "Solar Output", value: signals.solar_output, history: signalHistory.solar, color: "#22c55e" },
  ];

  // Split sims into active & memory
  const activeSims = sims.filter((s) => ["running", "queued"].includes(s.status?.toLowerCase()));
  const memorySims = sims.filter((s) => !["running", "queued"].includes(s.status?.toLowerCase()));

  return (
    <PageLayout>
      <div className="min-h-screen bg-[#060A14] text-slate-200 p-4 md:p-6 font-mono selection:bg-blue-500/30">
        {/* Header */}
        <header className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800/60">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500/20 to-blue-500/20 border border-emerald-500/30 flex items-center justify-center">
                <Terminal className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse border-2 border-[#060A14]" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                SIMHPC CONTROL ROOM
                <span className="text-[9px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded uppercase tracking-widest">
                  Alpha
                </span>
              </h1>
              <p className="text-[10px] text-slate-600 uppercase tracking-[0.25em]">
                GPU-Accelerated Simulation Operations Center
              </p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="hidden md:flex items-center gap-2 text-emerald-400 text-[10px]">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              <span className="uppercase tracking-widest font-bold">Live Feed</span>
            </div>
            <div className="text-slate-500 flex items-center gap-1.5">
              <Clock className="w-3 h-3" />
              <UTCClock />
            </div>
          </div>
        </header>

        {/* Main Grid: Sidebar + Content */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

          {/* ═══════════ LEFT SIDEBAR: LIVE SIGNALS ═══════════ */}
          <div className="lg:col-span-3">
            <div className="bg-[#0A0F1C] border border-slate-800/70 rounded-xl overflow-hidden h-full">
              <div className="px-4 py-3 border-b border-slate-800/60 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                    Live Signals
                  </span>
                </div>
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
              </div>
              <div className="divide-y divide-slate-800/40">
                {signalEntries.map((sig) => (
                  <motion.div
                    key={sig.key}
                    className="px-4 py-4 hover:bg-slate-800/20 transition-colors group"
                    initial={false}
                    animate={{ opacity: 1 }}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2 text-slate-500 group-hover:text-slate-300 transition-colors">
                        {getSignalIcon(sig.key)}
                        <span className="text-[9px] uppercase tracking-[0.15em] font-semibold">
                          {sig.label}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-end justify-between">
                      <motion.span
                        key={String(sig.value)}
                        initial={{ opacity: 0.5, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="text-xl font-bold tracking-tight text-white"
                      >
                        {sig.value || "—"}
                      </motion.span>
                      <Sparkline data={sig.history} color={sig.color} />
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Mini System Status */}
              <div className="px-4 py-3 border-t border-slate-800/60">
                <div className="space-y-2">
                  {[
                    { label: "API", status: "nominal" },
                    { label: "Worker Mesh", status: "connected" },
                    { label: "Redis", status: "synced" },
                  ].map((sys) => (
                    <div key={sys.label} className="flex items-center justify-between">
                      <span className="text-[8px] text-slate-600 uppercase tracking-widest">
                        {sys.label}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <div className="w-1 h-1 bg-emerald-500 rounded-full" />
                        <span className="text-[8px] text-emerald-500/70 uppercase tracking-wider">
                          {sys.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ═══════════ RIGHT CONTENT ═══════════ */}
          <div className="lg:col-span-9 space-y-4">

            {/* ─── ACTIVE SIMULATIONS ─── */}
            <div className="bg-[#0A0F1C] border border-slate-800/70 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-800/60 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                    Active Simulations
                  </span>
                  {activeSims.length > 0 && (
                    <span className="text-[9px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1.5 py-0.5 rounded-full ml-1">
                      {activeSims.length}
                    </span>
                  )}
                </div>
                <Button
                  size="sm"
                  className="bg-emerald-600/90 hover:bg-emerald-600 text-white border-none text-[10px] h-7 px-4 uppercase font-black tracking-[0.15em] rounded-lg shadow-lg shadow-emerald-500/10 disabled:opacity-40"
                  onClick={handleRunSimulation}
                  disabled={isTriggering}
                >
                  {isTriggering ? (
                    <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                  ) : (
                    <Play className="w-3 h-3 mr-2 fill-current" />
                  )}
                  {isTriggering ? "Dispatching..." : "Run Grid Sim"}
                </Button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-[10px]">
                  <thead className="bg-[#080D18] text-slate-600 uppercase tracking-[0.2em]">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Simulation</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                      <th className="px-4 py-3 font-semibold hidden sm:table-cell">Timestamp</th>
                      <th className="px-4 py-3 font-semibold w-8"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/30">
                    <AnimatePresence mode="popLayout">
                      {sims.length > 0 ? (
                        sims.slice(0, 8).map((sim, idx) => (
                          <motion.tr
                            key={sim.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="hover:bg-blue-500/[0.03] transition-colors group cursor-default"
                          >
                            <td className="px-4 py-3">
                              <span className="font-bold text-slate-300 uppercase tracking-wider group-hover:text-white transition-colors">
                                {sim.simulation_type?.replace(/_/g, " ")}
                              </span>
                            </td>
                            <td className="px-4 py-3">
                              <StatusBadge status={sim.status} />
                            </td>
                            <td className="px-4 py-3 text-slate-600 italic hidden sm:table-cell">
                              {new Date(sim.created_at).toLocaleString()}
                            </td>
                            <td className="px-4 py-3">
                              <ChevronRight className="w-3 h-3 text-slate-700 group-hover:text-slate-400 transition-colors" />
                            </td>
                          </motion.tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={4} className="px-4 py-12 text-center">
                            <div className="flex flex-col items-center gap-2">
                              <Database className="w-6 h-6 text-slate-700" />
                              <span className="text-slate-600 text-[9px] uppercase tracking-[0.25em]">
                                No simulations in registry
                              </span>
                            </div>
                          </td>
                        </tr>
                      )}
                    </AnimatePresence>
                  </tbody>
                </table>
              </div>
            </div>

            {/* ─── BOTTOM ROW: INSIGHTS + MEMORY ─── */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

              {/* === SIMULATION INSIGHTS === */}
              <div className="bg-[#0A0F1C] border border-slate-800/70 rounded-xl overflow-hidden flex flex-col">
                <div className="px-4 py-3 border-b border-slate-800/60 flex items-center gap-2">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                    Simulation Insights
                  </span>
                </div>
                <div
                  ref={insightRef}
                  className="divide-y divide-slate-800/30 overflow-y-auto max-h-[280px] flex-1 scroll-smooth"
                  style={{ scrollbarWidth: "thin", scrollbarColor: "#1e293b transparent" }}
                >
                  {insights.length > 0 ? (
                    insights.map((item, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05 }}
                        className="px-4 py-3.5 hover:bg-slate-800/20 transition-colors"
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-0.5 flex-shrink-0">{getInsightIcon(item.type)}</div>
                          <div className="flex-1 min-w-0">
                            <p
                              className={`text-[11px] font-bold leading-snug ${
                                item.type === "warning"
                                  ? "text-yellow-400"
                                  : item.type === "critical"
                                  ? "text-red-400"
                                  : "text-slate-300"
                              }`}
                            >
                              {item.message}
                            </p>
                            {item.action && (
                              <p className="text-[9px] text-emerald-400/80 mt-1 flex items-center gap-1">
                                <ChevronRight className="w-2.5 h-2.5" /> {item.action}
                              </p>
                            )}
                            {item.confidence && (
                              <div className="mt-2 flex items-center gap-2">
                                <div className="h-1 flex-1 bg-slate-800 rounded-full overflow-hidden">
                                  <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${item.confidence * 100}%` }}
                                    transition={{ duration: 0.6 }}
                                    className="h-full bg-emerald-500/50 rounded-full"
                                  />
                                </div>
                                <span className="text-[8px] text-slate-600 font-mono tabular-nums">
                                  {(item.confidence * 100).toFixed(0)}%
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))
                  ) : (
                    <div className="px-4 py-12 text-center">
                      <Info className="w-5 h-5 text-slate-700 mx-auto mb-2" />
                      <span className="text-[9px] text-slate-600 uppercase tracking-[0.2em]">
                        Awaiting signal analysis...
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* === SIMULATION MEMORY === */}
              <div className="bg-[#0A0F1C] border border-slate-800/70 rounded-xl overflow-hidden flex flex-col">
                <div className="px-4 py-3 border-b border-slate-800/60 flex items-center gap-2">
                  <History className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                    Simulation Memory
                  </span>
                  {memorySims.length > 0 && (
                    <span className="text-[9px] bg-amber-500/10 text-amber-400 border border-amber-500/20 px-1.5 py-0.5 rounded-full ml-1">
                      {memorySims.length}
                    </span>
                  )}
                </div>
                <div
                  className="divide-y divide-slate-800/30 overflow-y-auto max-h-[280px] flex-1"
                  style={{ scrollbarWidth: "thin", scrollbarColor: "#1e293b transparent" }}
                >
                  {memorySims.length > 0 ? (
                    memorySims.map((sim, idx) => (
                      <motion.div
                        key={sim.id}
                        initial={{ opacity: 0, y: 4 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.04 }}
                        className="px-4 py-3 hover:bg-slate-800/20 transition-colors group cursor-default"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5 min-w-0 flex-1">
                            <Database className="w-3 h-3 text-slate-700 group-hover:text-slate-500 flex-shrink-0 transition-colors" />
                            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider truncate group-hover:text-slate-200 transition-colors">
                              {sim.simulation_type?.replace(/_/g, " ")}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 flex-shrink-0">
                            <StatusBadge status={sim.status} />
                            <span className="text-[8px] text-slate-700 font-mono tabular-nums hidden sm:block">
                              {new Date(sim.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </motion.div>
                    ))
                  ) : (
                    <div className="px-4 py-12 text-center">
                      <Database className="w-5 h-5 text-slate-700 mx-auto mb-2" />
                      <span className="text-[9px] text-slate-600 uppercase tracking-[0.2em]">
                        No past simulations stored
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ─── NOTEBOOK / ANALYSIS ─── */}
            <div className="bg-[#0A0F1C] border border-slate-800/70 rounded-xl overflow-hidden relative group">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600/[0.03] via-transparent to-purple-600/[0.03] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
              <div className="px-4 py-3 border-b border-slate-800/60 flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
                  Notebook / Analysis
                </span>
              </div>
              <div className="px-4 py-5 flex items-center justify-between gap-6 relative z-10">
                <p className="text-[11px] text-slate-500 leading-relaxed max-w-lg">
                  Launch the integrated analysis environment for deep spectral analysis on simulation results. Export engineering datasets and review experiment history.
                </p>
                <div className="flex gap-2 flex-shrink-0">
                  <Button
                    className="bg-blue-600/90 hover:bg-blue-600 text-white text-[10px] h-8 px-5 uppercase font-black tracking-[0.15em] rounded-lg shadow-lg shadow-blue-500/10"
                    onClick={() => window.open("/dashboard/notebook", "_blank")}
                  >
                    <Terminal className="w-3 h-3 mr-2" />
                    Launch Notebook
                  </Button>
                  <Button
                    variant="outline"
                    className="border-slate-800 bg-transparent text-slate-500 hover:bg-slate-800 hover:text-white text-[10px] h-8 px-4 uppercase font-bold tracking-[0.12em] rounded-lg"
                  >
                    <Download className="w-3 h-3 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer Status Bar */}
        <footer className="mt-6 pt-4 border-t border-slate-800/40 flex flex-col sm:flex-row justify-between items-center gap-2 text-[8px] text-slate-700 uppercase tracking-[0.25em] font-mono">
          <div className="flex gap-6 flex-wrap justify-center">
            <span className="flex items-center gap-1.5">
              <div className="w-1 h-1 bg-emerald-500 rounded-full" /> GPU Cluster: Online
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-1 h-1 bg-emerald-500 rounded-full" /> SUNDIALS Solver: Ready
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-1 h-1 bg-blue-500 rounded-full" /> Mercury AI: Connected
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-1 h-1 bg-emerald-500 rounded-full" /> Supabase: Synced
            </span>
          </div>
          <div className="text-slate-600">v1.5.0-ALPHA</div>
        </footer>
      </div>
    </PageLayout>
  );
};

export default AlphaControlRoom;
