import { useState } from 'react';
import { api, RunStatusResponse } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';

export function useSimulation() {
  const { getToken } = useAuth();
  const [status, setStatus] = useState<'idle' | 'running' | 'completed' | 'failed' | 'queued' | 'processing'>('idle');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<any>(null);
  const [runId, setRunId] = useState<string | null>(null);

  const startSim = async (config: any) => {
    setStatus('queued');
    setProgress(0);
    setResults(null);
    
    try {
      const token = getToken();
      const response = await api.startRobustnessRun(config, token);
      setRunId(response.run_id);
      
      poll(response.run_id);
    } catch (e: any) {
      setStatus('failed');
      toast.error(e.message || 'Failed to start simulation');
    }
  };

  const poll = async (runId: string) => {
    try {
      const token = getToken();
      const finalStatus = await api.pollStatus(runId, token, (p) => {
        setProgress(p);
        setStatus('processing');
      });

      if (finalStatus.status === 'completed') {
        setResults(finalStatus.results);
        setStatus('completed');
        toast.success('Simulation completed successfully');
      } else {
        setStatus('failed');
        toast.error('Simulation failed');
      }
    } catch (e: any) {
      setStatus('failed');
      toast.error(`Polling failed: ${e.message}`);
    }
  };

  return { startSim, status, progress, results, runId };
}
