import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Play, Loader2, CheckCircle2, Clock, Cpu, Activity, X, Zap, ShieldCheck, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RunControlPanelProps {
  onStartRun: (config: { method: string; numRuns: number }) => void;
  onCancelRun: () => void;
  isRunning: boolean;
  numRuns: number;
  samplingMethod: string;
  activeParams: number;
  remainingRuns: number;
}

export function RunControlPanel({ 
  onStartRun, 
  onCancelRun,
  isRunning,
  numRuns: initialNumRuns,
  samplingMethod: initialMethod,
  activeParams,
  remainingRuns = 0
}: RunControlPanelProps) {
  const [method, setMethod] = useState<'lhs' | 'sobol'>(
    initialMethod === 'sobol' ? 'sobol' : 'lhs'
  );
  const [baseN, setBaseN] = useState(method === 'sobol' ? 32 : 15);

  // Calculate required runs based on method
  const requiredRuns = useMemo(() => {
    const D = activeParams;
    return method === 'sobol' ? baseN * (D + 2) : baseN;
  }, [method, baseN, activeParams]);

  // Backend currently tracks "runs" as the unit of limit
  const estimatedCost = 1; // 1 run from the weekly quota
  const canAfford = remainingRuns >= estimatedCost;

  const handleInitialize = () => {
    onStartRun({
      method: method === 'sobol' ? 'sobol' : 'latin_hypercube',
      numRuns: baseN
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-xl"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Run Control</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Configure and execute analysis</p>
        </div>
        {isRunning && (
          <span className="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400 font-medium">
            <Loader2 className="w-4 h-4 animate-spin" />
            Live Execution
          </span>
        )}
      </div>

      {/* Method Selection */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <button 
          onClick={() => setMethod('lhs')}
          disabled={isRunning}
          className={cn(
            "p-4 rounded-xl border-2 transition-all text-left",
            method === 'lhs' 
              ? "bg-blue-50 dark:bg-blue-900/20 border-blue-500 dark:border-blue-400" 
              : "bg-slate-50 dark:bg-slate-800 border-transparent hover:border-slate-300 dark:hover:border-slate-600"
          )}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="font-bold text-slate-900 dark:text-white">LHS Sweep</span>
            {method === 'lhs' && <CheckCircle2 className="w-4 h-4 text-blue-500" />}
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-400 italic">Standard Robustness Analysis</span>
        </button>
        <button 
          onClick={() => setMethod('sobol')}
          disabled={isRunning}
          className={cn(
            "p-4 rounded-xl border-2 transition-all text-left",
            method === 'sobol' 
              ? "bg-purple-50 dark:bg-purple-900/20 border-purple-500 dark:border-purple-400 shadow-[0_0_20px_rgba(168,85,247,0.15)]" 
              : "bg-slate-50 dark:bg-slate-800 border-transparent hover:border-slate-300 dark:hover:border-slate-600"
          )}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              Sobol GSA <ShieldCheck size={14} className="text-purple-500 dark:text-purple-400" />
            </span>
            {method === 'sobol' && <CheckCircle2 className="w-4 h-4 text-purple-500" />}
          </div>
          <span className="text-xs text-slate-500 dark:text-slate-400 italic">Enterprise Interaction Sensitivity</span>
        </button>
      </div>

      {/* Stats/Cost Grid */}
      <div className="bg-slate-50 dark:bg-slate-950 p-5 rounded-xl border border-slate-200 dark:border-slate-800 mb-6">
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-1">
            <span className="text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider font-semibold">Required Runs</span>
            <p className="text-xl font-mono font-bold text-slate-900 dark:text-white">{requiredRuns}</p>
          </div>
          <div className="space-y-1 text-right">
            <span className="text-slate-500 dark:text-slate-400 text-xs uppercase tracking-wider font-semibold">Quota Usage</span>
            <p className={cn(
              "text-xl font-mono font-bold",
              canAfford ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"
            )}>
              1 <span className="text-xs">Run</span>
            </p>
          </div>
        </div>
      </div>

      {/* Sobol-Specific Warning */}
      {method === 'sobol' && !isRunning && (
        <div className="flex gap-3 p-4 bg-purple-50 dark:bg-purple-900/20 border border-purple-100 dark:border-purple-500/30 rounded-xl mb-6">
          <AlertCircle className="text-purple-600 dark:text-purple-400 shrink-0" size={20} />
          <div>
            <p className="text-sm font-bold text-purple-900 dark:text-purple-300">Enterprise Sensitivity Mode</p>
            <p className="text-xs text-purple-700 dark:text-purple-400 mt-0.5">
              Sobol GSA identifies complex multi-variable interactions. 
              Estimated completion: <strong>~{Math.max(1, Math.round(requiredRuns / 8))} mins</strong> on A40 GPU.
            </p>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-4">
        {!isRunning ? (
          <div className="w-full space-y-3">
            <button 
              onClick={handleInitialize}
              disabled={!canAfford}
              className={cn(
                "w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all text-lg",
                canAfford 
                  ? "bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:scale-[1.02] shadow-lg shadow-slate-900/10" 
                  : "bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-600 cursor-not-allowed"
              )}
            >
              {canAfford ? (
                <>
                  <Zap size={20} className="fill-current" />
                  Initialize Simulation
                </>
              ) : (
                <>
                  <AlertCircle size={20} />
                  Limit Reached
                </>
              )}
            </button>
            {!canAfford && (
              <button className="w-full text-blue-600 dark:text-blue-400 text-sm font-semibold hover:underline">
                Upgrade Plan for More Runs
              </button>
            )}
          </div>
        ) : (
          <button
            onClick={onCancelRun}
            className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl font-bold bg-red-50 dark:bg-red-900/20 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 transition-all border border-red-100 dark:border-red-900/30"
          >
            <X className="w-5 h-5" />
            Cancel and Stop Simulation
          </button>
        )}
      </div>
    </motion.div>
  );
}
