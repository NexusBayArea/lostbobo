import { useState, useEffect } from 'react';
import { Cpu, Zap, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';

export function WakeGPU() {
  const { getToken } = useAuth();
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [warming, setWarming] = useState(false);

  const fetchReadiness = async () => {
    try {
      const token = await getToken();
      const data = await api.getFleetReadiness(token);
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch readiness:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReadiness();
    const interval = setInterval(fetchReadiness, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const handleWarm = async () => {
    setWarming(true);
    try {
      const token = await getToken();
      await api.warmPod(token);
      toast.success('GPU Warm-up initiated. Ready in ~90s.');
      fetchReadiness();
    } catch (error: any) {
      toast.error(error.message || 'Failed to warm GPU');
    } finally {
      setWarming(false);
    }
  };

  if (loading && !status) {
    return (
      <Card className="bg-slate-900 border-slate-800">
        <CardContent className="p-6 flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
        </CardContent>
      </Card>
    );
  }

  const isReady = status?.ready;
  const hasStoppedPods = status?.stopped_pods > 0;

  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className={`w-5 h-5 ${isReady ? 'text-cyan-400' : 'text-slate-400'}`} />
            <CardTitle className="text-white">GPU Fleet Readiness</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${isReady ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`} />
            <span className="text-xs font-mono text-slate-400 uppercase">
              {isReady ? 'System Primed' : 'On Standby'}
            </span>
          </div>
        </div>
        <CardDescription className="text-slate-400">
          Monitor and wake GPU instances for upcoming demonstrations.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Active Clusters</p>
            <p className="text-2xl font-mono text-white">{status?.running_pods || 0}</p>
          </div>
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
            <p className="text-[10px] uppercase font-bold text-slate-500 mb-1">Dormant Nodes</p>
            <p className="text-2xl font-mono text-white">{status?.stopped_pods || 0}</p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-4 bg-slate-950 rounded-xl border border-slate-800">
          {isReady ? (
            <CheckCircle2 className="w-5 h-5 text-cyan-400" />
          ) : (
            <AlertCircle className="w-5 h-5 text-amber-500" />
          )}
          <p className="text-sm text-slate-300">{status?.message}</p>
        </div>

        {!isReady && hasStoppedPods && (
          <Button
            onClick={handleWarm}
            disabled={warming}
            className="w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold"
          >
            {warming ? (
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
            ) : (
              <Zap className="w-4 h-4 mr-2" />
            )}
            WAKE GPU CLUSTER
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
