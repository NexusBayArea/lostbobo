import React, { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { PageLayout } from "@/components/PageLayout";
import { Terminal, Activity, Database, Zap, ExternalLink, Play, Info, AlertTriangle, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export const AlphaControlRoom = () => {
  const { getToken } = useAuth();
  const [signals, setSignals] = useState<any>({});
  const [sims, setSims] = useState<any[]>([]);
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAlphaData = async () => {
    const token = getToken();
    try {
      const signalData = await api.getAlphaSignals(token);
      setSignals(signalData);
      
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
    const interval = setInterval(fetchAlphaData, 5000); // Poll every 5s for "live" feel
    return () => clearInterval(interval);
  }, [getToken]);

  const handleRunSimulation = async () => {
    const token = getToken();
    if (!token) return;
    try {
      await api.runAlphaSimulation(token);
      fetchAlphaData(); // Refresh list
    } catch (error) {
      console.error("Simulation trigger failed:", error);
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'warning': return <AlertTriangle className="w-3 h-3 text-yellow-500" />;
      case 'critical': return <AlertTriangle className="w-3 h-3 text-red-500 animate-pulse" />;
      case 'suggestion': return <Lightbulb className="w-3 h-3 text-blue-400" />;
      default: return <Info className="w-3 h-3 text-green-400" />;
    }
  };

  return (
    <PageLayout>
      <div className="p-6 bg-[#080E1C] min-h-screen text-slate-200 font-mono">
        <div className="flex items-center justify-between mb-8 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <Terminal className="w-8 h-8 text-green-400" />
            <h1 className="text-2xl font-bold tracking-tighter text-white uppercase">
              SimHPC Alpha Control Room
            </h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-xs text-green-400 animate-pulse">
              <Activity className="w-4 h-4" />
              LIVE SYSTEM FEED
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* LIVE SIGNALS */}
          <Card className="bg-black border-slate-800 text-green-400 shadow-[0_0_15px_rgba(34,197,94,0.1)]">
            <CardHeader className="border-b border-slate-800">
              <CardTitle className="text-sm flex items-center gap-2 uppercase tracking-widest">
                <Zap className="w-4 h-4 text-green-400" />
                Live Signals
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div className="flex justify-between items-center group">
                <span className="text-slate-500 group-hover:text-slate-300 transition-colors uppercase text-[10px]">Temperature</span>
                <span className="text-xl font-bold tracking-widest">{signals.temperature || "---"}</span>
              </div>
              <div className="flex justify-between items-center group">
                <span className="text-slate-500 group-hover:text-slate-300 transition-colors uppercase text-[10px]">Grid Load</span>
                <span className="text-xl font-bold tracking-widest">{signals.grid_load || "---"}</span>
              </div>
              <div className="flex justify-between items-center group">
                <span className="text-slate-500 group-hover:text-slate-300 transition-colors uppercase text-[10px]">Energy Price</span>
                <span className="text-xl font-bold tracking-widest">{signals.energy_price || "---"}</span>
              </div>
              <div className="flex justify-between items-center group">
                <span className="text-slate-500 group-hover:text-slate-300 transition-colors uppercase text-[10px]">Solar Output</span>
                <span className="text-xl font-bold tracking-widest">{signals.solar_output || "---"}</span>
              </div>
            </CardContent>
          </Card>

          {/* ACTIVE SIMULATIONS */}
          <Card className="md:col-span-2 bg-[#0C1222] border-slate-800 shadow-xl">
            <CardHeader className="border-b border-slate-800 flex flex-row items-center justify-between py-3">
              <CardTitle className="text-xs flex items-center gap-2 text-slate-400 uppercase tracking-[0.2em]">
                <Activity className="w-4 h-4 text-blue-500" />
                Active Simulations
              </CardTitle>
              <Button 
                variant="outline" 
                size="sm" 
                className="bg-green-600 hover:bg-green-700 text-white border-none text-[10px] h-7 px-3 uppercase font-black tracking-widest"
                onClick={handleRunSimulation}
              >
                <Play className="w-3 h-3 mr-2 fill-current" />
                Run Grid Sim
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-[10px]">
                  <thead className="bg-slate-950 text-slate-500 uppercase tracking-widest">
                    <tr>
                      <th className="p-4 font-medium border-b border-slate-800">Simulation Type</th>
                      <th className="p-4 font-medium border-b border-slate-800">Status</th>
                      <th className="p-4 font-medium border-b border-slate-800">Created At</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {sims.length > 0 ? sims.map((sim) => (
                      <tr key={sim.id} className="hover:bg-blue-600/5 transition-colors group">
                        <td className="p-4 font-bold text-slate-300 uppercase tracking-wider group-hover:text-white">{sim.simulation_type}</td>
                        <td className="p-4">
                          <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-tighter ${
                            sim.status.toLowerCase() === 'running' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                            sim.status.toLowerCase() === 'completed' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                            'bg-slate-800/50 text-slate-500 border border-slate-700/50'
                          }`}>
                            <div className={`w-1 h-1 rounded-full ${
                              sim.status.toLowerCase() === 'running' ? 'bg-blue-400 animate-pulse' :
                              sim.status.toLowerCase() === 'completed' ? 'bg-green-400' :
                              'bg-slate-500'
                            }`} />
                            {sim.status}
                          </div>
                        </td>
                        <td className="p-4 text-slate-600 font-mono italic">
                          {new Date(sim.created_at).toLocaleString()}
                        </td>
                      </tr>
                    )) : (
                      <tr>
                        <td colSpan={3} className="p-12 text-center text-slate-600 italic uppercase tracking-[0.3em] text-[9px]">
                          No active simulations found in the registry.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* SIMULATION INSIGHTS */}
          <Card className="bg-[#0C1222] border-slate-800 shadow-lg">
            <CardHeader className="border-b border-slate-800 py-3">
              <CardTitle className="text-[10px] flex items-center gap-2 text-slate-400 uppercase tracking-[0.2em]">
                <Info className="w-4 h-4 text-green-500" />
                Simulation Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 overflow-y-auto max-h-[300px] insight-feed">
              <div className="divide-y divide-slate-800">
                {insights.map((item, idx) => (
                  <div key={idx} className="p-4 hover:bg-slate-900/50 transition-colors">
                    <div className="flex items-start gap-3">
                      <div className="mt-1">{getInsightIcon(item.type)}</div>
                      <div className="flex-1">
                        <p className={`text-[11px] font-bold tracking-tight leading-relaxed uppercase ${
                          item.type === 'warning' ? 'text-yellow-500' : 
                          item.type === 'critical' ? 'text-red-500' : 
                          'text-slate-300'
                        }`}>
                          {item.message}
                        </p>
                        {item.action && (
                          <p className="text-[9px] text-green-400/80 mt-1 italic tracking-widest uppercase">
                            → {item.action}
                          </p>
                        )}
                        {item.confidence && (
                          <div className="mt-2 flex items-center gap-2">
                            <div className="h-1 flex-1 bg-slate-800 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-green-500/50" 
                                style={{ width: `${item.confidence * 100}%` }} 
                              />
                            </div>
                            <span className="text-[8px] text-slate-600 font-mono">{(item.confidence * 100).toFixed(0)}% CONF</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* NOTEBOOK / ANALYSIS */}
          <Card className="md:col-span-2 bg-[#0C1222] border-slate-800 overflow-hidden relative group shadow-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-transparent to-purple-600/5 opacity-50 group-hover:opacity-100 transition-opacity pointer-events-none" />
            <CardHeader className="border-b border-slate-800 py-3">
              <CardTitle className="text-[10px] flex items-center gap-2 text-slate-400 uppercase tracking-[0.2em]">
                <Terminal className="w-4 h-4 text-blue-500" />
                Notebook / Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-10 pb-10 flex flex-col items-center justify-center text-center px-8 relative z-10">
              <div className="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6 group-hover:border-blue-500/50 transition-colors shadow-inner">
                <Terminal className="w-7 h-7 text-slate-600 group-hover:text-blue-400 transition-colors" />
              </div>
              <p className="text-slate-500 text-[11px] leading-relaxed max-w-sm mb-8 italic uppercase tracking-wider">
                Launch the integrated Jupyter environment to perform deep spectral analysis on simulation results and export engineering datasets.
              </p>
              <div className="flex flex-wrap justify-center gap-4">
                <Button 
                  className="bg-blue-600 hover:bg-blue-700 text-white border-none px-10 h-9 rounded-none uppercase tracking-[0.2em] text-[10px] font-black shadow-[0_0_20px_rgba(37,99,235,0.2)]"
                  onClick={() => window.open("/dashboard/notebook", "_blank")}
                >
                  Launch Notebook
                </Button>
                <Button 
                  variant="outline"
                  className="border-slate-800 bg-transparent text-slate-500 hover:bg-slate-800 hover:text-white rounded-none uppercase tracking-[0.2em] text-[10px] font-black h-9 px-6"
                >
                  Export Simulation Data
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* FOOTER STATUS */}
        <div className="mt-8 border-t border-slate-800/50 pt-4 flex justify-between items-center text-[9px] text-slate-600 uppercase tracking-[0.2em] font-mono">
          <div className="flex gap-6">
            <span className="flex items-center gap-2"><div className="w-1 h-1 bg-green-500 rounded-full" /> API STATUS: NOMINAL</span>
            <span className="flex items-center gap-2"><div className="w-1 h-1 bg-green-500 rounded-full" /> WORKER MESH: CONNECTED</span>
            <span className="flex items-center gap-2"><div className="w-1 h-1 bg-blue-500 rounded-full" /> REDIS SYNC: ACTIVE</span>
          </div>
          <div>v2.2.0-ALPHA_STABLE</div>
        </div>
      </div>
    </PageLayout>
  );
};

export default AlphaControlRoom;
