import { motion } from 'framer-motion';
import { Activity, ShieldAlert, Cpu, Zap, Activity as Sparkles, LayoutGrid } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useSimulations } from '@/hooks/useSimulations';
import { useAuth } from '@/hooks/useAuth';

export function ActiveSimulations() {
  const { user } = useAuth();
  const { simulations, loading } = useSimulations(user?.id);
  const activeSims = simulations.filter(s => s.status === 'running' || s.status === 'auditing');

  return (
    <Card className="bg-slate-900 border-slate-800 shadow-2xl h-full flex flex-col">
       <CardHeader className="py-4 border-b border-slate-800 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <LayoutGrid className="w-4 h-4 text-amber-500" />
            <CardTitle className="text-xs uppercase font-bold text-slate-400 font-mono">Live Solver Nodes</CardTitle>
          </div>
          <Badge variant="outline" className="border-amber-500/30 text-amber-400 bg-amber-400/5 px-1.5 font-mono text-[10px]">
            {activeSims.length} NODES
          </Badge>
       </CardHeader>
       <CardContent className="flex-1 p-0 overflow-y-auto">
          {loading && activeSims.length === 0 ? (
             <div className="p-8 text-center text-slate-600 animate-pulse text-[10px] uppercase font-bold">Scanning Flux Grids...</div>
          ) : activeSims.length === 0 ? (
             <div className="p-12 text-center text-slate-700 italic text-[10px] uppercase">No Active Solver Activity Detected</div>
          ) : (
             <div className="p-4 space-y-4">
                {activeSims.map((sim, i) => (
                   <div key={sim.id} className="p-4 bg-slate-950/50 rounded-xl border border-slate-800 group hover:border-cyan-500/30 transition-all shadow-lg active:scale-95 cursor-pointer">
                      <div className="flex items-center justify-between mb-3">
                         <div className="flex items-center gap-3">
                            <motion.div 
                              animate={{ scale: [1, 1.2, 1], opacity: [1, 0.5, 1] }} 
                              transition={{ duration: 1.5, repeat: Infinity }}
                              className="w-2 h-2 rounded-full bg-cyan-400" 
                            />
                            <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-tighter">#{sim.id.substring(0, 8)}</span>
                         </div>
                         <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-none px-1.5 py-0 h-4 text-[9px] font-bold uppercase tracking-widest">{sim.status}</Badge>
                      </div>
                      <div className="space-y-4">
                         <div className="flex items-center justify-between">
                             <div className="text-xs font-bold text-white group-hover:text-cyan-400 transition-colors truncate max-w-[140px] uppercase">{sim.scenario_name}</div>
                             <div className="text-[10px] font-mono text-slate-500">{sim.progress}%</div>
                         </div>
                         <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                            <motion.div 
                               initial={{ width: 0 }}
                               animate={{ width: `${sim.progress}%` }}
                               className="h-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)]" 
                            />
                         </div>
                         <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800/50">
                            <div>
                               <p className="text-[8px] uppercase font-bold text-slate-600 mb-1">Thermal Drift</p>
                               <p className={`text-[10px] font-mono ${sim.thermal_drift > 0.05 ? 'text-orange-400' : 'text-slate-400'}`}>{(sim.thermal_drift * 100).toFixed(2)}%</p>
                            </div>
                            <div className="text-right">
                               <p className="text-[8px] uppercase font-bold text-slate-600 mb-1">Pressure Spike</p>
                               <p className={`text-[10px] font-mono ${sim.pressure_spike ? 'text-red-500' : 'text-slate-400'}`}>{sim.pressure_spike ? 'DETECTED' : 'SYSTEM NOMINAL'}</p>
                            </div>
                         </div>
                      </div>
                   </div>
                ))}
             </div>
          )}
       </CardContent>
    </Card>
  );
}
