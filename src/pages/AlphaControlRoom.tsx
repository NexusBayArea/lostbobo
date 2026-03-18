import { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { api } from "@/lib/api";
import { PageLayout } from "@/components/PageLayout";
import {
  Terminal,
  Clock,
  Radio,
} from "lucide-react";
import { toast } from "sonner";
import { SimulationTimeline } from "@/components/SimulationTimeline";
import { TelemetryPanel } from "@/components/TelemetryPanel";
import { ActiveSimulations } from "@/components/ActiveSimulations";
import { SimulationLineage } from "@/components/SimulationLineage";
import { OperatorConsole } from "@/components/OperatorConsole";
import { GuidanceEngine } from "@/components/GuidanceEngine";
import { useControlRoomStore } from "@/store/controlRoomStore";

// --- UTC Clock Component ---
function UTCClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);
  return (
    <span className="font-mono tabular-nums text-[10px]">
      {time.toUTCString().split(" ").slice(4).join(" ").replace(" GMT", "")} UTC
    </span>
  );
}

export const AlphaControlRoom = () => {
  const { getToken } = useAuth();
  const store = useControlRoomStore();
  const [loading, setLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<any>(null);

  const fetchControlRoomState = async () => {
    const token = getToken();
    if (!token) return;
    try {
      // Fetch user profile for tier-based feature gating
      const [profile, state] = await Promise.all([
        api.getUserProfile(token),
        api.getControlRoomState(token)
      ]);
      
      setUserProfile(profile);
      
      store.setFullState({
        activeSimulations: state.active_runs || [],
        alerts: state.audit_alerts || [],
        timeline: state.timeline_events || [],
        lineage: profile.plan === 'free' ? null : state.lineage || null, // Disable lineage for free tier
        insights: state.guidance ? [state.guidance] : [],
        systemStatus: {
          gpu_load: state.telemetry?.gpu_load || 0,
          status: state.telemetry?.status || 'nominal'
        }
      });

    } catch (error) {
      console.error("Control Room sync error:", error);
      // Fallback/mock data for demo if API fails
      if (loading) {
         store.setFullState({
            systemStatus: { gpu_load: 42, status: 'nominal' }
         });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchControlRoomState();
    const interval = setInterval(fetchControlRoomState, 5000);
    return () => clearInterval(interval);
  }, [getToken]);

  return (
    <PageLayout>
      <div className="min-h-screen bg-[#060A14] text-slate-200 p-4 font-mono selection:bg-cyan-500/30 flex flex-col gap-4">
        
        {/* --- HEADER --- */}
        <header className="flex items-center justify-between pb-4 border-b border-slate-800/60">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-500/20 border border-cyan-500/30 flex items-center justify-center">
                <Terminal className="w-5 h-5 text-cyan-400" />
              </div>
              <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-cyan-500 rounded-full animate-pulse border-2 border-[#060A14]" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                SIMHPC COCKPIT
                <span className="text-[9px] font-mono bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 px-2 py-0.5 rounded uppercase tracking-widest">
                  Alpha Pilot
                </span>
              </h1>
              <p className="text-[10px] text-slate-600 uppercase tracking-[0.25em]">
                Decision Intelligence Operations Center
              </p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="hidden md:flex items-center gap-2 text-cyan-400 text-[10px]">
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              <span className="uppercase tracking-widest font-bold">Live Stream Active</span>
            </div>
            <div className="text-slate-500 flex items-center gap-1.5">
              <Clock className="w-3 h-3" />
              <UTCClock />
            </div>
          </div>
        </header>

        {/* --- 1. SIMULATION TIMELINE (Top Horizontal) --- */}
        <SimulationTimeline />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1">
          
          {/* --- 2. TELEMETRY PANEL (Left Sidebar) --- */}
          <div className="lg:col-span-3">
            <TelemetryPanel />
          </div>

          {/* --- 3. ACTIVE CLUSTER & MEMORY (Main Content) --- */}
          <div className="lg:col-span-9 flex flex-col gap-4">
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 min-h-[400px]">
              {/* Active Simulations */}
              <ActiveSimulations />
              
              {/* Simulation Memory / Lineage */}
              <SimulationLineage />
            </div>

            {/* --- 4. COMMAND CONSOLE & GUIDANCE ENGINE (Bottom Actions) --- */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <OperatorConsole />
              <GuidanceEngine />
            </div>

          </div>
        </div>

        {/* --- FOOTER STATUS BAR --- */}
        <footer className="pt-4 border-t border-slate-800/40 flex flex-col sm:flex-row justify-between items-center gap-2 text-[8px] text-slate-700 uppercase tracking-[0.25em] font-mono">
          <div className="flex gap-6 flex-wrap justify-center">
            <span className="flex items-center gap-1.5">
              <div className="w-1 h-1 bg-emerald-500 rounded-full" /> GPU Cluster: Online
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-1 h-1 bg-emerald-500 rounded-full" /> SUNDIALS Solver: Ready
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-1 h-1 bg-blue-500 rounded-full" /> Mercury AI: Connected
            </span>
            <span className="flex items-center gap-1.5">
              <div className="w-1 h-1 bg-emerald-500 rounded-full" /> Supabase: Synced
            </span>
          </div>
          <div className="text-slate-600 flex items-center gap-4">
            <span 
              className="text-cyan-500/50 font-black border border-cyan-500/20 px-2 py-0.5 rounded cursor-pointer hover:bg-cyan-500/10 transition-colors"
              onClick={() => toast.success("Generating Physics-Verified Certificate...")}
            >
              [GENERATE CERTIFICATE]
            </span>
            <span>v1.6.0-ALPHA</span>
          </div>
        </footer>
      </div>
    </PageLayout>
  );
};

export default AlphaControlRoom;
