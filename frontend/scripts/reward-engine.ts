export interface CIOutcome {
  success: boolean;
  durationMs: number;
  cacheHit: boolean;
  rerunCount: number;
}

export function computeReward(outcome: CIOutcome): number {
  let reward = 0;

  reward += outcome.success ? 100 : -200;

  reward -= outcome.durationMs / 1000;

  if (outcome.cacheHit) reward += 20;

  reward -= outcome.rerunCount * 15;

  return Math.round(reward);
}
