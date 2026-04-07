/// <reference types="vite/client" />
/**
 * SimHPC API Client
 *
 * Single source of truth for all frontend → backend communication.
 * Reads VITE_API_URL from environment so the same build works against:
 *   - Local dev:   http://localhost:8000
 *   - RunPod:      https://73atszmbozf16d-8000.proxy.runpod.net
 *   - Production:  https://api.simhpc.com
 *
 * Usage in .env.local:
 *   VITE_API_URL=http://localhost:8000
 *
 * Usage in Vercel dashboard (Environment Variables):
 *   VITE_API_URL=https://api.simhpc.com
 *
 * Never hardcode the backend URL anywhere else in the frontend.
 */

// ─── Base URL ──────────────────────────────────────────────────────────────

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(
  /\/$/,
  ""
);

if (!API_BASE) {
  console.error(
    "[SimHPC] VITE_API_URL is not set. " +
      "Add it to .env.local for dev or Vercel Environment Variables for prod.\n" +
      "Example: VITE_API_URL=http://localhost:8000"
  );
}

// ─── Types ─────────────────────────────────────────────────────────────────

export interface ApiError {
  message: string;
  status: number;
  detail?: unknown;
}

export interface JobResponse {
  run_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: { current: number; total: number };
  created_at: string;
  completed_at?: string;
  error?: string;
  results?: Record<string, unknown>;
  ai_report?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface SystemStatus {
  mercury: "online" | "offline";
  runpod: "online" | "offline";
  supabase: "online" | "offline";
  worker: "online" | "offline";
  timestamp: string;
}

export interface RobustnessRunRequest {
  config: {
    parameters: Array<{
      name: string;
      base_value: number;
      unit?: string;
      perturbable?: boolean;
      min_value?: number;
      max_value?: number;
    }>;
    num_runs?: number;
    sampling_method?: "±5%" | "±10%" | "latin_hypercube" | "sobol" | "monte_carlo";
    random_seed?: number;
  };
}

export interface FleetStatus {
  pods: number;
  pod_ids: string[];
  queue: number;
  cost_today: number;
  timestamp: string;
}

// ─── Core Fetch Wrapper ─────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string; apiKey?: string } = {}
): Promise<T> {
  const { token, apiKey, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (apiKey) headers["X-API-Key"] = apiKey;

  const url = `${API_BASE}${path}`;

  let response: Response;
  try {
    response = await fetch(url, { ...fetchOptions, headers });
  } catch (err) {
    throw {
      message: `Network error — cannot reach ${API_BASE}. Is the backend running?`,
      status: 0,
      detail: err,
    } satisfies ApiError;
  }

  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    throw {
      message: `API error ${response.status}: ${response.statusText}`,
      status: response.status,
      detail,
    } satisfies ApiError;
  }

  // Handle 204 No Content
  if (response.status === 204) return undefined as unknown as T;

  return response.json() as Promise<T>;
}

// ─── Health ─────────────────────────────────────────────────────────────────

export const api = {
  /**
   * Ping the backend. Use this on app mount to verify connectivity.
   */
  health(): Promise<SystemStatus> {
    return apiFetch<SystemStatus>("/api/v1/system/status");
  },

  // ─── Simulation ────────────────────────────────────────────────────────

  simulation: {
    /**
     * Submit a robustness analysis run.
     * Returns run_id immediately; poll status() for results.
     */
    run(body: RobustnessRunRequest, token: string): Promise<{ run_id: string }> {
      return apiFetch("/api/v1/robustness/run", {
        method: "POST",
        body: JSON.stringify(body),
        token,
      });
    },

    /**
     * Poll job status by run_id.
     */
    status(runId: string, token: string): Promise<JobResponse> {
      return apiFetch(`/api/v1/robustness/status/${runId}`, { token });
    },

    /**
     * Cancel a running job.
     */
    cancel(runId: string, token: string): Promise<{ cancelled: boolean }> {
      return apiFetch(`/api/v1/robustness/cancel/${runId}`, {
        method: "POST",
        token,
      });
    },

    /**
     * List the current user's simulation history.
     */
    history(token: string): Promise<JobResponse[]> {
      return apiFetch("/api/v1/robustness/history", { token });
    },
  },

  // ─── Reports ───────────────────────────────────────────────────────────

  reports: {
    /**
     * Generate an AI report for a completed run.
     */
    generate(runId: string, token: string): Promise<{ report: Record<string, unknown> }> {
      return apiFetch("/api/v1/reports/generate", {
        method: "POST",
        body: JSON.stringify({ run_id: runId }),
        token,
      });
    },

    /**
     * Download the PDF for a completed run.
     * Returns a Blob you can URL.createObjectURL() to trigger download.
     */
    async downloadPdf(runId: string, token: string): Promise<Blob> {
      const response = await fetch(`${API_BASE}/api/v1/reports/${runId}/pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        throw {
          message: `PDF download failed: ${response.statusText}`,
          status: response.status,
        } satisfies ApiError;
      }
      return response.blob();
    },
  },

  // ─── Demo (magic link) ─────────────────────────────────────────────────

  demo: {
    /**
     * Validate a magic-link demo token and get session info.
     */
    validate(token: string): Promise<{
      valid: boolean;
      remaining?: number;
      usage_limit?: number;
      email?: string;
      reason?: string;
    }> {
      return apiFetch("/api/v1/demo/validate", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
    },

    /**
     * Consume one demo run. Call before submitting a simulation.
     */
    useRun(token: string): Promise<{ success: boolean; remaining: number }> {
      return apiFetch("/api/v1/demo/use", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
    },
  },

  // ─── Admin (fleet management) ──────────────────────────────────────────

  admin: {
    /**
     * Get RunPod fleet status. Requires admin secret header.
     */
    fleet(adminSecret: string): Promise<{ status: string; fleet: FleetStatus }> {
      return apiFetch("/api/v1/admin/fleet", {
        headers: { "X-Admin-Secret": adminSecret },
      });
    },

    /**
     * Get today's cost summary.
     */
    cost(adminSecret: string): Promise<{ status: string; cost: Record<string, unknown> }> {
      return apiFetch("/api/v1/admin/fleet/cost", {
        headers: { "X-Admin-Secret": adminSecret },
      });
    },

    /**
     * Stop a running pod (preserves disk, stops GPU billing).
     */
    stopPod(podId: string, adminSecret: string): Promise<{ status: string }> {
      return apiFetch(`/api/v1/admin/fleet/pod/${podId}/stop`, {
        method: "POST",
        headers: { "X-Admin-Secret": adminSecret },
      });
    },

    /**
     * Terminate a pod permanently (deletes disk).
     */
    terminatePod(podId: string, adminSecret: string): Promise<{ status: string }> {
      return apiFetch(`/api/v1/admin/fleet/pod/${podId}/terminate`, {
        method: "POST",
        headers: { "X-Admin-Secret": adminSecret },
      });
    },
  },

  // ─── WebSocket helper ──────────────────────────────────────────────────

  /**
   * Open a WebSocket connection to stream live telemetry for a run.
   *
   * Usage:
   *   const ws = api.telemetrySocket("run-id-here", token);
   *   ws.onmessage = (e) => console.log(JSON.parse(e.data));
   *   ws.onclose = () => console.log("done");
   */
  telemetrySocket(runId: string, token: string): WebSocket {
    const wsBase = API_BASE?.replace(/^http/, "ws") ?? "ws://localhost:8000";
    return new WebSocket(`${wsBase}/api/v1/ws/telemetry/${runId}?token=${token}`);
  },
};

export default api;
