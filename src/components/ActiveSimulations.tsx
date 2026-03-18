import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useControlRoomStore } from '../store/controlRoomStore';
import { Activity, Play, Square, Zap } from 'lucide-react';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

export const ActiveSimulations: React.FC = () => {
  const activeSims = useControlRoomStore((state) => state.activeSimulations);

  return (
    <div className="flex flex-col h-full bg-slate-900/50 border border-slate-800 rounded-lg p-4 backdrop-blur-md overflow-hidden">
      <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-2">
        <h2 className="text-lg font-mono flex items-center gap-2 text-cyan-400">
          <Activity className="w-5 h-5" />
          DECISION PANEL: ACTIVE FLEET
        </h2>
        <Badge variant="outline" className="font-mono text-cyan-500 border-cyan-500/30">
          {activeSims.length} NODES DISPATCHED
        </Badge>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
        <AnimatePresence mode="popLayout">
          {activeSims.length === 0 ? (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="h-full flex flex-col items-center justify-center text-slate-500 font-mono text-sm opacity-50"
            >
              <Zap className="w-12 h-12 mb-2 stroke-1" />
              WAITING FOR DISPATCH...
            </motion.div>
          ) : (
            activeSims.map((sim) => (
              <motion.div
                key={sim.run_id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="group relative bg-slate-950/80 border border-slate-800 rounded p-4 hover:border-cyan-500/50 transition-colors"
              >
                {/* Solver Health Indicator */}
                <div className={`absolute top-0 right-0 w-1 h-full rounded-r ${
                  sim.solver_health === 'optimal' ? 'bg-cyan-500' : 
                  sim.solver_health === 'stiff' ? 'bg-amber-500' : 'bg-red-500 animate-pulse'
                }`} />

                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="text-xs font-mono text-slate-500 uppercase tracking-widest mb-1">
                      RUN_ID: {sim.run_id}
                    </div>
                    <div className="text-sm font-bold text-slate-200 uppercase tracking-tight">
                      {sim.model.replace(/_/g, ' ')}
                    </div>
                  </div>
                  <Badge className={`${
                    sim.solver_health === 'optimal' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' : 
                    sim.solver_health === 'stiff' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 
                    'bg-red-500/10 text-red-500 border-red-500/20'
                  } font-mono text-[10px]`}>
                    SOLVER: {sim.solver_health}
                  </Badge>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 uppercase">
                    <span>Convergence Alpha</span>
                    <span>{sim.runtime_sec.toFixed(1)}s</span>
                  </div>
                  <Progress value={45} className="h-1 bg-slate-800" />
                </div>

                <div className="mt-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button size="sm" variant="outline" className="h-7 text-[10px] font-mono border-slate-700 hover:bg-red-950 hover:text-red-500 hover:border-red-900">
                    <Square className="w-3 h-3 mr-1" /> INTERCEPT
                  </Button>
                  <Button size="sm" variant="outline" className="h-7 text-[10px] font-mono border-slate-700 hover:bg-cyan-950 hover:text-cyan-400 hover:border-cyan-900">
                    <Zap className="w-3 h-3 mr-1" /> BOOST
                  </Button>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800 group cursor-pointer hover:bg-cyan-500/5 transition-colors p-2 rounded">
        <div className="flex items-center gap-3 text-xs font-mono text-slate-400">
          <div className="p-1.5 bg-slate-900 rounded border border-slate-800">
            <Play className="w-4 h-4 text-cyan-500" />
          </div>
          <div>
            <div className="text-[10px] text-slate-500">QUICK COMMAND</div>
            <div className="text-slate-200">LAUNCH NEW THERMAL NODE</div>
          </div>
        </div>
      </div>
    </div>
  );
};
