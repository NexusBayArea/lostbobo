import { motion } from 'framer-motion';
import { Play, Loader2, CheckCircle2, Clock, Cpu, Activity, Square, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RunControlPanelProps {
  onStartRun: () => void;
  onCancelRun: () => void;
  isRunning: boolean;
  numRuns: number;
  samplingMethod: string;
  activeParams: number;
  userBalance: number;
}

export function RunControlPanel({
  onStartRun,
  onCancelRun,
  isRunning,
  numRuns,
  samplingMethod,
  activeParams,
  userBalance,
}: RunControlPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="bg-slate-900 border border-slate-800 rounded-2xl p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-white">Run Control</h2>
          <p className="text-sm text-slate-400">Execute robustness analysis</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <Zap className="w-4 h-4 text-yellow-500" />
            <span className="text-sm font-medium text-yellow-500">${userBalance.toFixed(2)}</span>
          </div>
          {isRunning && (
            <span className="flex items-center gap-2 text-sm text-cyan-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              Running...
            </span>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-500 mb-1">
            <Activity className="w-4 h-4 text-cyan-500" />
            <span className="text-xs">Status</span>
          </div>
          <p className={cn(
            "text-lg font-semibold",
            isRunning ? "text-cyan-400" : "text-slate-300"
          )}>
            {isRunning ? 'Running' : 'Ready'}
          </p>
        </div>
        <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-500 mb-1">
            <Cpu className="w-4 h-4 text-cyan-500" />
            <span className="text-xs">Runs</span>
          </div>
          <p className="text-lg font-semibold text-white font-mono">{numRuns}</p>
        </div>
        <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-500 mb-1">
            <Clock className="w-4 h-4 text-cyan-500" />
            <span className="text-xs">Method</span>
          </div>
          <p className="text-lg font-semibold text-white">
            {samplingMethod.split(' ')[0]}
          </p>
        </div>
        <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-500 mb-1">
            <CheckCircle2 className="w-4 h-4 text-cyan-500" />
            <span className="text-xs">Params</span>
          </div>
          <p className="text-lg font-semibold text-white">{activeParams} active</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={onStartRun}
          disabled={isRunning}
          className={cn(
            'flex-1 flex items-center justify-center gap-2 px-6 py-4 rounded-xl font-medium transition-all',
            isRunning
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
              : 'bg-cyan-500 text-white hover:bg-cyan-600 hover:scale-[1.02] shadow-lg shadow-cyan-500/20'
          )}
        >
          {isRunning ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Running Analysis...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Start Robustness Analysis
            </>
          )}
        </button>

        {isRunning && (
          <button
            onClick={onCancelRun}
            className="flex items-center justify-center gap-2 px-6 py-4 bg-red-500/10 hover:bg-red-500/20 text-red-400 font-medium rounded-xl transition-all border border-red-500/20"
          >
            <Square className="w-5 h-5" />
            Cancel
          </button>
        )}
      </div>
    </motion.div>
  );
}
