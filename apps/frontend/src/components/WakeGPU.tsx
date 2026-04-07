/// <reference types="vite/client" />
/**
 * WakeGPU — Admin dashboard component for Option C pod management.
 *
 * Shows pod state (running / stopped / warming) and lets the admin
 * wake the pod before a demo with one click.
 *
 * Props:
 *   adminSecret  — from env or admin session
 *
 * Usage in your admin dashboard:
 *   import WakeGPU from "@/components/WakeGPU";
 *   <WakeGPU adminSecret={import.meta.env.VITE_ADMIN_SECRET} />
 */

import { useState, useEffect, useCallback, useRef } from "react";

const API_BASE = (import.meta.env.VITE_API_URL as string)?.replace(/\/$/, "");

type PodState = "unknown" | "running" | "stopped" | "warming" | "creating" | "error";

interface ReadinessResponse {
  ready:        boolean;
  running_pods: number;
  stopped_pods: number;
  worker_live:  boolean;
  queue_depth:  number;
  pod_ids:      string[];
  message:      string;
}

interface WarmResponse {
  status:      string;
  pod_id?:     string;
  message:     string;
  cost_per_hr?: number;
}

const STATE_LABEL: Record<PodState, string> = {
  unknown:  "Checking...",
  running:  "Running — ready",
  stopped:  "Stopped — will wake on job",
  warming:  "Warming up (~90s)...",
  creating: "Creating new pod (~3 min)...",
  error:    "Error",
};

const STATE_COLOR: Record<PodState, string> = {
  unknown:  "var(--color-text-secondary)",
  running:  "var(--color-text-success)",
  stopped:  "var(--color-text-warning)",
  warming:  "var(--color-text-info)",
  creating: "var(--color-text-info)",
  error:    "var(--color-text-danger)",
};

// Dot indicator
function StatusDot({ state }: { state: PodState }) {
  const color = STATE_COLOR[state];
  const pulse = state === "warming" || state === "creating" || state === "running";
  return (
    <span style={{ position: "relative", display: "inline-flex", alignItems: "center" }}>
      <span
        style={{
          width: 10,
          height: 10,
          borderRadius: "50%",
          background: color,
          display: "inline-block",
          animation: pulse ? "statusPulse 2s ease-in-out infinite" : undefined,
        }}
      />
    </span>
  );
}

export default function WakeGPU({ adminSecret }: { adminSecret: string }) {
  const [podState,   setPodState]   = useState<PodState>("unknown");
  const [message,    setMessage]    = useState("");
  const [podId,      setPodId]      = useState<string | null>(null);
  const [costPerHr,  setCostPerHr]  = useState<number | null>(null);
  const [queueDepth, setQueueDepth] = useState(0);
  const [loading,    setLoading]    = useState(false);
  const [warmProgress, setWarmProgress] = useState(0); // 0-100

  const pollRef  = useRef<ReturnType<typeof setInterval> | null>(null);
  const warmRef  = useRef<ReturnType<typeof setInterval> | null>(null);

  const headers = { "X-Admin-Secret": adminSecret, "Content-Type": "application/json" };

  // ── Poll readiness ────────────────────────────────────────────────────────
  const checkReadiness = useCallback(async () => {
    try {
      const res  = await fetch(`${API_BASE}/api/v1/admin/fleet/readiness`, { headers });
      if (!res.ok) return;
      const data: ReadinessResponse = await res.json();

      setMessage(data.message);
      setQueueDepth(data.queue_depth);
      if (data.pod_ids?.length) setPodId(data.pod_ids[0]);

      if (data.ready) {
        setPodState("running");
        stopPolling();
        setWarmProgress(100);
      } else if (data.running_pods > 0 && !data.worker_live) {
        setPodState("warming");
      } else if (data.stopped_pods > 0) {
        setPodState("stopped");
      }
    } catch {
      // network hiccup — keep polling
    }
  }, [adminSecret]);

  const stopPolling = () => {
    if (pollRef.current)  clearInterval(pollRef.current);
    if (warmRef.current)  clearInterval(warmRef.current);
    pollRef.current = null;
    warmRef.current = null;
  };

  // Initial readiness check on mount
  useEffect(() => {
    checkReadiness();
    pollRef.current = setInterval(checkReadiness, 5000);
    return () => stopPolling();
  }, [checkReadiness]);

  // ── Warm pod ──────────────────────────────────────────────────────────────
  const handleWarm = async () => {
    setLoading(true);
    setWarmProgress(0);
    try {
      const res  = await fetch(`${API_BASE}/api/v1/admin/fleet/warm`, {
        method: "POST",
        headers,
      });
      const data: WarmResponse = await res.json();

      setMessage(data.message);
      if (data.pod_id)     setPodId(data.pod_id);
      if (data.cost_per_hr) setCostPerHr(data.cost_per_hr);

      if (data.status === "already_running") {
        setPodState("running");
        setWarmProgress(100);
        return;
      }

      if (data.status === "warming") {
        setPodState("warming");
        // Simulate progress over 90 seconds
        let progress = 0;
        warmRef.current = setInterval(() => {
          progress = Math.min(progress + 1.2, 95); // cap at 95 until confirmed
          setWarmProgress(progress);
        }, 1080); // 90s / ~83 ticks ≈ 1.1s per tick

      } else if (data.status === "creating") {
        setPodState("creating");
        let progress = 0;
        warmRef.current = setInterval(() => {
          progress = Math.min(progress + 0.55, 95);
          setWarmProgress(progress);
        }, 1000);
      } else if (data.status === "error") {
        setPodState("error");
      }
    } catch (e) {
      setPodState("error");
      setMessage("Could not reach the API.");
    } finally {
      setLoading(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  const isWarming   = podState === "warming" || podState === "creating";
  const canWarm     = podState === "stopped" || podState === "error" || podState === "unknown";
  const isRunning   = podState === "running";

  return (
    <>
      <style>{`
        @keyframes statusPulse {
          0%,100% { opacity: 1; }
          50%      { opacity: 0.45; }
        }
        .wake-card {
          border: 1px solid var(--color-border-tertiary);
          border-radius: var(--border-radius-lg);
          padding: 20px 24px;
          display: flex;
          flex-direction: column;
          gap: 14px;
          max-width: 420px;
        }
        .wake-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .wake-title {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-primary);
        }
        .wake-badge {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--color-text-secondary);
          background: var(--color-background-secondary);
          border: 1px solid var(--color-border-tertiary);
          border-radius: 20px;
          padding: 3px 10px;
        }
        .wake-message {
          font-size: 13px;
          color: var(--color-text-secondary);
          line-height: 1.5;
        }
        .wake-meta {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: var(--color-text-tertiary);
        }
        .progress-bar-track {
          width: 100%;
          height: 4px;
          background: var(--color-background-secondary);
          border-radius: 2px;
          overflow: hidden;
        }
        .progress-bar-fill {
          height: 100%;
          background: var(--color-text-info);
          border-radius: 2px;
          transition: width 1s linear;
        }
        .wake-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          height: 36px;
          padding: 0 16px;
          border-radius: var(--border-radius-md);
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          border: 1px solid transparent;
          transition: opacity 0.15s;
        }
        .wake-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .wake-btn-primary {
          background: var(--color-text-primary);
          color: var(--color-background-primary);
        }
        .wake-btn-secondary {
          background: transparent;
          color: var(--color-text-secondary);
          border-color: var(--color-border-secondary);
        }
        .wake-btn:not(:disabled):hover { opacity: 0.8; }
      `}</style>

      <div className="wake-card">
        {/* Header */}
        <div className="wake-header">
          <span className="wake-title">GPU Pod</span>
          <span className="wake-badge">
            <StatusDot state={podState} />
            <span style={{ color: STATE_COLOR[podState] }}>
              {STATE_LABEL[podState]}
            </span>
          </span>
        </div>

        {/* Progress bar (shown while warming) */}
        {isWarming && (
          <div>
            <div className="progress-bar-track">
              <div
                className="progress-bar-fill"
                style={{ width: `${warmProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Message */}
        <p className="wake-message">{message || "Checking pod status..."}</p>

        {/* Meta */}
        <div className="wake-meta">
          {podId && <span>Pod: {podId.slice(0, 14)}…</span>}
          {costPerHr != null && isRunning && (
            <span>${costPerHr.toFixed(3)}/hr</span>
          )}
          {queueDepth > 0 && <span>Queue: {queueDepth} jobs</span>}
          {podState === "stopped" && (
            <span>Idle cost: ~$0.005/hr</span>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 8 }}>
          {canWarm && (
            <button
              className="wake-btn wake-btn-primary"
              onClick={handleWarm}
              disabled={loading}
            >
              {loading ? "Requesting..." : "Wake GPU"}
            </button>
          )}
          {isWarming && (
            <button
              className="wake-btn wake-btn-secondary"
              onClick={checkReadiness}
            >
              Check now
            </button>
          )}
          {isRunning && (
            <span style={{ fontSize: 13, color: "var(--color-text-success)", alignSelf: "center" }}>
              Ready for simulations
            </span>
          )}
        </div>

        {/* Cost note */}
        {(podState === "stopped") && (
          <p style={{ fontSize: 11, color: "var(--color-text-tertiary)", margin: 0 }}>
            Pod is stopped — disk and Network Volume preserved.
            Wake ~90s before your demo.
          </p>
        )}
      </div>
    </>
  );
}
