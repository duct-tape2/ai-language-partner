import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const npmRunPattern = /\bnpm\s+run\s+([A-Za-z0-9:_-]+)/g;

export function findMissingReadmeScripts(markdownByPath, scripts) {
  const availableScripts = scripts instanceof Set ? scripts : new Set(Object.keys(scripts ?? {}));
  const missing = [];

  for (const [markdownPath, markdown] of Object.entries(markdownByPath)) {
    const seenInFile = new Set();

    for (const match of markdown.matchAll(npmRunPattern)) {
      const scriptName = match[1];
      if (!availableScripts.has(scriptName) && !seenInFile.has(scriptName)) {
        missing.push({ path: markdownPath, script: scriptName });
        seenInFile.add(scriptName);
      }
    }
  }

  return missing;
}

function readUtf8(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

function main() {
  const mobileRoot = path.resolve(import.meta.dirname, "..");
  const repoRoot = path.resolve(mobileRoot, "..", "..");
  const packageJsonPath = path.join(mobileRoot, "package.json");
  const markdownPaths = [
    path.join(repoRoot, "README.md"),
    path.join(mobileRoot, "README.md"),
  ];

  const packageJson = JSON.parse(readUtf8(packageJsonPath));
  const markdownByPath = Object.fromEntries(
    markdownPaths.map((markdownPath) => [path.relative(repoRoot, markdownPath), readUtf8(markdownPath)]),
  );

  const missing = findMissingReadmeScripts(markdownByPath, packageJson.scripts);

  if (missing.length > 0) {
    console.error("README files reference npm scripts that are missing from apps/mobile/package.json:");
    for (const item of missing) {
      console.error(`- ${item.path}: npm run ${item.script}`);
    }
    process.exitCode = 1;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
