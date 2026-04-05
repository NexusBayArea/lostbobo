import { SimulationRow } from './db';

export interface SimulationUpdate {
  id: string;
  status: SimulationRow['status'];
  scenario_name: string | null;
  job_id: string | null;
}

export interface SimulationInsert {
  id: string;
  user_id: string;
  status: SimulationRow['status'];
  created_at: string;
}
