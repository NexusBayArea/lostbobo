import React, { useState, useEffect, useMemo } from 'react';
import { useSimulations } from '../../hooks/useSimulations';
import { useAuth } from '../../hooks/useAuth';
import { supabase } from '../../lib/supabase';
import { RunStatusResponse } from '../../types/simulations';
import { 
  Copy, Check, Activity, LayoutDashboard, 
  Terminal, ChevronRight, Inbox, AlertCircle 
} from 'lucide-react';

// --- Sub-Component: Defensive Copy Button ---
const CopyButton = ({ text }: { text: string | undefined | null }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  if (!text) return null;

  return (
    <button 
      onClick={handleCopy} 
      title="Copy ID"
      className="ml-2 text-muted-foreground hover:text-primary transition-colors focus:outline-none"
    >
      {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
    </button>
  );
};

import { isPingRecent, formatPing } from '../../lib/utils';
// ... rest of the imports ...

// --- Helpers ---
// Remove the old local versions as we now use the ones from '../../lib/utils'


export const AdminAnalyticsPage = () => {
  const { user } = useAuth();
  const { simulations = [], loading, error } = useSimulations(user?.id || '');
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const [fleetMetrics, setFleetMetrics] = useState({ active_pods: 0, hourly_spend_usd: '0.00' });

  // 1. Safe Metric Fetching
  useEffect(() => {
    let isMounted = true;
    const fetchMetrics = async () => {
      try {
        const { data, error: fetchError } = await supabase.functions.invoke('get-fleet-metrics');
        if (isMounted && data && !fetchError) {
          setFleetMetrics({
            active_pods: data.active_pods ?? 0,
            hourly_spend_usd: data.hourly_spend_usd ?? '0.00'
          });
        }
      } catch (err) {
        console.error("Metric sync failed:", err);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  // 2. Memoized filtering to prevent unnecessary re-renders
  const safeSimulations = useMemo(() => {
    return Array.isArray(simulations) ? simulations : [];
  }, [simulations]);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-sidebar border-r border-border transition-transform duration-300 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}>
        <div className="p-6 flex flex-col h-full">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-8 h-8 bg-primary rounded flex items-center justify-center text-primary-foreground font-bold text-xs">HPC</div>
            <h2 className="text-xl font-bold tracking-tight">SimHPC</h2>
          </div>
          
          <nav className="flex-1 space-y-1">
            <button className="flex items-center gap-3 w-full px-3 py-2 rounded-md bg-accent text-accent-foreground text-sm font-medium">
              <LayoutDashboard size={18} /> Fleet Analytics
            </button>
            <button className="flex items-center gap-3 w-full px-3 py-2 rounded-md hover:bg-accent/50 text-muted-foreground hover:text-foreground transition-colors text-sm font-medium">
              <Terminal size={18} /> Live Logs
            </button>
          </nav>

          <div className="mt-auto p-3 bg-muted/50 rounded-lg border border-border">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">Gateway: 8080</span>
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" />
            </div>
            <p className="text-[11px] text-muted-foreground">Cluster: Primary-Alpha</p>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-4 lg:p-8">
        <header className="mb-8">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
            <span>Admin</span> <ChevronRight size={12} /> <span className="text-foreground">Fleet Analytics</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Fleet Analytics</h1>
        </header>

        {/* 3. Conditional State Mapping */}
        {loading ? (
          <div className="flex items-center justify-center h-64 text-muted-foreground animate-pulse">
            Syncing with Supabase cluster...
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-64 bg-destructive/5 border border-destructive/20 rounded-xl p-6 text-center">
            <AlertCircle className="text-destructive mb-2" size={32} />
            <p className="text-sm font-medium text-destructive">Failed to load simulations</p>
            <p className="text-xs text-muted-foreground mt-1">Please verify your admin permissions.</p>
          </div>
        ) : safeSimulations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed border-border rounded-xl bg-card/30">
            <Inbox className="w-10 h-10 text-muted-foreground/30 mb-4" />
            <h3 className="text-sm font-semibold">No simulation data found</h3>
            <p className="text-xs text-muted-foreground mt-1 mb-6">Initialize a job via the API to see live metrics.</p>
            <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-xs font-bold hover:opacity-90">
              Go to Sandbox
            </button>
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead className="bg-muted/50 border-b border-border text-muted-foreground">
                  <tr>
                    <th className="px-6 py-4 font-semibold text-xs uppercase">Job ID</th>
                    <th className="px-6 py-4 font-semibold text-xs uppercase text-center">Verify</th>
                    <th className="px-6 py-4 font-semibold text-xs uppercase text-center">Cost</th>
                    <th className="px-6 py-4 font-semibold text-xs uppercase">Health</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {(safeSimulations as RunStatusResponse[]).map((sim) => (
                    <tr key={sim.id} className="hover:bg-muted/20 transition-colors group">
                      <td className="px-6 py-4 font-mono text-[13px] flex items-center">
                        <span className="text-muted-foreground/60">#</span>
                        {sim.job_id?.substring(0, 8) ?? 'N/A'}
                        <CopyButton text={sim.job_id} />
                      </td>
                      <td className="px-6 py-4 text-center">
                        {sim.certificate_hash ? (
                          <span title="Verifiable Run" className="text-emerald-500">🛡️</span>
                        ) : (
                          <span className="text-gray-600">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-center text-xs font-bold text-gray-400">
                        {sim.credit_cost} CR
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 group">
                          {/* Visual Health Indicator */}
                          <div 
                            className={`h-2 w-2 rounded-full shadow-sm transition-colors duration-500 ${
                              isPingRecent(sim.last_ping) 
                                ? 'bg-emerald-500 shadow-emerald-500/20' 
                                : 'bg-rose-500 shadow-rose-500/20 animate-pulse'
                            }`} 
                          />
                          
                          <div className="flex flex-col">
                            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-tighter">
                              {isPingRecent(sim.last_ping) ? 'Healthy' : 'Stale'}
                            </span>
                            <span className="text-[9px] text-muted-foreground font-mono">
                              {formatPing(sim.last_ping)}
                            </span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminAnalyticsPage;
