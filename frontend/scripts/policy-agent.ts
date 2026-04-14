import { loadPolicy } from "./policy-store";
import { Actions, CIAction } from "./ci-actions";

export function selectAction(stateKey: string, epsilon = 0.1): CIAction {
  const policy = loadPolicy();

  if (!policy[stateKey]) {
    policy[stateKey] = { FAST: 0, BALANCED: 0, FULL: 0 };
  }

  if (Math.random() < epsilon) {
    const randomAction = Actions[Math.floor(Math.random() * Actions.length)];
    return randomAction;
  }

  const state = policy[stateKey];
  const best = Object.entries(state).sort((a, b) => b[1] - a[1])[0][0] as CIAction;
  return best;
}