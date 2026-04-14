import { updatePolicy } from "./policy-update.js";

interface PolicyUpdateInput {
  stateKey: string;
  action: string;
  success: boolean;
  durationMs: number;
  cacheHit: boolean;
  rerunCount: number;
}

const input = JSON.parse(process.argv[2] || "{}") as PolicyUpdateInput;

if (!input.stateKey || !input.action) {
  console.error("Usage: node scripts/update-policy-runner.ts '{\"stateKey\":\"...\",\"action\":\"FAST\",\"success\":true,\"durationMs\":5000,\"cacheHit\":true,\"rerunCount\":0}'");
  process.exit(1);
}

updatePolicy(input.stateKey, input.action as any, {
  success: input.success,
  durationMs: input.durationMs,
  cacheHit: input.cacheHit,
  rerunCount: input.rerunCount,
});

console.log("✅ Policy updated");