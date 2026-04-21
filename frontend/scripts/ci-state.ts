import crypto from "crypto";

export interface CIStateInput {
  branch: string;
  dagHash: string;
  changeRisk: number;
}

export function getCIState(input: CIStateInput): string {
  const data = `${input.branch}:${input.dagHash}:${input.changeRisk}`;
  return crypto.createHash("sha256").update(data).digest("hex").slice(0, 12);
}
