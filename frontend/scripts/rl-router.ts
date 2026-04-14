import { selectAction } from "./policy-agent";
import { getCIState, CIStateInput } from "./ci-state";
import { ActionConfig } from "./ci-actions";

interface RouteContext {
  branch: string;
  dagHash: string;
  riskScore: number;
}

export function routeCI(context: RouteContext): { action: string; stateKey: string; config: any } {
  const stateKey = getCIState({
    branch: context.branch,
    dagHash: context.dagHash,
    changeRisk: context.riskScore,
  });

  const action = selectAction(stateKey);
  const config = ActionConfig[action as keyof typeof ActionConfig];

  console.log(`🧠 RL CI decision: ${action} (state: ${stateKey})`);

  return { action, stateKey, config };
}