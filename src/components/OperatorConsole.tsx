import React, { useEffect, useState } from 'react';
import { useControlRoomStore } from '../store/controlRoomStore';
import { Anchor, Copy, Zap, FileCheck, Terminal, Lock, Crown } from 'lucide-react';
import { Button } from './ui/button';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';
import { toast } from 'sonner';

export const OperatorConsole: React.FC = () => {
  const activeSims = useControlRoomStore((state) => state.activeSimulations);
  const selectedRunId = activeSims.length > 0 ? activeSims[0].run_id : null;
  const [userProfile, setUserProfile] = useState<any>(null);

  const { getToken } = useAuth();
  
  useEffect(() => {
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
  
  const handleCommand = async (action: string) => {
    const token = getToken();
    if (!token || !selectedRunId) return;
    
    // Check for free tier restrictions
    if (isFreeTier && (action === 'boost' || action === 'certify')) {
      toast.error("Upgrade to Pro for Advanced Commands", {
        description: `${action.toUpperCase()} is available on Professional and Enterprise tiers.`,
        action: {
          label: "Upgrade",
          onClick: () => {
            window.location.href = '/pricing';
          }
        }
      });
      return;
    }
    
    try {
      await api.executeControlCommand(token, action, selectedRunId);
      toast.success(`OPERATOR_COMMAND: ${action.toUpperCase()} DISPATCHED`, {
        description: `Targeting node ${selectedRunId.slice(0, 8)}...`
      });
    } catch (error) {
      toast.error(`COMMAND_FAILED: ${action.toUpperCase()}`);
    }
  };

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono shadow-2xl">
      <div className="flex items-center gap-2 mb-4 text-emerald-500 border-b border-slate-800 pb-2">
        <Terminal className="w-4 h-4" />
        <span className="text-sm tracking-tighter">OPERATOR_CONSOLE v1.1</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Button 
          variant="outline" 
          disabled={!selectedRunId}
          onClick={() => handleCommand('intercept')}
          className="h-12 border-slate-800 hover:border-red-500/50 hover:bg-red-500/5 group text-xs justify-start px-3"
        >
          <Anchor className="w-4 h-4 mr-2 text-slate-500 group-hover:text-red-500" />
          <div className="text-left">
            <div className="font-bold uppercase tracking-tighter">INTERCEPT</div>
            <div className="text-[8px] text-slate-500 uppercase">PHYSICS PAUSE</div>
          </div>
        </Button>

        <Button 
          variant="outline" 
          disabled={!selectedRunId}
          onClick={() => handleCommand('clone')}
          className="h-12 border-slate-800 hover:border-cyan-500/50 hover:bg-cyan-500/5 group text-xs justify-start px-3"
        >
          <Copy className="w-4 h-4 mr-2 text-slate-500 group-hover:text-cyan-500" />
          <div className="text-left">
            <div className="font-bold uppercase tracking-tighter">CLONE & RE-RUN</div>
            <div className="text-[8px] text-slate-500 uppercase">BRANCH CHILD</div>
          </div>
        </Button>

        <Button 
          variant="outline" 
          disabled={!selectedRunId}
          onClick={() => handleCommand('boost')}
          className="h-12 border-slate-800 hover:border-amber-500/50 hover:bg-amber-500/5 group text-xs justify-start px-3"
        >
          <Zap className="w-4 h-4 mr-2 text-slate-500 group-hover:text-amber-500" />
          <div className="text-left">
            <div className="font-bold uppercase tracking-tighter">BOOST PRIORITY</div>
            <div className="text-[8px] text-slate-500 uppercase">GPU REALLOC</div>
          </div>
        </Button>

        <Button 
          variant="outline" 
          disabled={!selectedRunId}
          onClick={() => handleCommand('certify')}
          className="h-12 border-slate-800 hover:border-emerald-500/50 hover:bg-emerald-500/5 group text-xs justify-start px-3 font-bold bg-emerald-500/5"
        >
          <FileCheck className="w-4 h-4 mr-2 text-emerald-500" />
          <div className="text-left">
            <div className="font-bold uppercase tracking-tighter text-emerald-400">CERTIFY</div>
            <div className="text-[8px] text-emerald-600 uppercase">DOCUMENT RESULT</div>
          </div>
        </Button>
      </div>

      {!selectedRunId && (
        <div className="mt-4 text-[9px] text-slate-600 uppercase text-center opacity-50">
          SELECT NODE TO ENABLE OPERATOR AFFORDANCES
        </div>
      )}
    </div>
  );
};
