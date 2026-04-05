import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { SimulationRow } from '../types/db';

export interface SimulationTelemetry {
  id: string;
  job_id: string | null;
  scenario_name: string | null;
  status: string;
  progress: number;
  thermal_drift: number;
  pressure_spike: boolean;
  created_at: string;
  updated_at: string;
}

function extractTelemetry(row: SimulationRow): SimulationTelemetry {
  const result = (row.result_summary as Record<string, unknown>) || {};
  const gpu = (row.gpu_result as Record<string, unknown>) || {};
  return {
    id: row.id,
    job_id: row.job_id,
    scenario_name: row.scenario_name,
    status: row.status,
    progress: (result.progress as number) ?? (row.status === 'completed' ? 100 : row.status === 'running' ? 50 : 0),
    thermal_drift: (result.thermal_drift as number) ?? (gpu.thermal_drift as number) ?? 0,
    pressure_spike: (result.pressure_spike as boolean) ?? (gpu.pressure_spike as boolean) ?? false,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

export function useSimulations(userId: string | undefined) {
  const [simulations, setSimulations] = useState<SimulationTelemetry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId || !supabase) {
      setLoading(false);
      return;
    }

    const client = supabase;

    const fetchSims = async () => {
      try {
        const { data, error } = await client
          .from('simulations')
          .select('*')
          .eq('user_id', userId)
          .order('created_at', { ascending: false })
          .limit(10);

        if (!error && data) {
          setSimulations(data.map(extractTelemetry));
        }
      } catch (err) {
        console.error('Failed to fetch simulations:', err);
      }
      setLoading(false);
    };

    fetchSims();

    let channel: ReturnType<typeof client.channel> | undefined;

    try {
      channel = client
        .channel('simulations-telemetry')
        .on(
          'postgres_changes',
          {
            event: '*',
            schema: 'public',
            table: 'simulations',
            filter: `user_id=eq.${userId}`,
          },
          (payload) => {
            if (payload.eventType === 'INSERT') {
              setSimulations((prev) => [
                extractTelemetry(payload.new as SimulationRow),
                ...prev,
              ]);
            } else if (payload.eventType === 'UPDATE') {
              setSimulations((prev) =>
                prev.map((sim) =>
                  sim.id === (payload.new as SimulationRow).id
                    ? extractTelemetry(payload.new as SimulationRow)
                    : sim
                )
              );
            }
          }
        )
        .subscribe();
    } catch (err) {
      console.error('Realtime subscription failed:', err);
    }

    return () => {
      if (channel) {
        client.removeChannel(channel);
      }
    };
  }, [userId]);

  return { simulations, loading };
}
