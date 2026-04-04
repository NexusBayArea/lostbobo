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

  // Admin Fleet Management
  async getFleetStatus(token: string) {
    const response = await fetch(`${API_URL}/api/v1/admin/fleet/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch fleet status');
    return response.json();
  },

  async getFleetReadiness(token: string) {
    const response = await fetch(`${API_URL}/api/v1/admin/fleet/readiness`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch fleet readiness');
    return response.json();
  },

  async warmPod(token: string) {
    const response = await fetch(`${API_URL}/api/v1/admin/fleet/warm`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to warm pod');
    return response.json();
  },

  async stopPod(token: string, podId: string) {
    const response = await fetch(`${API_URL}/api/v1/admin/fleet/pod/${podId}/stop`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to stop pod');
    return response.json();
  },

  async terminatePod(token: string, podId: string) {
    const response = await fetch(`${API_URL}/api/v1/admin/fleet/pod/${podId}/terminate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to terminate pod');
    return response.json();
  },

  // Edge Functions (Admin Only)
  async getFleetMetrics(token: string) {
    // This calls the Supabase Edge Function directly or through the API proxy
    // For now, assume it's routed through the API for simplicity or called directly
    const response = await fetch(`${API_URL}/api/v1/admin/fleet/metrics`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error('Failed to fetch fleet metrics');
    return response.json();
  },
};

