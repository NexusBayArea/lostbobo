// SimHPC Platform Types

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'user' | 'demo_partner' | 'admin';
  plan: 'free' | 'starter' | 'professional' | 'enterprise';
  createdAt: string;
}

export interface SimulationConfig {
  id?: string;
  name: string;
  meshFile?: string;
  parameters: SimulationParameter[];
  solver: 'mfem' | 'sundials';
  gpuEnabled: boolean;
  robustnessEnabled: boolean;
  numRuns?: number;
}

export interface SimulationParameter {
  name: string;
  value: number;
  unit?: string;
  min?: number;
  max?: number;
  perturbable: boolean;
}

export interface SimulationResult {
  id: string;
  configId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  maxTemperature?: number;
  minTemperature?: number;
  peakStress?: number;
  convergenceTime?: number;
  meshElements?: number;
  residualTolerance?: number;
  createdAt: string;
  completedAt?: string;
}

export interface RobustnessSummary {
  baselineResult: SimulationResult;
  allResults: SimulationResult[];
  sensitivityRanking: SensitivityMetric[];
  confidenceInterval: number;
  variance: number;
  standardDeviation: number;
  nonConvergentCount: number;
  runCount: number;
  samplingMethod: string;
  computationTime: number;
}

export interface SensitivityMetric {
  parameterName: string;
  influenceCoefficient: number;
  varianceContribution: number;
  rank: number;
}

export interface AIReport {
  id: string;
  simulationId: string;
  sections: AIReportSection[];
  generatedAt: string;
  disclaimer: string;
}

export interface AIReportSection {
  title: string;
  content: string;
  order: number;
}

export interface PricingPlan {
  id: string;
  name: string;
  description: string;
  price: number;
  priceUnit: string;
  features: string[];
  notIncluded?: string[];
  highlighted?: boolean;
  cta: string;
}
