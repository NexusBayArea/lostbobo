import { supabase } from '@/lib/supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  async getSimulationUsage(token: string) {
    const response = await fetch(`${API_URL}/api/v1/usage`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error('Failed to fetch usage');
    return response.json();
  },

  async startSimulation(token: string, params: Record<string, unknown>) {
    const response = await fetch(`${API_URL}/api/v1/simulations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(params),
    });
    if (!response.ok) throw new Error('Failed to start simulation');
    return response.json();
  },

  async cancelSimulation(token: string, jobId: string) {
    const response = await fetch(`${API_URL}/api/v1/simulations/${jobId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) throw new Error('Failed to cancel simulation');
    return response.json();
  },
};
