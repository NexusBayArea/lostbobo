import { toast } from 'sonner';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'https://api.simhpc.com/api/v1').replace(/\/$/, '');
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

export interface RunStatusResponse {
  run_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  results?: any;
  error?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // ... (rest of the class remains the same, I'll just add the missing methods)
  // Wait, I should probably rewrite the class to be complete.

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    showToast: boolean = true
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

    const config: RequestInit = {
      ...options,
      headers: {
        ...getHeaders(options.headers?.['Authorization']?.split(' ')[1]),
        ...options.headers,
      } as any,
      credentials: 'include',
    };

    try {
      const response = await fetch(url, config);
      const contentType = response.headers.get('content-type');

      if (contentType?.includes('application/pdf')) {
        return await response.blob() as any;
      }

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

  async exportPdf(runId: string, token: string): Promise<Blob> {
    return this.request<Blob>(`/reports/${runId}/pdf`, {
      headers: { Authorization: `Bearer ${token}` }
    }, false);
  }

  async warmPod(token: string): Promise<any> {
    return this.request<any>('/admin/fleet/warm', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    }, true);
  }

  async getFleetReadiness(token: string): Promise<any> {
    return this.request<any>('/admin/fleet/readiness', {
      headers: { Authorization: `Bearer ${token}` }
    }, false);
  }

  async listRuns(token: string): Promise<RunStatusResponse[]> {
    return this.request<RunStatusResponse[]>('/robustness/history', {
      headers: { Authorization: `Bearer ${token}` }
    }, false);
  }

  async pollStatus(runId: string, token: string): Promise<RunStatusResponse> {
    return this.request<RunStatusResponse>(`/robustness/status/${runId}`, {
      headers: { Authorization: `Bearer ${token}` }
    }, false);
  }

  async startRobustnessRun(body: any, token: string): Promise<{ run_id: string }> {
    return this.request<{ run_id: string }>('/robustness/run', {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { Authorization: `Bearer ${token}` }
    }, true);
  }

  // Compatibility methods for MLMonitoringDashboard
  async fetch(endpoint: string, options: any = {}): Promise<any> {
    return this.request<any>(endpoint, options, false);
  }

  // Original methods preserved
  async getTrace(): Promise<any> { return this.get('/admin/observability', false); }
  async replayFailed(): Promise<any> { return this.post('/admin/replay', {}); }
  async replayFull(): Promise<any> { return this.post('/admin/replay/full', {}); }
  async getFleetStatus(token?: string): Promise<any> {
    return this.request<any>('/admin/fleet', { headers: token ? { Authorization: `Bearer ${token}` } : {} }, false);
  }
  async getFleetMetrics(token?: string): Promise<any> {
    return this.request<any>('/admin/fleet/metrics', { headers: token ? { Authorization: `Bearer ${token}` } : {} }, false);
  }

  getUrl(endpoint: string): string {
    const cleanEndpoint = endpoint.replace(/^\/api\/v1/, '');
    return `${API_BASE_URL}${cleanEndpoint.startsWith('/') ? '' : '/'}${cleanEndpoint}`;
  }
}

export const api = new ApiClient();
export default api;
