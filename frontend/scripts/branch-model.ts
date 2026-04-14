export function getBranchWeight(branch: string): number {
  if (branch === "main") return 1.0;
  if (branch.startsWith("release/")) return 0.8;
  if (branch.startsWith("feature/")) return 1.2;
  return 1.5;
}
