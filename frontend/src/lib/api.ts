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
        ...getHeaders(options.headers?.['Authorization']?.split(' ')[1]),
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

  async getTrace(): Promise<any> {
    return this.request<any>('/admin/observability', { method: 'GET' }, false);
  }

  async replayFailed(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/admin/replay', { method: 'POST' }, false);
  }

  async replayFull(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/admin/replay/full', { method: 'POST' }, false);
  }

  async getFleetStatus(token?: string): Promise<any> {
    return this.request<any>('/admin/fleet', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    }, false);
  }

  async getFleetMetrics(token?: string): Promise<any> {
    return this.request<any>('/admin/fleet/metrics', {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    }, false);
  }

  async stopPod(token: string, podId: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/admin/fleet/pod/${podId}/stop`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    }, false);
  }

  async terminatePod(token: string, podId: string): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/admin/fleet/pod/${podId}/terminate`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    }, false);
  }

  async getUsage(): Promise<any> {
    return this.request<any>('/admin/usage', { method: 'GET' }, false);
  }

  async wakePod(token: string): Promise<any> {
    const podId = import.meta.env.VITE_RUNPOD_POD_ID;
    const apiKey = import.meta.env.VITE_RUNPOD_API_KEY;
    if (!podId || !apiKey) {
      throw new Error('RunPod not configured');
    }
    const response = await fetch(`https://api.runpod.io/v2/pod/${podId}/resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      }
    });
    return response.json();
  }

  async checkPodStatus(token: string): Promise<any> {
    const podId = import.meta.env.VITE_RUNPOD_POD_ID;
    const apiKey = import.meta.env.VITE_RUNPOD_API_KEY;
    if (!podId || !apiKey) {
      throw new Error('RunPod not configured');
    }
    const response = await fetch(`https://api.runpod.io/v2/pod/${podId}`, {
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    });
    return response.json();
  }
}

export const api = new ApiClient();
