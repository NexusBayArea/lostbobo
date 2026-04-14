import { classifyChange } from "./change-classifier";

function dagKey(commit: string, dagHash: string): string {
  const crypto = require("crypto");
  return crypto.createHash("sha256").update(`${commit}:${dagHash}`).digest("hex");
}

async function getCachedDag(key: string): Promise<any> {
  return null;
}

async function setCachedDag(key: string, value: any): Promise<void> {
  const fs = require("fs");
  const cacheDir = ".dag-cache";
  if (!fs.existsSync(cacheDir)) fs.mkdirSync(cacheDir, { recursive: true });
  fs.writeFileSync(`${cacheDir}/${key}.json`, JSON.stringify(value, null, 2));
}

export async function predictDag(): Promise<{dag: any; riskScore: number; prewarmPriority: string}> {
  const changeSignature = await classifyChange();

  const riskScore = changeSignature.reduce((acc, f) => {
    if (f.type === "route") return acc + 3;
    if (f.type === "core") return acc + 2;
    return acc + 1;
  }, 0);

  const dag = { files: changeSignature.length, timestamp: Date.now() };

  return {
    dag,
    riskScore,
    prewarmPriority: riskScore > 10 ? "high" : "low",
  };
}

async function prewarm() {
  const commit = process.env.GITHUB_SHA || "local";

  const prediction = await predictDag();

  const key = dagKey(commit, JSON.stringify(prediction.dag));

  const existing = await getCachedDag(key);

  if (existing) {
    console.log("🔥 Prewarm HIT (already exists)");
    return;
  }

  console.log("🧠 Prewarming DAG...");

  await setCachedDag(key, {
    commit,
    dag: prediction.dag,
    riskScore: prediction.riskScore,
    prewarmed: true,
  });

  console.log("🚀 DAG prewarmed successfully");
}

prewarm().catch(console.error);
