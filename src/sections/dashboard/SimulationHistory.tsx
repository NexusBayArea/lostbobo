import { format } from 'date-fns';
import { motion } from 'framer-motion';
import { Play, CheckCircle2, XCircle, Loader2, Download, Eye, ExternalLink } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { SimulationTelemetry } from '@/hooks/useSimulations';

interface SimulationHistoryProps {
  simulations: SimulationTelemetry[];
  loading: boolean;
  onViewDetails: (sim: SimulationTelemetry) => void;
}

export function SimulationHistory({ simulations, loading, onViewDetails }: SimulationHistoryProps) {
  if (loading && simulations.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
        <p className="text-slate-500 font-mono text-sm uppercase tracking-widest">Hydrating History...</p>
      </div>
    );
  }

  if (simulations.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
        <Play className="w-12 h-12 text-slate-800 mx-auto mb-4" />
        <h3 className="text-white font-bold text-lg mb-2">No Simulations Found</h3>
        <p className="text-slate-500 max-w-xs mx-auto">
          Start your first Monte Carlo analysis to see real-time solver telemetry here.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
         <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Play className="w-4 h-4 text-cyan-400" /> Recent Simulations
         </h2>
         <Badge variant="outline" className="border-slate-800 text-[10px] text-slate-500 font-mono">
            LIVE SYNC ACTIVE
         </Badge>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader className="bg-slate-950/50">
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Reference</TableHead>
              <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Scenario</TableHead>
              <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Status</TableHead>
              <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Telemetry</TableHead>
              <TableHead className="text-slate-500 font-bold uppercase text-[10px]">Created</TableHead>
              <TableHead className="text-slate-500 font-bold uppercase text-[10px] text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {simulations.map((sim) => (
              <TableRow key={sim.id} className="border-slate-800 hover:bg-slate-800/30 transition-colors group">
                <TableCell className="font-mono text-xs text-slate-500">
                  {sim.job_id ? sim.job_id.substring(0, 8) : 'PENDING'}
                </TableCell>
                <TableCell className="font-medium text-white max-w-[150px] truncate">
                  {sim.scenario_name || 'Baseline Run'}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    {sim.status === 'completed' ? (
                      <Badge variant="outline" className="bg-green-500/10 text-green-400 border-none px-2 py-0.5">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> COMPLETED
                      </Badge>
                    ) : sim.status === 'failed' ? (
                      <Badge variant="outline" className="bg-red-500/10 text-red-400 border-none px-2 py-0.5">
                        <XCircle className="w-3 h-3 mr-1" /> FAILED
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-none px-2 py-0.5 animate-pulse">
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" /> {sim.status.toUpperCase()}
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-4">
                    <div className="flex flex-col gap-1">
                       <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Progress</span>
                       <div className="w-24 h-1 bg-slate-800 rounded-full overflow-hidden">
                          <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${sim.progress}%` }}
                            className={`h-full ${sim.status === 'failed' ? 'bg-red-500' : 'bg-cyan-400'}`} 
                          />
                       </div>
                    </div>
                    {sim.thermal_drift > 0 && (
                       <div className="flex flex-col gap-1">
                          <span className="text-[10px] text-orange-500 font-bold uppercase tracking-widest">Drift</span>
                          <span className="text-[10px] font-mono text-orange-400">{(sim.thermal_drift * 100).toFixed(2)}%</span>
                       </div>
                    )}
                 </div>
                </TableCell>
                <TableCell className="text-slate-500 text-xs font-mono">
                  {format(new Date(sim.created_at), 'MMM d, HH:mm')}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 text-slate-400 hover:text-cyan-400 hover:bg-cyan-400/10"
                      onClick={() => onViewDetails(sim)}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 text-slate-400 hover:text-white"
                      disabled={sim.status !== 'completed'}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
