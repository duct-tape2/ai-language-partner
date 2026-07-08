#!/usr/bin/env node
// CI guard (GPT-5.5 Pro review #1): fail the build if the dev signed_challenge HMAC
// secret leaks into ANY production web-export artifact (JS bundle, sourcemaps, env,
// metadata). The dev attestation path is __DEV__-gated in src/api/auth.ts, but a
// manual grep is fragile — this makes it automatic.
//
// Usage:
//   EXPO_PUBLIC_DEVICE_ATTESTATION_SECRET=<secret> \
//   npx expo export --platform web --output-dir dist-prod
//   node scripts/verify-prod-no-attestation-secret.mjs dist-prod
//
// Exit 0 = clean (secret absent). Exit 1 = LEAK (secret present) or misuse.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const dir = process.argv[2];
const secret = process.env.EXPO_PUBLIC_DEVICE_ATTESTATION_SECRET || '';

if (!dir) { console.error('usage: verify-prod-no-attestation-secret.mjs <export-dir>'); process.exit(1); }
if (!secret) { console.error('SKIP: no EXPO_PUBLIC_DEVICE_ATTESTATION_SECRET set — nothing to check'); process.exit(0); }

const hits = [];
function walk(p) {
  for (const name of readdirSync(p)) {
    const full = join(p, name);
    const st = statSync(full);
    if (st.isDirectory()) { walk(full); continue; }
    // scan text-ish artifacts (bundles, maps, json, html, txt)
    if (!/\.(js|map|json|html|txt|css)$/i.test(name)) continue;
    let body;
    try { body = readFileSync(full, 'utf8'); } catch { continue; }
    if (body.includes(secret)) hits.push(full);
  }
}
walk(dir);

if (hits.length) {
  console.error(`FAIL: dev attestation secret leaked into ${hits.length} production artifact(s):`);
  for (const h of hits) console.error('  - ' + h);
  console.error('The dev HMAC signer must be __DEV__-gated and never bundled into production.');
  process.exit(1);
}
console.log('PASS: dev attestation secret is absent from all production export artifacts.');
process.exit(0);
