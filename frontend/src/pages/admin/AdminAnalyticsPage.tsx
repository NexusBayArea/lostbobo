import React, { useState, useEffect } from 'react';
import { useSimulations } from '../../hooks/useSimulations';
import { useAuth } from '../../hooks/useAuth';
import { supabase } from '../../lib/supabase';
import { 
  Copy, Check, Activity, LayoutDashboard, 
  Terminal, ShieldAlert, ChevronRight, Inbox 
} from 'lucide-react';

// --- Sub-Component: Copy-to-Clipboard ---
const CopyButton = ({ text }: { text: string }) => {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button onClick={handleCopy} className="ml-2 text-muted-foreground hover:text-primary transition-colors">
      {copied ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
    </button>
  );
};

// --- Sub-Component: Breadcrumbs ---
const Breadcrumbs = ({ paths }: { paths: string[] }) => (
  <nav className="flex items-center space-x-2 text-sm text-muted-foreground mb-6">
    {paths.map((path, i) => (
      <React.Fragment key={path}>
        <span className="capitalize hover:text-foreground cursor-pointer">{path}</span>
        {i < paths.length - 1 && <ChevronRight size={14} />}
      </React.Fragment>
    ))}
  </nav>
);

export const AdminAnalyticsPage = () => {
  const { user } = useAuth();
  const { simulations, loading } = useSimulations(user?.id || '');
  const [fleetMetrics, setFleetMetrics] = useState({ active_pods: 0, hourly_spend_usd: '0.00' });
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const fetchMetrics = async () => {
      const { data } = await supabase.functions.invoke('get-fleet-metrics');
      if (data) setFleetMetrics(data);
    };
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Mobile/Tablet Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden" 
          onClick={() => setSidebarOpen(false)} 
        />
      )}

      {/* Responsive Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-sidebar border-r border-border 
        transition-transform duration-300 transform 
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="p-6 flex flex-col h-full">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-8 h-8 bg-primary rounded flex items-center justify-center text-primary-foreground font-bold">S</div>
            <h2 className="text-xl font-bold tracking-tight">SimHPC</h2>
          </div>

          <nav className="flex-1 space-y-2">
            <button className="flex items-center gap-3 w-full px-3 py-2 rounded-md bg-accent text-accent-foreground">
              <LayoutDashboard size={18} /> <span>Fleet Analytics</span>
            </button>
            <button className="flex items-center gap-3 w-full px-3 py-2 rounded-md hover:bg-accent/50 transition-colors">
              <Terminal size={18} /> <span>Live Logs</span>
            </button>
          </nav>

          {/* System Heartbeat (Port 8080) */}
          <div className="mt-auto p-3 bg-muted rounded-lg border border-border">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] uppercase font-bold text-muted-foreground">Gateway: 8080</span>
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <p className="text-xs text-muted-foreground">Cluster Healthy</p>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-4 lg:p-8">
        <div className="flex items-center justify-between lg:block">
          <button 
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 -ml-2 text-muted-foreground"
          >
            <Activity size={24} />
          </button>
          <Breadcrumbs paths={['admin', 'fleet_analytics']} />
        </div>

        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Fleet Analytics</h1>
          <p className="text-muted-foreground">Real-time resource allocation and job telemetry.</p>
        </header>

        {/* Empty State Logic */}
        {simulations.length === 0 && !loading ? (
          <div className="flex flex-col items-center justify-center h-64 border-2 border-dashed border-border rounded-xl bg-card/50">
            <Inbox className="w-12 h-12 text-muted-foreground mb-4 opacity-20" />
            <h3 className="text-lg font-medium">No Active Simulations</h3>
            <p className="text-muted-foreground mb-6 text-sm text-center max-w-xs">
              Provisioning new compute nodes is required to see live telemetry data.
            </p>
            <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90">
              Launch Fleet Node
            </button>
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl overflow-hidden shadow-sm">
             <table className="w-full text-left text-sm">
                <thead className="bg-muted/50 border-b border-border text-muted-foreground">
                  <tr>
                    <th className="px-6 py-4 font-medium">Job ID</th>
                    <th className="px-6 py-4 font-medium">Status</th>
                    <th className="px-6 py-4 font-medium">Telemetry</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {simulations.map(sim => (
                    <tr key={sim.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4 font-mono flex items-center">
                        {sim.job_id.substring(0, 8)}...
                        <CopyButton text={sim.job_id} />
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                          {sim.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                          <div 
                            className="bg-primary h-full transition-all duration-500 ease-out" 
                            style={{ width: `${sim.progress}%` }} 
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
             </table>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminAnalyticsPage;
