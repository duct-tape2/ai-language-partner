import assert from "node:assert/strict";

import { findMissingReadmeScripts } from "./verify-readme-scripts.mjs";

assert.deepEqual(
  findMissingReadmeScripts(
    { "README.md": "Run `npm run verify` before opening a PR." },
    { verify: "npm run typecheck" },
  ),
  [],
);

assert.deepEqual(
  findMissingReadmeScripts(
    { "apps/mobile/README.md": "This fixture mentions `npm run missing-script`." },
    { verify: "npm run typecheck" },
  ),
  [{ path: "apps/mobile/README.md", script: "missing-script" }],
);

console.log("verify-readme-scripts tests passed");
