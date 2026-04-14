import crypto from "crypto";
import fs from "fs";

export function hashFile(path: string): string {
  const content = fs.readFileSync(path, "utf-8");
  return crypto.createHash("sha256").update(content).digest("hex");
}
