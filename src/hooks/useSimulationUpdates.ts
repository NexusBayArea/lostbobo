import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { toast } from 'sonner';
import { SimulationRow } from '../types/db';
import { SimulationUpdate } from '../types/realtime';

export const useSimulationUpdates = (userId: string | undefined) => {
  const [simulations, setSimulations] = useState<SimulationRow[]>([]);

  useEffect(() => {
    if (!userId || !supabase) return;

    const fetchHistory = async () => {
      try {
        const { data, error } = await supabase
          .from('simulations')
          .select('*')
          .eq('user_id', userId)
          .order('created_at', { ascending: false })
          .limit(20);

        if (error) throw error;
        if (data) setSimulations(data as SimulationRow[]);
      } catch (err) {
        console.error('Failed to fetch simulations:', err);
      }
    };

    fetchHistory();

    let channel: ReturnType<typeof supabase.channel> | undefined;

    try {
      channel = supabase
        .channel('simulation-updates')
        .on(
          'postgres_changes',
          {
            event: 'UPDATE',
            schema: 'public',
            table: 'simulations',
            filter: `user_id=eq.${userId}`,
          },
          (payload) => {
            const updated = payload.new as SimulationUpdate;

            setSimulations((current) =>
              current.map((sim) => (sim.id === updated.id ? { ...sim, ...updated } as SimulationRow : sim))
            );

            if (updated.status === 'completed') {
              toast.success(`Simulation ${updated.scenario_name || (updated.job_id || '').slice(0, 8)} Complete!`, {
                duration: 10000,
                description: 'Results are ready for review. Download your AI report below.',
                style: {
                  minWidth: '380px',
                  fontSize: '16px',
                },
              });
            }

            if (updated.status === 'failed') {
              toast.error(`Simulation ${updated.scenario_name || (updated.job_id || '').slice(0, 8)} Failed`, {
                duration: 10000,
                description: 'Check the job logs for details.',
              });
            }
          }
        )
        .on(
          'postgres_changes',
          {
            event: 'INSERT',
            schema: 'public',
            table: 'simulations',
            filter: `user_id=eq.${userId}`,
          },
          (payload) => {
            const newSim = payload.new as SimulationRow;
            setSimulations((current) => [newSim, ...current]);
          }
        )
        .subscribe();
    } catch (err) {
      console.error('Realtime subscription failed:', err);
    }

    return () => {
      if (channel) {
        supabase.removeChannel(channel);
      }
    };
  }, [userId]);

  return { simulations, setSimulations };
};
