import fs from "fs";
import path from "path";
import resolve from "enhanced-resolve";

const SRC_DIR = path.join(import.meta.dirname, "../src");

const resolver = resolve.create.sync({
  extensions: [".ts", ".tsx", ".js", ".jsx"],
});

function findTsFiles(dir: string): string[] {
  const files: string[] = [];
  for (const entry of fs.readdirSync(dir)) {
    const fullPath = path.join(dir, entry);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      if (entry.startsWith(".")) continue;
      files.push(...findTsFiles(fullPath));
    } else if (/\.(ts|tsx|js|jsx)$/.test(entry)) {
      files.push(fullPath);
    }
  }
  return files;
}

function extractImports(content: string): string[] {
  const regex = /import\s+.*?\s+from\s+['"]([^'"]+)['"]/g;
  const imports: string[] = [];
  let match;
  while ((match = regex.exec(content)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}

let errorCount = 0;

for (const file of findTsFiles(SRC_DIR)) {
  const content = fs.readFileSync(file, "utf-8");
  const imports = extractImports(content);
  const fileDir = path.dirname(file);

  for (const imp of imports) {
    if (imp.startsWith(".") || imp.startsWith("/")) {
      try {
        resolver(fileDir, imp);
      } catch (e) {
        console.error(`❌ Broken import: ${imp} in ${path.relative(SRC_DIR, file)}`);
        errorCount++;
      }
    }
  }
}

if (errorCount > 0) {
  console.error(`\n❌ ${errorCount} broken import(s) found`);
  process.exit(1);
} else {
  console.log("✅ All imports resolved");
}
