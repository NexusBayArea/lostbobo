import { useState, useEffect } from 'react';
import { api, RunStatusResponse } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';

export function useSimulations(userId?: string) {
  const { getToken } = useAuth();
  const [simulations, setSimulations] = useState<RunStatusResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSimulations = async () => {
    try {
      setLoading(true);
      const token = getToken();
      const runs = await api.listRuns(token);
      setSimulations(Array.isArray(runs) ? runs : []);
    } catch (e: any) {
      setError(e.message);
      setSimulations([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSimulations();
    const interval = setInterval(fetchSimulations, 30000);
    return () => clearInterval(interval);
  }, [userId]);

  return { simulations, loading, error, refetch: fetchSimulations };
}
