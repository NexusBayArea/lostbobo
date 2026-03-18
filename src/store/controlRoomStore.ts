import { create } from 'zustand';

export interface ActiveSimulation {
  run_id: string;
  model: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  runtime_sec: number;
  solver_health: 'optimal' | 'stiff' | 'diverging';
  created_at: string;
}

export interface Alert {
  alert_id: string;
  level: 'CRITICAL' | 'WARNING' | 'INFO';
  source: string;
  message: string;
  timestamp: string;
}

export interface Insight {
  insight_id: string;
  type: 'parameter_sensitivity' | 'optimization' | 'rag_discrepancy';
  message: string;
  recommended_action: string;
}

export interface Recommendation {
  id: string;
  label: string;
  description: string;
  isCompleted: boolean;
}

export interface TimelineEvent {
  id: string;
  type: 'SIMULATION_EVENT' | 'AUDIT_EVENT' | 'OPERATOR_ACTION' | 'SOLVER_STATE' | 'CERTIFICATION_EVENT';
  severity: 'info' | 'warning' | 'critical' | 'success';
  label: string;
  message?: string;
  timestamp: string;
}

export interface LineageData {
  nodes: { id: string; label: string; type: string }[];
  edges: { source: string; target: string }[];
}

interface ControlRoomState {
  activeSimulations: ActiveSimulation[];
  alerts: Alert[];
  insights: Insight[];
  recommendations: Recommendation[];
  timeline: TimelineEvent[];
  lineage: LineageData | null;
  systemStatus: {
    gpu_load: number;
    status: 'nominal' | 'degraded' | 'critical';
  };
  
  // Actions
  setFullState: (state: Partial<ControlRoomState>) => void;
  updateSimulation: (runId: string, updates: Partial<ActiveSimulation>) => void;
  addAlert: (alert: Alert) => void;
  addTimelineEvent: (event: TimelineEvent) => void;
  setLineage: (lineage: LineageData) => void;
}

export const useControlRoomStore = create<ControlRoomState>((set) => ({
  activeSimulations: [],
  alerts: [],
  insights: [],
  recommendations: [],
  timeline: [],
  lineage: null,
  systemStatus: {
    gpu_load: 0,
    status: 'nominal',
  },

  setFullState: (newState) => set((state) => ({ ...state, ...newState })),
  
  updateSimulation: (runId, updates) => set((state) => ({
    activeSimulations: state.activeSimulations.map((sim) => 
      sim.run_id === runId ? { ...sim, ...updates } : sim
    )
  })),

  addAlert: (alert) => set((state) => ({
    alerts: [alert, ...state.alerts].slice(0, 50) // Keep last 50
  })),

  addTimelineEvent: (event) => set((state) => ({
    timeline: [...state.timeline, event]
  })),

  setLineage: (lineage) => set({ lineage }),
}));
