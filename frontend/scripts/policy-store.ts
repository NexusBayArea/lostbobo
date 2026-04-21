import fs from "fs";
import path from "path";

const POLICY_FILE = path.join(import.meta.dirname, "../ci-policy.json");

export type QTable = Record<string, Record<string, number>>;

export function loadPolicy(): QTable {
  if (!fs.existsSync(POLICY_FILE)) return {};
  return JSON.parse(fs.readFileSync(POLICY_FILE, "utf-8"));
}

export function savePolicy(policy: QTable): void {
  fs.writeFileSync(POLICY_FILE, JSON.stringify(policy, null, 2));
}
