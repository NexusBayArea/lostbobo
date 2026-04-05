export interface SimulationRow {
  id: string;
  user_id: string;
  job_id: string | null;
  scenario_name: string | null;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  result_summary: Record<string, unknown> | null;
  gpu_result: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  plan: 'free' | 'pro' | 'enterprise';
  created_at: string;
  updated_at: string;
}

export interface Certificate {
  id: string;
  simulation_id: string;
  user_id: string;
  signed_url: string | null;
  created_at: string;
}

export interface Document {
  id: string;
  user_id: string;
  title: string;
  content: string;
  created_at: string;
}

export interface OnboardingState {
  step: number;
  completed: boolean;
  last_seen: string | null;
}
