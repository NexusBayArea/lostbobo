import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, ShieldAlert, Cpu, Zap, Activity as Sparkles, Terminal, ChevronRight, LayoutGrid, Clock, Play, AlertCircle, RefreshCw, Layers, GitBranch, Sparkles as Magic } from 'lucide-react';
import { Navigation } from '@/components/Navigation';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useSimulations } from '@/hooks/useSimulations';
import { toast } from 'sonner';

// Rebuilt Production-Grade Cockpit Components
import { TelemetryPanel } from '@/components/TelemetryPanel';
import { ActiveSimulations } from '@/components/ActiveSimulations';
import { SimulationLineage } from '@/components/SimulationLineage';
import { OperatorConsole } from '@/components/OperatorConsole';
import { GuidanceEngine } from '@/components/GuidanceEngine';

export function AlphaControlRoom() {
  const { user, getToken } = useAuth();
  const { simulations, loading: simsLoading } = useSimulations(user?.id);
  const [activeTab, setActiveTab] = useState('observe');
  
  // HUD Data
  const activeCount = simulations.filter(s => s.status === 'running' || s.status === 'auditing').length;
  const completedCount = simulations.filter(s => s.status === 'completed').length;
  const errorCount = simulations.filter(s => s.status === 'failed').length;

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col font-mono selection:bg-cyan-500/30">
      <Navigation />
      
      <div className="flex-1 pt-16 flex overflow-hidden">
        {/* Left Sidebar HUD */}
        <aside className="w-16 border-r border-slate-800 bg-slate-950/50 flex flex-col items-center py-6 gap-8 z-20">
          <div className="mt-4">
            <Zap className="w-6 h-6 text-cyan-400 opacity-80 animate-pulse" />
          </div>
          <div className="flex-1 flex flex-col gap-4">
            {[
              { id: 'observe', icon: Activity, label: 'O' },
              { id: 'detect', icon: ShieldAlert, label: 'D' },
              { id: 'investigate', icon: Layers, label: 'I' },
              { id: 'act', icon: Terminal, icon2: Zap, label: 'A' },
              { id: 'verify', icon: Magic, label: 'V' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all group relative overflow-hidden ${
                  activeTab === tab.id ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_15px_rgba(34,211,238,0.2)]' : 'text-slate-600 hover:text-slate-400'
                }`}
              >
                <tab.icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${activeTab === tab.id ? 'scale-110' : ''}`} />
                <div className="absolute inset-0 bg-cyan-400 opacity-0 group-hover:opacity-10 transition-opacity" />
              </button>
            ))}
          </div>
          <div className="mb-4">
             <div className="w-1 h-32 bg-slate-800 rounded-full overflow-hidden flex flex-col justify-end">
                <motion.div animate={{ height: ['40%', '60%', '20%', '80%', '40%'] }} className="w-full bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)]" />
             </div>
          </div>
        </aside>

        {/* HUD Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Ticker Hub */}
          <div className="h-10 bg-slate-900 border-b border-slate-800/50 flex items-center px-6 justify-between overflow-hidden shadow-lg backdrop-blur-2xl">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Live Fleet</span>
                <Badge variant="outline" className="h-5 text-[10px] border-cyan-500/30 text-cyan-400 bg-cyan-400/5 px-2 font-mono font-bold">
                  {activeCount} NODES
                </Badge>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Throughput</span>
                <span className="text-[10px] text-white font-mono">4.2 SIMS/HR</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Stability</span>
                <span className="text-[10px] text-green-400 font-mono">99.98%</span>
              </div>
            </div>
            
            <div className="flex items-center gap-6 text-[10px] font-mono">
              <span className="text-slate-600 flex items-center gap-2">
                 <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                 MERCURY-2: ONLINE
              </span>
              <span className="text-slate-600 lowercase bg-slate-800/50 px-2 py-0.5 rounded tracking-tighter">UTC: {new Date().toISOString().substring(11, 19)}</span>
            </div>
          </div>

          {/* Main 4-Panel HUD View (O-D-I-A-V Loop) */}
          <div className="flex-1 p-6 grid grid-cols-12 grid-rows-12 gap-6 overflow-hidden">
            {/* Panel 1: Live Telemetry */}
            <div className="col-span-8 row-span-6 transition-all">
               <TelemetryPanel />
            </div>

            {/* Panel 2: Decision Grid (Active Sims) */}
            <div className="col-span-4 row-span-8 transition-all">
               <ActiveSimulations />
            </div>

            {/* Panel 3: Temporal Memory (Design Lineage) */}
            <div className="col-span-8 row-span-6 transition-all">
               <SimulationLineage />
            </div>

            {/* Panel 4: Intervention Console & AI Navigation */}
            <div className="col-span-4 row-span-4 grid grid-cols-1 gap-6 transition-all">
               {activeTab === 'act' ? <OperatorConsole /> : <GuidanceEngine />}
            </div>
          </div>
        </div>
      </div>
      
      {/* Footer System Status Bar */}
      <footer className="h-8 bg-slate-950 border-t border-slate-800/50 px-6 flex items-center justify-between text-[8px] font-mono tracking-[0.2em] uppercase text-slate-600">
         <div className="flex items-center gap-6">
            <span className="flex items-center gap-2">
               INFRA: <span className="text-slate-400">RUNPOD/A40</span>
            </span>
            <span className="flex items-center gap-2">
               RESOLVER: <span className="text-slate-400">SUNDIALS CVODE</span>
            </span>
            <span className="flex items-center gap-2">
               ENCRYPT: <span className="text-green-500">AES-256</span>
            </span>
         </div>
         <div>
            SIMHPC MISSION CONTROL Cockpit // v2.5.0-ALPHA-BUILD-000782
         </div>
      </footer>
    </div>
  );
}
