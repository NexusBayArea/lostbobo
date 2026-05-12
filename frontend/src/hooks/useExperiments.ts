import { useState, useEffect } from 'react';

interface Experiment {
  id: string;
  title: string;
  status: string;
  engine: string;
  question: string;
  tags: string[];
  createdAt: string;
  completedAt: string | null;
  parameters: { name: string; value: number; changed: boolean }[];
  runs: { id: number; label: string; param: string; value: string; result: string; convergent: boolean; plotY: number[] }[];
  observations: string[];
  conclusion: string;
  linkedIds: string[];
  metrics: Record<string, string>;
}

interface UseExperimentsResult {
  experiments: Experiment[];
  loading: boolean;
}

export function useExperiments(token?: string): UseExperimentsResult {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchExperiments = async () => {
      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const res = await fetch('/api/v1/capability/invoke', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            capability: 'memory.recall',
            payload: {
              tenant_id: 'default',
              memory_type: 'execution',
              limit: 100,
              filters: { plugin_name: 'robustness' },
            },
          }),
        });

        const json = await res.json();
        const records = (json.data?.records || json.records || []).map((rec: any) => {
          const state = rec.execution_state || {};
          const exp = state.experiment || {};
          const results = state.results || [];
          const runs = results.map((r: any, i: number) => ({
            id: i + 1,
            label: `Run #${i + 1}`,
            param: Object.keys(r.parameters || {}).join(', '),
            value: Object.values(r.parameters || {}).join(', '),
            result: r.converged ? 'Stable' : 'Failed',
            convergent: r.converged || false,
            plotY: r.plotY || [],
          }));

          return {
            id: rec.memory_id?.substring(0, 8) || 'unknown',
            title: exp.title || rec.metadata?.report_title || 'Untitled',
            status: state.completed === state.total ? 'completed' : 'running',
            engine: state.solver_type || 'MFEM+SUNDIALS',
            question: exp.question || '',
            tags: exp.tags || [],
            createdAt: rec.timestamp ? new Date(rec.timestamp * 1000).toISOString() : '',
            completedAt: state.completed === state.total ? new Date().toISOString() : null,
            parameters: (state.parameters || []).map((p: any) => ({
              name: p.name,
              value: p.base,
              changed: false,
            })),
            runs,
            observations: exp.observations || [],
            conclusion: exp.conclusion || '',
            linkedIds: [],
            metrics: {},
          };
        });

        setExperiments(records);
      } catch (e) {
        console.error('Failed to fetch experiments', e);
      } finally {
        setLoading(false);
      }
    };

    fetchExperiments();
  }, [token]);

  return { experiments, loading };
}
