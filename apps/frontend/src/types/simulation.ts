export interface SensitivityEntry {
  parameter_name: string;
  influence_coefficient: number; // 0.0 to 1.0
  rank: number;
}

export interface SimulationStats {
  variance: number;
  std_dev: number;
  confidence_interval: number;
  non_convergent_count: number;
}

export interface AIReport {
  report_id: string;
  summary: string;
  recommendations: string[];
  risk_level: 'low' | 'medium' | 'high';
  generated_at: string;
}

export interface SimulationResults {
  baseline: {
    max_temperature: number;
    peak_stress: number;
    convergence_time_sec: number;
  };
  sensitivity: SensitivityEntry[];
  stats: SimulationStats;
  ai_report?: AIReport;
}
