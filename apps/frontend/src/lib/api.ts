
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

  async getUserProfile(token: string): Promise<UserProfile> {
    return this.request<UserProfile>('/user/profile', {
      headers: { Authorization: `Bearer ${token}` }
    });
  }

  async getUsage(token: string): Promise<{ used: number; limit: number; remaining: number }> {
    return this.request<{ used: number; limit: number; remaining: number }>('/simulations/usage', {
      headers: { Authorization: `Bearer ${token}` }
    });
  }

  async subscribe(plan: string, token: string): Promise<{ url: string }> {
    return this.request<{ url: string }>('/subscribe', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ plan }),
    });
  }

  async startRobustnessRun(config: any, token?: string): Promise<RunStatusResponse> {
    return this.request<RunStatusResponse>('/robustness/run', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
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
  }

  async getRunStatus(runId: string, token?: string): Promise<RunStatusResponse> {
    return this.request<RunStatusResponse>(`/robustness/status/${runId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
  }

  async listRuns(token?: string): Promise<any> {
    return this.request<any>('/robustness/runs', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
  }

  async getSamplingMethods(token?: string): Promise<any> {
    return this.request<any>('/sampling-methods', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
  }

  async cancelRobustnessRun(runId: string, token?: string): Promise<any> {
    return this.request<any>(`/robustness/cancel/${runId}`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
  }

  async exportPdf(runId: string, token?: string): Promise<Blob> {
    const url = `${this.baseUrl}/robustness/report/${runId}/pdf`;
    const response = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    });
    if (!response.ok) {
      throw new Error('Failed to export PDF');
    }
    return response.blob();
  }

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
    
    await new Promise(resolve => setTimeout(resolve, 2000));
    return this.pollStatus(runId, token, onProgress);
  }
}

export const api = new ApiClient();

