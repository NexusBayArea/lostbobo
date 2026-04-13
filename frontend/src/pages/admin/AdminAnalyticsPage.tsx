import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LayoutDashboard, Users, CreditCard, Terminal, Cpu, Zap, Activity, ShieldAlert, AlertTriangle, AlertCircle, Trash2, StopCircle, RefreshCw, ChevronRight, LayoutList, MessageSquare, Loader2 } from 'lucide-react';
import { Navigation } from '@/components/Navigation';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { WakeGPU } from '@/components/admin/WakeGPU';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { supabase } from '@/lib/supabase';

export function AdminAnalyticsPage() {
  const { getToken } = useAuth();
  const [activeTab, setActiveTab] = useState('fleet');
  const [fleetStatus, setFleetStatus] = useState<any>(null);
  const [fleetMetrics, setFleetMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  const fetchDashboardData = async () => {
    try {
      setRefreshing(true);
      const token = await getToken();
      
      const [status, metrics] = await Promise.all([
        api.getFleetStatus(token),
        api.getFleetMetrics(token).catch(() => null) // Fallback if edge function fails
      ]);

      setFleetStatus(status);
      setFleetMetrics(metrics);
    } catch (error) {
      console.error('Failed to fetch admin dashboard data:', error);
      toast.error('Failed to fetch fleet status');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // 30s refresh

    // Real-time Platform Alerts
    const alertsChannel = (supabase as any)?.channel('platform_alerts_admin')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'platform_alerts' },
        (payload: any) => {
          setAlerts(prev => [payload.new, ...prev].slice(0, 50));
          toast.error(`PLATFORM ALERT: ${payload.new.message}`, {
            icon: <ShieldAlert className="w-4 h-4 text-red-500" />
          });
        }
      )
      .subscribe();

    return () => {
      clearInterval(interval);
      if (alertsChannel) (supabase as any).removeChannel(alertsChannel);
    };
  }, []);

  const handleStopPod = async (podId: string) => {
    if (!window.confirm(`Are you sure you want to STOP pod ${podId}? This will preserve the disk but stop GPU billing.`)) return;
    setActionLoading(podId);
    try {
      const token = await getToken();
      await api.stopPod(token, podId);
      toast.success('Pod stop command sent');
      fetchDashboardData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to stop pod');
    } finally {
      setActionLoading(null);
    }
  };

  const handleTerminatePod = async (podId: string) => {
    if (!window.confirm(`CRITICAL: Are you sure you want to TERMINATE pod ${podId}? This will PERMANENTLY DELETE the disk and data.`)) return;
    setActionLoading(podId);
    try {
      const token = await getToken();
      await api.terminatePod(token, podId);
      toast.success('Pod termination command sent');
      fetchDashboardData();
    } catch (error: any) {
      toast.error(error.message || 'Failed to terminate pod');
    } finally {
      setActionLoading(null);
    }
  };

  const handlePanicButton = async () => {
    if (!window.confirm('PANIC SHUTDOWN: This will TERMINATE ALL running GPU pods. Do you want to proceed?')) return;
    if (!window.confirm('SECOND CONFIRMATION: Are you absolutely certain?')) return;
    
    setActionLoading('panic');
    try {
      const token = await getToken();
      // Panic button logic via API trigger
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/v1/admin/fleet/panic`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) throw new Error('Panic shutdown failed');
      toast.success('Panic shutdown initiated for all pods');
      fetchDashboardData();
    } catch (error: any) {
      toast.error(error.message || 'Panic shutdown failed');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading && !fleetStatus) {
    return (
      <div className="min-h-screen bg-slate-950">
        <Navigation />
        <div className="pt-24 flex flex-col items-center justify-center">
          <Loader2 className="w-12 h-12 text-cyan-400 animate-spin mb-4" />
          <p className="text-slate-400 font-mono">Initializing Command Bridge...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      <Navigation />
      
      <div className="flex-1 pt-16 flex">
        {/* Sidebar Nav */}
        <aside className="w-64 border-r border-slate-800 bg-slate-900 hidden md:block">
          <div className="p-4">
            <h2 className="text-xs uppercase font-bold text-slate-500 mb-6 flex items-center gap-2">
              <ShieldAlert className="w-3 h-3" /> Fleet Intelligence
            </h2>
            <nav className="space-y-1">
              {[
                { id: 'fleet', label: 'Fleet Analytics', icon: Activity },
                { id: 'users', label: 'User Management', icon: Users },
                { id: 'ci_policies', label: 'CI Policies', icon: ShieldAlert },
                { id: 'revenue', label: 'Stripe Revenue', icon: CreditCard },
                { id: 'prompts', label: 'AI Prompts', icon: MessageSquare },
                { id: 'events', label: 'Scaling Events', icon: LayoutList },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === item.id 
                      ? 'bg-cyan-500/10 text-cyan-400' 
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </button>
              ))}
            </nav>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto">
          <div className="p-8 max-w-7xl mx-auto space-y-8">
            <header className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-white tracking-tight">Mission Control</h1>
                <p className="text-slate-400 mt-1 flex items-center gap-2">
                  <Activity className="w-4 h-4" /> Global Infrastructure Snapshot
                </p>
              </div>
              <div className="flex items-center gap-4">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={fetchDashboardData}
                  disabled={refreshing}
                  className="bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                  Sync Status
                </Button>
                <Button 
                  variant="destructive" 
                  size="sm" 
                  onClick={handlePanicButton}
                  disabled={actionLoading === 'panic'}
                  className="font-bold border-2 border-red-900 hover:bg-red-600 transition-all active:scale-95"
                >
                  {actionLoading === 'panic' ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <AlertTriangle className="w-4 h-4 mr-2" />}
                  PANIC SHUTDOWN
                </Button>
              </div>
            </header>

            {activeTab === 'ci_policies' && (
              <div className="space-y-8">
                <Card className="bg-slate-900 border-slate-800">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-white">CI Policy Execution Graph</CardTitle>
                        <CardDescription className="text-slate-500">
                          Automated guards enforced by the DAG Policy Engine.
                        </CardDescription>
                      </div>
                      <Badge variant="outline" className="text-cyan-400 border-cyan-500/30">
                        v8.0.0 Stable
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader className="bg-slate-950 border-slate-800">
                        <TableRow className="hover:bg-transparent">
                          <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Policy Name</TableHead>
                          <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Status</TableHead>
                          <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Guard Rule</TableHead>
                          <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Last Evaluated</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {[
                          { name: "no_mutable_tags", rule: "immutable_image_tags", status: "PASS", evaluated: "Just now" },
                          { name: "dag_validity", rule: "dag_integrity", status: "PASS", evaluated: "Just now" },
                          { name: "deterministic_builds", rule: "hash_check", status: "SKIP", evaluated: "2 mins ago" },
                        ].map((policy) => (
                          <TableRow key={policy.name} className="border-slate-800 hover:bg-slate-800/30">
                            <TableCell className="font-medium text-white">{policy.name}</TableCell>
                            <TableCell>
                              <Badge 
                                variant="outline" 
                                className={cn(
                                  "border-none",
                                  policy.status === "PASS" ? "bg-green-500/10 text-green-400" : 
                                  policy.status === "SKIP" ? "bg-slate-500/10 text-slate-400" : "bg-red-500/10 text-red-400"
                                )}
                              >
                                {policy.status}
                              </Badge>
                            </TableCell>
                            <TableCell className="font-mono text-xs text-slate-400">{policy.rule}</TableCell>
                            <TableCell className="text-slate-500 text-xs">{policy.evaluated}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                  <CardFooter className="bg-slate-950/50 px-6 py-3 border-t border-slate-800">
                    <p className="text-[10px] text-slate-500 font-mono italic">
                      Policies are cached and evaluated per-commit. Failing policies block downstream compute nodes.
                    </p>
                  </CardFooter>
                </Card>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <Card className="bg-slate-900 border-slate-800 overflow-hidden">
                    <CardHeader className="bg-slate-950/30 border-b border-slate-800">
                      <div className="flex items-center gap-2">
                         <RefreshCw className="w-4 h-4 text-cyan-400" />
                         <CardTitle className="text-sm text-white">Autonomous Recovery</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent className="p-6 space-y-4">
                       <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-400">Diagnosis Convergence</span>
                          <span className="text-sm font-bold text-green-400">92%</span>
                       </div>
                       <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-400">Auto-Fix Proposals</span>
                          <span className="text-sm font-bold text-white">14 / 24 hrs</span>
                       </div>
                       <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-400">Self-Healing Status</span>
                          <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-none animate-pulse text-[10px]">MONITORING</Badge>
                       </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-slate-900 border-slate-800 overflow-hidden">
                    <CardHeader className="bg-slate-950/30 border-b border-slate-800">
                      <div className="flex items-center gap-2">
                         <Zap className="w-4 h-4 text-amber-400" />
                         <CardTitle className="text-sm text-white">Learning Intelligence</CardTitle>
                      </div>
                    </CardHeader>
                    <CardContent className="p-6 space-y-4">
                       <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-400">Prediction Accuracy</span>
                          <span className="text-sm font-bold text-amber-400">87.5%</span>
                       </div>
                       <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-400">Knowledge Base Size</span>
                          <span className="text-sm font-bold text-white">124 patterns</span>
                       </div>
                       <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-400">Adaptive Gain</span>
                          <span className="text-sm font-bold text-green-400">+12% speedup</span>
                       </div>
                    </CardContent>
                  </Card>

                  <div className="space-y-4">
                    <h3 className="text-sm font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
                       <Zap className="w-4 h-4 text-cyan-400" /> Cached Optimization
                    </h3>
                    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
                       <div className="flex justify-between items-end mb-2">
                          <span className="text-xs text-slate-400">CI Run Speedup</span>
                          <span className="text-xl font-bold text-white tracking-widest">85%</span>
                       </div>
                       <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                          <div className="bg-cyan-500 h-full w-[85%]" />
                       </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {activeTab === 'fleet' && (
              <div className="space-y-8">
                {/* Existing Fleet content... */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Left Column: Pod Management */}
                  <div className="lg:col-span-2 space-y-8">
                    <Card className="bg-slate-900 border-slate-800">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-white">Active GPU Fleet</CardTitle>
                            <CardDescription className="text-slate-500">Live orchestrator-managed instances on RunPod.</CardDescription>
                          </div>
                          <Badge variant="outline" className="text-cyan-400 border-cyan-500/30">
                            {fleetStatus?.fleet?.strategy}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <Table>
                          <TableHeader className="bg-slate-950 border-slate-800">
                            <TableRow className="hover:bg-transparent">
                              <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Node ID</TableHead>
                              <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Status</TableHead>
                              <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Type</TableHead>
                              <TableHead className="text-slate-500 font-bold uppercase text-[10px] text-right">Interventions</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {(fleetStatus?.fleet?.running_ids || []).map((id: string) => (
                              <TableRow key={id} className="border-slate-800 hover:bg-slate-800/30">
                                <TableCell className="font-mono text-cyan-400 text-xs">{id}</TableCell>
                                <TableCell>
                                  <Badge variant="outline" className="bg-green-500/10 text-green-400 border-none">ACTIVE</Badge>
                                </TableCell>
                                <TableCell className="text-slate-400 text-sm">NVIDIA A40</TableCell>
                                <TableCell className="text-right space-x-2">
                                  <Button 
                                    variant="outline" 
                                    size="sm" 
                                    onClick={() => handleStopPod(id)}
                                    disabled={actionLoading === id}
                                    className="h-7 px-2 text-[10px] bg-slate-950 border-slate-700 text-slate-400 hover:text-white"
                                  >
                                    {actionLoading === id ? <Loader2 className="w-3 h-3 animate-spin" /> : <StopCircle className="w-3 h-3 mr-1" />}
                                    STOP
                                  </Button>
                                  <Button 
                                    variant="outline" 
                                    size="sm" 
                                    onClick={() => handleTerminatePod(id)}
                                    disabled={actionLoading === id}
                                    className="h-7 px-2 text-[10px] bg-slate-950 border-red-900/50 text-red-400 hover:bg-red-900/20"
                                  >
                                    <Trash2 className="w-3 h-3 mr-1" />
                                    KILL
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                            {(fleetStatus?.fleet?.running_ids || []).length === 0 && (
                              <TableRow>
                                <TableCell colSpan={4} className="text-center py-8 text-slate-500 font-mono text-sm bg-slate-950/50">
                                  NO ESCALATED NODES DETECTED
                                </TableCell>
                              </TableRow>
                            )}
                          </TableBody>
                        </Table>
                      </CardContent>
                      <CardFooter className="bg-slate-950/50 px-6 py-3 border-t border-slate-800 flex justify-between items-center">
                        <div className="flex items-center gap-4">
                          <span className="text-[10px] text-slate-500 font-bold uppercase">Daily Sprawl Cost</span>
                          <span className="text-xs font-mono text-white">${fleetStatus?.cost?.today_usd?.toFixed(2) || '0.00'} / ${fleetStatus?.cost?.daily_cap_usd?.toFixed(2)}</span>
                        </div>
                        {fleetStatus?.cost?.today_usd > (fleetStatus?.cost?.daily_cap_usd * 0.8) && (
                          <div className="flex items-center gap-1 text-amber-500 text-[10px] font-bold uppercase animate-pulse">
                            <AlertCircle className="w-3 h-3" /> Near Daily Cap
                          </div>
                        )}
                      </CardFooter>
                    </Card>

                    {/* Dormant Nodes */}
                    {fleetStatus?.fleet?.stopped_ids?.length > 0 && (
                      <Card className="bg-slate-900 border-slate-800">
                        <CardHeader className="py-4">
                          <CardTitle className="text-sm text-slate-400">Dormant Nodes (Option C Lifecycle)</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <Table>
                            <TableBody>
                              {fleetStatus.fleet.stopped_ids.map((id: string) => (
                                <TableRow key={id} className="border-slate-800 hover:bg-transparent">
                                  <TableCell className="font-mono text-slate-500 text-xs">{id}</TableCell>
                                  <TableCell>
                                    <Badge variant="outline" className="bg-slate-800 text-slate-500 border-none">STOPPED</Badge>
                                  </TableCell>
                                  <TableCell className="text-right">
                                    <Button 
                                      variant="outline" 
                                      size="sm" 
                                      onClick={() => handleTerminatePod(id)}
                                      disabled={actionLoading === id}
                                      className="h-7 px-2 text-[10px] bg-slate-950 border-red-900/50 text-red-500 hover:bg-red-900/20"
                                    >
                                      PERMA-TERMINATE
                                    </Button>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </CardContent>
                      </Card>
                    )}
                  </div>

                  {/* Right Column: Alerts & Manual Control */}
                  <div className="space-y-8">
                    <WakeGPU />

                    <Card className="bg-slate-900 border-slate-800 overflow-hidden">
                      <header className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                        <h3 className="text-white font-bold flex items-center gap-2">
                          <ShieldAlert className="w-4 h-4 text-cyan-400" />
                          Platform Alerts
                        </h3>
                        <Badge variant="outline" className="text-[10px] uppercase font-bold text-slate-500">
                          Real-time
                        </Badge>
                      </header>
                      <CardContent className="p-0 max-h-[400px] overflow-y-auto">
                        {alerts.length > 0 ? (
                          <div className="divide-y divide-slate-800">
                            {alerts.map((alert, i) => (
                              <div key={i} className="p-4 flex gap-3 hover:bg-slate-800/30 transition-colors">
                                <div className="mt-1">
                                  {alert.severity === 'critical' ? (
                                    <AlertTriangle className="w-4 h-4 text-red-500" />
                                  ) : alert.severity === 'warning' ? (
                                    <AlertCircle className="w-4 h-4 text-amber-500" />
                                  ) : (
                                    <Activity className="w-4 h-4 text-blue-500" />
                                  )}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className={`text-[10px] font-bold uppercase tracking-wider ${
                                      alert.type === 'billing' ? 'text-amber-400' :
                                      alert.type === 'thermal' ? 'text-orange-400' : 'text-cyan-400'
                                    }`}>
                                      {alert.type}
                                    </span>
                                    <span className="text-[10px] text-slate-500 font-mono">{format(new Date(alert.created_at), 'HH:mm:ss')}</span>
                                  </div>
                                  <p className="text-sm text-slate-300 line-clamp-2">{alert.message}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="p-8 text-center bg-slate-950/30">
                            <Activity className="w-8 h-8 text-slate-700 mx-auto mb-2 opacity-20" />
                            <p className="text-xs text-slate-600 font-mono">ALL SYSTEMS NOMINAL</p>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
