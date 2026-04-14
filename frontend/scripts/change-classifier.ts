import fg from "fast-glob";
import { hashFile } from "./hash";

export async function classifyChange(): Promise<Array<{file: string; hash: string; type: string}>> {
  const files = await fg("src/**/*.{ts,tsx,js,jsx}");

  const signature: Array<{file: string; hash: string; type: string}> = [];

  for (const file of files) {
    const h = hashFile(file);
    const type = file.includes("pages/") ? "route" : file.includes("components/") ? "ui" : "core";
    signature.push({ file, hash: h, type });
  }

  return signature;
}
