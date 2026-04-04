export interface SimulationParams {
  iterations: number;
  grid_size: number;
  thermal_conductivity: number;
  youngs_modulus: number;
  heat_flux: number;
  cooling_coefficient: number;
  timeout: number;
  seed?: number;
}

export interface SimulationResult {
  run_id: string;
  progress: number;
  thermal_drift: number;
  pressure_spike: boolean;
  runtime_ms: number;
}

export interface UsageStats {
  used: number;
  limit: number;
  remaining: number;
}
