import { loadPolicy, savePolicy } from "./policy-store";
import { computeReward } from "./reward-engine";
import { CIAction } from "./ci-actions";
import { CIOutcome } from "./reward-engine";

export function updatePolicy(stateKey: string, action: CIAction, outcome: CIOutcome): void {
  const policy = loadPolicy();

  const reward = computeReward(outcome);

  if (!policy[stateKey]) {
    policy[stateKey] = { FAST: 0, BALANCED: 0, FULL: 0 };
  }

  const alpha = 0.2;
  const oldQ = policy[stateKey][action];
  const newQ = (1 - alpha) * oldQ + alpha * reward;

  policy[stateKey][action] = Math.round(newQ * 100) / 100;

  savePolicy(policy);
}