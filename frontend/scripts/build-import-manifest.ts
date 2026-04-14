import fg from "fast-glob";
import fs from "fs";
import path from "path";
import { Project } from "ts-morph";
import resolve from "enhanced-resolve";

const SCRIPTS_DIR = path.resolve("scripts");
const SRC_DIR = path.resolve("src");

const resolver = resolve.create.sync({
  extensions: [".ts", ".tsx", ".js", ".jsx"],
  cwd: SCRIPTS_DIR,
});

function resolveImport(fromFile: string, spec: string): string | null {
  if (!spec.startsWith(".") && !spec.startsWith("/")) return spec;
  try {
    return resolver(path.dirname(fromFile), spec);
  } catch {
    return null;
  }
}

async function buildManifest() {
  const files = await fg("**/*.{ts,tsx,js,jsx}", { cwd: SRC_DIR });

  const project = new Project({
    tsConfigFilePath: "tsconfig.json",
  });

  const manifest: Record<string, { imports: string[]; exports: string[] }> = {};

  for (const file of files) {
    const fullPath = path.join(SRC_DIR, file);
    const source = project.addSourceFileAtPath(fullPath);

    const imports = source
      .getImportDeclarations()
      .map((i) => i.getModuleSpecifierValue())
      .map((imp) => resolveImport(fullPath, imp))
      .filter((imp): imp is string => imp !== null);

    const exports = Array.from(source.getExportedDeclarations().keys());

    manifest[file] = { imports, exports };
  }

  let errorCount = 0;
  for (const [file, entry] of Object.entries(manifest)) {
    for (const imp of entry.imports) {
      if (imp.startsWith(".")) {
        const impPath = path.isAbsolute(imp) ? imp : path.join(SRC_DIR, imp);
        if (!fs.existsSync(impPath) && !fs.existsSync(impPath + ".ts") && !fs.existsSync(impPath + ".tsx")) {
          console.error(`❌ Missing module: ${imp} (imported by ${file})`);
          errorCount++;
        }
      }
    }
  }

  if (errorCount > 0) {
    console.error(`\n❌ ${errorCount} broken import(s) found`);
    process.exit(1);
  }

  const manifestPath = path.join(SCRIPTS_DIR, "import-manifest.json");
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

  console.log(`✅ Import manifest compiled: ${Object.keys(manifest).length} files`);
}

buildManifest().catch((e) => {
  console.error(e);
  process.exit(1);
});