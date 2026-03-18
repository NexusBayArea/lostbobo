import React, { useEffect, useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { Activity, Clock, Zap } from "lucide-react";

interface StatusData {
  mercury: string;
  supabase: string;
  worker: string;
  timestamp: string;
}

interface JobLog {
  id: string;
  status: string;
  created_at: string;
  model_name: string;
}

interface UsageData {
  runs_used: number;
  limit: number;
  reset_timestamp: string;
}

const StatusLED = ({ state }: { state: string }) => {
  const isGood = ['online', 'connected', 'warm'].includes(state);
  return (
    <div className="flex items-center space-x-2 my-1">
      <div className={`h-2.5 w-2.5 rounded-full ${isGood ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-red-500'} ${isGood && 'animate-pulse'}`} />
      <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
        {state || 'checking...'}
      </span>
    </div>
  );
};

export function SystemStatus() {
  const { getToken } = useAuth();
  const [status, setStatus] = useState<StatusData>({ mercury: '', supabase: '', worker: '', timestamp: '' });
  const [logs, setLogs] = useState<JobLog[]>([]);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [userPlan, setUserPlan] = useState<string>('free');
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const token = getToken();
      const response = await fetch('/api/v1/system-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      setStatus(data);
    } catch (e) {
      setStatus({ mercury: 'offline', supabase: 'offline', worker: 'offline', timestamp: new Date().toISOString() });
    }
  };

  const fetchLogs = async () => {
    try {
      const token = getToken();
      const response = await fetch('/api/v1/system/job-logs', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      setLogs(data);
    } catch (e) {
      console.error("Failed to fetch logs:", e);
    }
  };

  const fetchUserInfo = async () => {
    try {
      const token = getToken();
      const response = await fetch('/api/v1/user/profile', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (response.ok) {
        const profile = await response.json();
        setUserPlan(profile.plan || 'free');
        // For free tier, show usage
        if (profile.plan === 'free') {
          setUsage({ runs_used: profile.runs_used || 0, limit: 5, reset_timestamp: '' });
        }
      }
    } catch (e) {
      console.error("Failed to fetch user info:", e);
    }
  };

  const fetchData = async () => {
    await Promise.all([fetchStatus(), fetchLogs(), fetchUserInfo()]);
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="mt-auto px-4 py-6 space-y-6">
      {/* Free Tier Usage Counter */}
      {userPlan === 'free' && usage && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              <span className="text-[11px] font-bold text-amber-500 uppercase tracking-wider">
                Free Tier
              </span>
            </div>
            <span className="text-[10px] px-2 py-1 bg-amber-500/20 text-amber-400 rounded font-mono">
              {usage.limit - usage.runs_used} / {usage.limit} runs left
            </span>
          </div>
          <div className="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-amber-500 transition-all duration-300"
              style={{ width: `${(usage.runs_used / usage.limit) * 100}%` }}
            />
          </div>
          <p className="text-[9px] text-slate-500 mt-2">
            Resets every 7 days. Upgrade to Pro for unlimited runs.
          </p>
        </div>
      )}

      {/* System Health Status */}
      <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg mb-4">
        <h4 className="text-[10px] font-bold text-cyan-500 uppercase mb-3 tracking-[0.2em] flex items-center gap-2">
          <Activity className="w-3 h-3" />
          System Health
        </h4>
        <div className="grid grid-cols-1 gap-1">
          <div className="flex justify-between items-center border-b border-slate-800/50 pb-1">
            <span className="text-[11px] text-slate-300">Mercury AI</span>
            <StatusLED state={status.mercury} />
          </div>
          <div className="flex justify-between items-center border-b border-slate-800/50 py-1">
            <span className="text-[11px] text-slate-300">Sim Worker</span>
            <StatusLED state={status.worker} />
          </div>
          <div className="flex justify-between items-center pt-1">
            <span className="text-[11px] text-slate-300">Supabase DB</span>
            <StatusLED state={status.supabase} />
          </div>
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-700/50">
        <h4 className="text-[10px] font-bold tracking-[0.2em] text-slate-500 dark:text-slate-400 uppercase flex items-center gap-2">
          <Clock className="w-3 h-3 text-cyan-500" />
          Recent Jobs
        </h4>
        
        <div className="space-y-2">
          {logs.length > 0 ? (
            logs.map((job) => (
              <div key={job.id} className="group p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors border border-transparent hover:border-slate-200 dark:hover:border-slate-700">
                <div className="flex items-center justify-between gap-2">
                  <span className={cn(
                    "text-[10px] font-semibold uppercase tracking-wider",
                    job.status === 'completed' ? "text-emerald-500" : 
                    job.status === 'failed' ? "text-rose-500" : "text-amber-500"
                  )}>
                    {job.status}
                  </span>
                  <span className="text-[9px] text-slate-400 dark:text-slate-500 font-mono">
                    {new Date(job.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="text-[10px] text-slate-500 dark:text-slate-400 truncate mt-1">
                  ID: {job.id.slice(0, 8)}... — {job.model_name}
                </div>
              </div>
            ))
          ) : (
            <div className="text-[10px] text-slate-400 dark:text-slate-500 italic py-2">
              {loading ? "Initializing..." : "No recent activity"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
