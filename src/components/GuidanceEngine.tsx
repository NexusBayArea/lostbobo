import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useControlRoomStore } from '../store/controlRoomStore';
import { Compass, Info, CheckCircle, ExternalLink } from 'lucide-react';

export const GuidanceEngine: React.FC = () => {
  const insights = useControlRoomStore((state) => state.insights);

  return (
    <div className="bg-slate-950/50 border border-slate-800 rounded-lg p-4 h-full flex flex-col">
      <div className="flex items-center gap-2 mb-4 text-cyan-500 border-b border-slate-800 pb-2">
        <Compass className="w-4 h-4" />
        <h3 className="text-sm font-mono tracking-tighter uppercase font-bold">OPERATOR GUIDANCE</h3>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 custom-scrollbar">
        <AnimatePresence>
          {insights.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-700 font-mono text-xs opacity-50 uppercase tracking-widest text-center px-4">
              NAVIGATOR STANDBY...<br/>AWAITING PHYSICS DRIFT
            </div>
          ) : (
            insights.map((insight) => (
              <motion.div
                key={insight.insight_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-slate-900 border-l-2 border-cyan-500 p-3 rounded-r shadow-lg relative overflow-hidden group"
              >
                <div className="absolute top-0 right-0 p-1 opacity-20 group-hover:opacity-100 transition-opacity">
                  <ExternalLink className="w-3 h-3 text-cyan-400 cursor-pointer" />
                </div>
                
                <div className="flex items-start gap-3">
                  <div className="bg-cyan-500/10 p-1 rounded">
                    <Info className="w-3 h-3 text-cyan-400" />
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-cyan-500 mb-1">STRATEGY_RECOMMENDATION</div>
                    <p className="text-xs text-slate-300 mb-3 leading-relaxed">
                      {insight.message}
                    </p>
                    
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 bg-emerald-500/5 p-2 rounded border border-emerald-500/10">
                        <CheckCircle className="w-3 h-3" />
                        ACTION: {insight.recommended_action}
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      <div className="mt-4 flex items-center justify-between text-[9px] font-mono text-slate-500 uppercase tracking-tight opacity-50 space-x-4">
        <span className="flex items-center gap-1"><Info className="w-2 h-2" /> Persona: Directive</span>
        <span className="flex items-center gap-1 border-l border-slate-800 pl-4 font-bold text-cyan-700">Source: Enterprise Vault Verified</span>
      </div>
    </div>
  );
};
