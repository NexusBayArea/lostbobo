import crypto from "crypto";
import fs from "fs";
import path from "path";

const POLICY_FILE = path.join(import.meta.dirname, "ci-policy.json");

type CIAction = "FAST" | "BALANCED" | "FULL";
const Actions: CIAction[] = ["FAST", "BALANCED", "FULL"];

const ActionConfig: Record<CIAction, { cacheDag: boolean; typecheck: boolean; fullBuild: boolean }> = {
  FAST: { cacheDag: true, typecheck: false, fullBuild: false },
  BALANCED: { cacheDag: true, typecheck: true, fullBuild: false },
  FULL: { cacheDag: false, typecheck: true, fullBuild: true },
};

interface CIOutcome {
  success: boolean;
  durationMs: number;
  cacheHit: boolean;
  rerunCount: number;
}

function computeReward(outcome: CIOutcome): number {
  let reward = 0;
  reward += outcome.success ? 100 : -200;
  reward -= outcome.durationMs / 1000;
  if (outcome.cacheHit) reward += 20;
  reward -= outcome.rerunCount * 15;
  return Math.round(reward);
}

type QTable = Record<string, Record<string, number>>;

function loadPolicy(): QTable {
  if (!fs.existsSync(POLICY_FILE)) return {};
  return JSON.parse(fs.readFileSync(POLICY_FILE, "utf-8"));
}

function savePolicy(policy: QTable): void {
  fs.writeFileSync(POLICY_FILE, JSON.stringify(policy, null, 2));
}

function getCIState(input: { branch: string; dagHash: string; changeRisk: number }): string {
  const data = `${input.branch}:${input.dagHash}:${input.changeRisk}`;
  return crypto.createHash("sha256").update(data).digest("hex").slice(0, 12);
}

function selectAction(stateKey: string, epsilon = 0.1): CIAction {
  const policy = loadPolicy();
  if (!policy[stateKey]) {
    policy[stateKey] = { FAST: 0, BALANCED: 0, FULL: 0 };
  }
  if (Math.random() < epsilon) {
    return Actions[Math.floor(Math.random() * Actions.length)];
  }
  const state = policy[stateKey];
  return Object.entries(state).sort((a, b) => b[1] - a[1])[0][0] as CIAction;
}

function updatePolicy(stateKey: string, action: CIAction, outcome: CIOutcome): void {
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

const mode = process.argv[2];

if (mode === "route") {
  const branch = process.argv[3] || "main";
  const dagHash = process.argv[4] || "default";
  const riskScore = parseFloat(process.argv[5] || "0.5");
  
  const stateKey = getCIState({ branch, dagHash, changeRisk: riskScore });
  const action = selectAction(stateKey);
  const config = ActionConfig[action];
  
  console.log(JSON.stringify({ action, stateKey, config }));
} else if (mode === "update") {
  const input = JSON.parse(process.argv[3] || "{}");
  updatePolicy(input.stateKey, input.action, {
    success: input.success,
    durationMs: input.durationMs,
    cacheHit: input.cacheHit,
    rerunCount: input.rerunCount,
  });
  console.log("✅ Policy updated");
} else {
  console.log("Usage: ts-node scripts/rl-ci.ts route <branch> <dagHash> <riskScore>");
  console.log("       ts-node scripts/rl-ci.ts update '{\"stateKey\":\"...\",\"action\":\"FAST\",\"success\":true,\"durationMs\":5000,\"cacheHit\":true,\"rerunCount\":0}'");
}
