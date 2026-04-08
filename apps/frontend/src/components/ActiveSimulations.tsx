import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Play, Clock, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { useSimulations } from '@/hooks/useSimulations';
import { useAuth } from '@/hooks/useAuth';

export function ActiveSimulations() {
  const { user } = useAuth();
  const { simulations, loading } = useSimulations(user?.id);

  const activeSims = simulations.filter(s => 
    s.status === 'running' || s.status === 'auditing' || s.status === 'queued'
  ).slice(0, 5);

  return (
    <Card className="h-full bg-slate-900/80 border-slate-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2">
          <Play className="w-3 h-3 text-cyan-400" />
          Active Simulations
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
          </div>
        ) : activeSims.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs">No active simulations</div>
        ) : (
          <div className="space-y-2">
            {activeSims.map((sim) => (
              <div key={sim.id} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono text-white truncate">{sim.name || 'Untitled'}</span>
                  <Badge variant="outline" className="text-[8px] h-5">
                    {sim.status.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 text-[8px] text-slate-500">
                  <Clock className="w-2 h-2" />
                  <span>{new Date(sim.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
