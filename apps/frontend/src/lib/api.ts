
// src/lib/api.ts
import { toast } from 'sonner';

const API_BASE_URL = '/api/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY || '';

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

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    showToast: boolean = true
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

    const config: RequestInit = {
      ...options,
      headers: {
        ...getHeaders(options.headers?.Authorization?.split(' ')[1]),
        ...options.headers,
      },
      credentials: 'include',
    };

    try {
      const response = await fetch(url, config);
      const contentType = response.headers.get('content-type');
      let data: any;

      if (contentType?.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMessage = data?.error || data?.message || data?.detail || `HTTP ${response.status}`;
        
        if (showToast) {
          toast.error(errorMessage, { duration: 6000 });
        }
        throw new Error(errorMessage);
      }

      return data as T;
    } catch (error: any) {
      console.error(`API Error [${endpoint}]:`, error);
      if (showToast && !error.message?.includes('Failed to fetch')) {
        toast.error(error.message || 'Request failed');
      }
      throw error;
    }
  }

  async get<T>(endpoint: string, showToast = true): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' }, showToast);
  }

  async post<T>(endpoint: string, body: any, showToast = true): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }, showToast);
  }

  async put<T>(endpoint: string, body: any, showToast = true): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body: JSON.stringify(body) }, showToast);
  }

  async delete<T>(endpoint: string, showToast = true): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' }, showToast);
  }
}

export const api = new ApiClient();

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
  plan: 'free' | 'professional' | 'enterprise' | 'demo_general' | 'demo_full';
  email?: string;
  subscription_status: string;
  stripe_customer_id?: string;
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
  }
};
