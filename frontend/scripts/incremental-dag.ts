import fg from "fast-glob";
import fs from "fs";
import { Project } from "ts-morph";
import { hashFile } from "./hash";

const CACHE_FILE = "dag-cache.json";
const AFFECTED_FILE = "affected.json";

function loadCache(): Record<string, any> {
  if (!fs.existsSync(CACHE_FILE)) return {};
  return JSON.parse(fs.readFileSync(CACHE_FILE, "utf-8"));
}

function saveCache(cache: Record<string, any>): void {
  fs.writeFileSync(CACHE_FILE, JSON.stringify(cache, null, 2));
}

async function run() {
  const cache = loadCache();
  const files = await fg("src/**/*.{ts,tsx,js,jsx}");

  const changedFiles: string[] = [];

  for (const file of files) {
    try {
      const newHash = hashFile(file);
      const oldHash = cache[file]?.hash;

      if (newHash !== oldHash) {
        changedFiles.push(file);
      }
    } catch {
      changedFiles.push(file);
    }
  }

  console.log(`Changed files: ${changedFiles.length}`);

  const project = new Project({ tsConfigFilePath: "tsconfig.json" });
  const resolvedFiles = new Set<string>();

  for (const file of changedFiles) {
    try {
      const source = project.addSourceFileAtPath(file);
      const imports = source
        .getImportDeclarations()
        .map((i) => i.getModuleSpecifierValue());

      cache[file] = { imports, hash: hashFile(file) };
      resolvedFiles.add(file);
    } catch {
      cache[file] = { imports: [], hash: hashFile(file) };
    }
  }

  const affected = new Set<string>(changedFiles);

  for (const file of Object.keys(cache)) {
    const imports = cache[file]?.imports || [];
    if (imports.some((imp: string) => changedFiles.includes(imp))) {
      affected.add(file);
    }
  }

  const affectedArray = Array.from(affected);
  console.log(`Affected subgraph: ${affectedArray.length} files`);

  saveCache(cache);
  fs.writeFileSync(AFFECTED_FILE, JSON.stringify(affectedArray));

  return affectedArray;
}

run().catch(console.error);
