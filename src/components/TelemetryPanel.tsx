import React, { useState, useEffect } from 'react';
import { Activity, Cpu, TrendingUp, ShieldAlert, ShieldCheck } from 'lucide-react';
import { useControlRoomStore } from '../store/controlRoomStore';

// --- Signal Sparkline Component ---
function Sparkline({ data, color = "#22c55e" }: { data: number[]; color?: string }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const h = 24;
  const w = 80;
  const points = data
    .map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / range) * h}`)
    .join(" ");

  return (
    <svg width={w} height={h} className="opacity-60">
      <polyline fill="none" stroke={color} strokeWidth="1.5" points={points} />
    </svg>
  );
}

export const TelemetryPanel: React.FC = () => {
  const store = useControlRoomStore();
  const [signalHistory, setSignalHistory] = useState<{
    gpu: number[];
    convergence: number[];
    error: number[];
  }>({ gpu: [], convergence: [], error: [] });

  useEffect(() => {
    // Update local history for sparklines whenever store updates
    setSignalHistory((prev) => ({
      gpu: [...prev.gpu.slice(-19), store.systemStatus.gpu_load],
      // For demo purposes, we'll randomize or simulate convergence/error if not in store
      convergence: [...prev.convergence.slice(-19), 98 + Math.random()], 
      error: [...prev.error.slice(-19), Math.random() * 5],
    }));
  }, [store.systemStatus.gpu_load]);

  return (
    <div className="bg-[#0A0F1C] border border-slate-800/70 rounded-xl overflow-hidden h-full flex flex-col font-mono">
      <div className="px-4 py-3 border-b border-slate-800/60 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
            Telemetry
          </span>
        </div>
        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse" />
      </div>
      
      <div className="flex-1 divide-y divide-slate-800/40">
        {/* GPU Load */}
        <div className="px-4 py-4 group">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2 text-slate-500 group-hover:text-slate-300 transition-colors">
              <Cpu className="w-3.5 h-3.5" />
              <span className="text-[9px] uppercase tracking-[0.15em] font-semibold">GPU Load</span>
            </div>
          </div>
          <div className="flex items-end justify-between">
            <span className="text-xl font-bold tracking-tight text-white">{store.systemStatus.gpu_load}%</span>
            <Sparkline data={signalHistory.gpu} color="#3b82f6" />
          </div>
        </div>

        {/* Convergence */}
        <div className="px-4 py-4 group">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2 text-slate-500 group-hover:text-slate-300 transition-colors">
              <TrendingUp className="w-3.5 h-3.5" />
              <span className="text-[9px] uppercase tracking-[0.15em] font-semibold">Convergence</span>
            </div>
          </div>
          <div className="flex items-end justify-between">
            <span className="text-xl font-bold tracking-tight text-emerald-400">
              {signalHistory.convergence[signalHistory.convergence.length - 1]?.toFixed(1) || '98.5'}%
            </span>
            <Sparkline data={signalHistory.convergence} color="#22c55e" />
          </div>
        </div>

        {/* Residual Error */}
        <div className="px-4 py-4 group">
          <div className="flex items-center justify-between mb-1.5">
            <div className="flex items-center gap-2 text-slate-500 group-hover:text-slate-300 transition-colors">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span className="text-[9px] uppercase tracking-[0.15em] font-semibold">Resid. Error</span>
            </div>
          </div>
          <div className="flex items-end justify-between">
            <span className="text-xl font-bold tracking-tight text-slate-300">1.2e-5</span>
            <Sparkline data={signalHistory.error} color="#64748b" />
          </div>
        </div>
      </div>

      {/* Auditor Status */}
      <div className="p-4 bg-red-500/5 border-t border-red-500/20">
        <div className="flex items-center gap-2 mb-2">
          <ShieldCheck className="w-3 h-3 text-red-500" />
          <span className="text-[10px] font-bold text-red-400 uppercase tracking-widest">Rnj-1 Auditor</span>
        </div>
        {store.alerts.length > 0 ? (
          <p className="text-[10px] text-red-300/80 leading-relaxed italic">
            "{store.alerts[0].message}"
          </p>
        ) : (
          <p className="text-[10px] text-slate-500 italic">No anomalies detected in active mesh.</p>
        )}
      </div>
    </div>
  );
};
