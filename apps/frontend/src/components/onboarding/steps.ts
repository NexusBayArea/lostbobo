import type { OnboardingState } from './onboardingReducer';

export interface StepDefinition {
  id: string;
  type: 'modal' | 'tooltip';
  title?: string;
  content: string;
  cta?: string;
  target?: string;
  event?: string;
  next?: string;
  condition?: (state: OnboardingState) => boolean;
}

export const steps: StepDefinition[] = [
  {
    id: 'welcome',
    type: 'modal',
    title: 'Welcome to SimHPC',
    content: 'Run your first simulation in minutes. This quick guide will walk you through the essentials.',
    cta: 'Start Guided Setup',
    next: 'explore_dashboard',
  },
  {
    id: 'explore_dashboard',
    type: 'tooltip',
    target: '[data-onboarding="sidebar"]',
    content: 'This is your mission control. Navigate between Live Center, Notebook, and settings from here.',
    event: 'dashboard_explored',
    next: 'run_simulation',
  },
  {
    id: 'run_simulation',
    type: 'tooltip',
    target: '[data-onboarding="run-button"]',
    content: 'Launch your first simulation from here. Choose a template or start from scratch.',
    event: 'simulation_started',
    next: 'monitor_jobs',
  },
  {
    id: 'monitor_jobs',
    type: 'tooltip',
    target: '[data-onboarding="job-queue"]',
    content: 'Monitor your running jobs here. Watch real-time telemetry and convergence metrics.',
    event: 'job_monitored',
    next: 'view_results',
  },
  {
    id: 'view_results',
    type: 'tooltip',
    target: '[data-onboarding="results-panel"]',
    content: 'Your simulation results appear here with confidence intervals and AI-generated reports.',
    event: 'results_viewed',
    next: 'try_notebook',
  },
  {
    id: 'try_notebook',
    type: 'tooltip',
    target: '[data-onboarding="notebook-link"]',
    content: 'Open your Engineer Notebook to document experiments, track parameters, and compare results.',
    event: 'notebook_opened',
    next: 'try_live_center',
  },
  {
    id: 'try_live_center',
    type: 'tooltip',
    target: '[data-onboarding="live-center-link"]',
    content: 'Visit the Live Center for real-time fleet monitoring, telemetry, and AI-guided interventions.',
    event: 'live_center_opened',
    next: 'complete',
  },
  {
    id: 'complete',
    type: 'modal',
    title: "You're All Set!",
    content: 'You now know the basics. Start running simulations and explore advanced features at your own pace.',
    cta: 'Start Simulating',
  },
];
