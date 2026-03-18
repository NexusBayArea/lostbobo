import React from 'react';
import { motion } from 'framer-motion';
import { useControlRoomStore } from '../store/controlRoomStore';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api';
import { Share2, GitBranch, ArrowRightLeft, FileCode, Lock, Crown } from 'lucide-react';
import { toast } from 'sonner';

export const SimulationLineage: React.FC = () => {
  const lineage = useControlRoomStore((state) => state.lineage);
  const { getToken } = useAuth();
  const [userProfile, setUserProfile] = React.useState<any>(null);

  React.useEffect(() => {
    const fetchProfile = async () => {
      try {
        const token = getToken();
        const profile = await api.getUserProfile(token);
        setUserProfile(profile);
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
      }
    };
    fetchProfile();
  }, [getToken]);

  const isFreeTier = userProfile?.plan === 'free';

  const handleUpgradeClick = () => {
    toast.error("Upgrade to Pro for Experiment Trees & Advanced Lineage", {
      description: "Unlock full ancestry tracking, flux delta analysis, and compliance RAG anchoring.",
      action: {
        label: "Upgrade",
        onClick: () => {
          // Navigate to pricing or trigger upgrade modal
          window.location.href = '/pricing';
        }
      }
    });
  };

  return (
    <div className="bg-slate-900/30 border border-slate-800 rounded-lg p-5 flex flex-col h-full overflow-hidden relative">
      {/* Free Tier Lock Overlay */}
      {isFreeTier && (
        <div 
          className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm flex flex-col items-center justify-center z-10 cursor-pointer group"
          onClick={handleUpgradeClick}
        >
          <div className="text-center p-6">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center group-hover:bg-amber-500/20 transition-colors">
              <Lock className="w-8 h-8 text-amber-500" />
            </div>
            <h4 className="text-sm font-bold text-amber-500 uppercase tracking-wider mb-2">
              PRO FEATURE LOCKED
            </h4>
            <p className="text-[10px] text-slate-400 mb-4 max-w-xs">
              Experiment Trees and Advanced Lineage are available on Professional and Enterprise tiers.
            </p>
            <div className="inline-flex items-center gap-2 text-[10px] px-3 py-1.5 bg-amber-500/10 border border-amber-500/30 rounded text-amber-500 hover:bg-amber-500/20 transition-colors">
              <Crown className="w-3 h-3" />
              UPGRADE TO PRO
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-3">
        <h3 className="text-sm font-mono flex items-center gap-2 text-slate-300">
          <GitBranch className="w-4 h-4 text-emerald-500" />
          SIMULATION_LINEAGE
        </h3>
        <div className="text-[10px] font-mono text-slate-500 uppercase">
          {isFreeTier ? 'PRO ONLY' : `Ancestry_Depth: 0${lineage?.nodes.length || 0}`}
        </div>
      </div>

      <div className="flex-1 overflow-auto custom-scrollbar pr-2">
        {!lineage && !isFreeTier ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-600 font-mono text-xs opacity-40 italic text-center px-4">
            <Share2 className="w-10 h-10 mb-2 stroke-1" />
            INITIALIZING LINEAGE ANCESTRY GRAPH...
          </div>
        ) : lineage && !isFreeTier ? (
          <div className="space-y-6">
            <div className="flex flex-col gap-4">
              {lineage.nodes.map((node, i) => (
                <motion.div
                  key={node.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="relative group bg-slate-950 border border-slate-800 p-3 rounded hover:border-emerald-500/30 transition-all cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-mono text-emerald-500 uppercase tracking-tighter">ITERATION_{node.id}</span>
                    <FileCode className="w-3 h-3 text-slate-600 group-hover:text-emerald-500" />
                  </div>
                  <div className="text-xs font-bold text-slate-200 uppercase mb-3">{node.label}</div>
                  
                  {i > 0 && (
                    <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-900 border-dashed">
                      <ArrowRightLeft className="w-3 h-3 text-amber-500" />
                      <span className="text-[9px] font-mono text-amber-500/80 uppercase">Flux Delta: +15% vs Parent</span>
                    </div>
                  )}

                  <div className="absolute -left-1 top-4 w-2 h-2 bg-emerald-500/40 rounded-full blur-[2px]" />
                </motion.div>
              ))}
            </div>
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-slate-500 text-[10px]">
              <p>Lineage visualization unavailable on free tier.</p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 text-[9px] font-mono text-slate-500 flex items-center gap-2 opacity-50 underline decoration-slate-800 cursor-pointer hover:text-emerald-400">
        <FileCode className="w-3 h-3" />
        {isFreeTier ? 'PRO FEATURE: RAG ANCHOR' : 'VIEW SOURCE COMPLIANCE RAG ANCHOR'}
      </div>
    </div>
  );
};
