
// Point to the RunPod Proxy URL
const API_BASE_URL = 'https://40n3yh92ugakps-8000.proxy.runpod.net/api/v1';
const API_KEY = 'shpc_live_40n3yh92ugakps';

const getHeaders = (token?: string) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  } else {
    headers['X-API-Key'] = API_KEY;
  }
  
  return headers;
};

export interface ParameterConfig {
  name: string;
  base_value: number;
  unit: string;
  description: string;
  perturbable: boolean;
  min_value?: number;
  max_value?: number;
}

export interface RobustnessConfig {
  enabled: boolean;
  num_runs: number;
  sampling_method: string;
  parameters: ParameterConfig[];
  convergence_timeout_sec: number;
  random_seed?: number;
}

export interface RunStatusResponse {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'queued' | 'processing';
  progress: {
    current: number;
    total: number;
  } | number;
  created_at: string;
  completed_at?: string;
  results?: any;
  ai_report?: any;
  config_summary?: any;
  error?: string;
}

export interface UserProfile {
  user_id: string;
  plan: 'free' | 'professional' | 'enterprise' | 'demo_general' | 'demo_full' | 'demo_magic';
  email?: string;
  subscription_status: string;
  stripe_customer_id?: string;
}

export interface DemoValidationResponse {
  valid: boolean;
  remaining?: number;
  usage_limit?: number;
  email?: string;
  reason?: 'limit_reached' | 'expired' | 'invalid';
  message?: string;
}

export interface DemoUsageResponse {
  remaining: number;
  limit: number;
  used: number;
  expired: boolean;
}

export const api = {
  async getUserProfile(token: string): Promise<UserProfile> {
    const response = await fetch(`${API_BASE_URL}/user/profile`, { 
      headers: getHeaders(token) 
    });
    if (!response.ok) {
      throw new Error('Failed to fetch user profile');
    }
    return response.json();
  },

  async subscribe(plan: string, token: string): Promise<{ url: string }> {
    const response = await fetch(`${API_BASE_URL}/subscribe`, {
      method: 'POST',
      headers: getHeaders(token),
      body: JSON.stringify({ plan }),
    });
    if (!response.ok) {
      throw new Error('Failed to create subscription session');
    }
    return response.json();
  },

  async startRobustnessRun(config: any, token?: string): Promise<RunStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/robustness/run`, {
      method: 'POST',
      headers: getHeaders(token),
      body: JSON.stringify({
        config: {
          enabled: true,
          num_runs: config.numRuns,
          sampling_method: config.samplingMethod,
          parameters: config.parameters.map((p: any) => ({
            name: p.name,
            base_value: p.baseValue,
            unit: p.unit || '',
            description: p.description || '',
            perturbable: p.perturbable,
            min_value: p.min,
            max_value: p.max
          })),
          convergence_timeout_sec: config.timeout || 300,
          random_seed: config.seed
        }
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail?.message || errorData.detail || 'Failed to start robustness run');
    }

    return response.json();
  },

  async getRunStatus(runId: string, token?: string): Promise<RunStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/robustness/status/${runId}`, { 
      headers: getHeaders(token) 
    });
    if (!response.ok) {
      throw new Error('Failed to fetch run status');
    }
    return response.json();
  },

  async listRuns(token?: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/robustness/runs`, { 
      headers: getHeaders(token) 
    });
    if (!response.ok) {
      throw new Error('Failed to list runs');
    }
    return response.json();
  },

  async getSamplingMethods(token?: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/sampling-methods`, { 
      headers: getHeaders(token) 
    });
    if (!response.ok) {
      throw new Error('Failed to fetch sampling methods');
    }
    return response.json();
  },

  async cancelRobustnessRun(runId: string, token?: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/robustness/cancel/${runId}`, {
      method: 'POST',
      headers: getHeaders(token),
    });
    if (!response.ok) {
      throw new Error('Failed to cancel robustness run');
    }
    return response.json();
  },

  async exportPdf(runId: string, token?: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/robustness/report/${runId}/pdf`, { 
      headers: getHeaders(token) 
    });
    if (!response.ok) {
      throw new Error('Failed to export PDF');
    }
    return response.blob();
  },

  /**
   * Polls the status of a simulation until it completes or fails.
   */
  async pollStatus(
    runId: string, 
    token?: string, 
    onProgress?: (progress: number) => void
  ): Promise<RunStatusResponse> {
    const data = await this.getRunStatus(runId, token);
    
    if (data.status === 'completed' || data.status === 'failed') {
      return data;
    }
    
    if (onProgress) {
      let percent = 0;
      if (typeof data.progress === 'number') {
        percent = data.progress;
      } else if (data.progress && typeof data.progress === 'object') {
        percent = Math.round((data.progress.current / data.progress.total) * 100);
      }
      onProgress(percent);
    }
    
    // Wait 2 seconds before next poll
    await new Promise(resolve => setTimeout(resolve, 2000));
    return this.pollStatus(runId, token, onProgress);
  },

  async getAlphaSignals(token?: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/alpha/signals`, {
      headers: getHeaders(token)
    });
    if (!response.ok) {
      throw new Error('Failed to fetch alpha signals');
    }
    return response.json();
  },

  async getAlphaSimulations(token: string): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/alpha/simulations`, {
      headers: getHeaders(token)
    });
    if (!response.ok) {
      throw new Error('Failed to fetch alpha simulations');
    }
    return response.json();
  },

  async runAlphaSimulation(token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/alpha/run-simulation`, {
      method: 'POST',
      headers: getHeaders(token),
    });
    if (!response.ok) {
      throw new Error('Failed to trigger alpha simulation');
    }
    return response.json();
  },

  async getAlphaInsights(token?: string): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/alpha/insights`, {
      headers: getHeaders(token)
    });
    if (!response.ok) {
      throw new Error('Failed to fetch alpha insights');
    }
    return response.json();
  },

  // --- Demo Magic Link Methods ---

  async validateDemoToken(token: string): Promise<DemoValidationResponse> {
    const response = await fetch(`${API_BASE_URL}/demo/magic-link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    });
    return response.json();
  },

  async getDemoUsage(): Promise<DemoUsageResponse> {
    const demoToken = localStorage.getItem('demo_token');
    if (!demoToken) {
      return { remaining: 0, limit: 0, used: 0, expired: true };
    }
    const response = await fetch(`${API_BASE_URL}/demo/usage`, {
      headers: {
        'Content-Type': 'application/json',
        'X-Demo-Token': demoToken,
      },
    });
    if (!response.ok) {
      return { remaining: 0, limit: 0, used: 0, expired: true };
    }
    return response.json();
  },

  async decrementDemoUsage(): Promise<{ success: boolean; remaining: number }> {
    const demoToken = localStorage.getItem('demo_token');
    if (!demoToken) {
      return { success: false, remaining: 0 };
    }
    const response = await fetch(`${API_BASE_URL}/demo/use-run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Demo-Token': demoToken,
      },
    });
    if (!response.ok) {
      return { success: false, remaining: 0 };
    }
    const data = await response.json();
    // Update local cache
    localStorage.setItem('demo_remaining', String(data.remaining));
    return data;
  },
};
