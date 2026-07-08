#!/usr/bin/env node
import assert from 'node:assert/strict';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
import ts from 'typescript';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');

function loadTsModule(relPath) {
  const filename = join(root, relPath);
  const source = readFileSync(filename, 'utf8');
  const { outputText, diagnostics } = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020, esModuleInterop: true },
    fileName: filename,
    reportDiagnostics: true,
  });
  const blocking = diagnostics?.filter((d) => d.category === ts.DiagnosticCategory.Error) ?? [];
  assert.equal(blocking.length, 0, `TypeScript transpile failed for ${relPath}`);
  const module = { exports: {} };
  const sandbox = { module, exports: module.exports, console, require: () => ({}) };
  vm.runInNewContext(outputText, sandbox, { filename });
  return module.exports;
}

function assertNoDoubleSlashExceptProtocol(value) {
  assert.equal(value.replace(/^https?:\/\//, '').includes('//'), false, `${value} contains a duplicate slash`);
}

function walkJsonFiles(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) out.push(...walkJsonFiles(full));
    else if (name.endsWith('.json')) out.push(full);
  }
  return out;
}

const { joinApiUrl, normalizeApiBase } = loadTsModule('src/api/url.ts');
const urlCases = [
  ['https://api.example.com', '/v1/foo', 'https://api.example.com/v1/foo'],
  ['https://api.example.com/', '/v1/foo', 'https://api.example.com/v1/foo'],
  ['https://api.example.com///', 'v1/foo', 'https://api.example.com/v1/foo'],
  ['', '/v1/foo', '/v1/foo'],
];
for (const [base, path, expected] of urlCases) {
  const actual = joinApiUrl(normalizeApiBase(base, ''), path);
  assert.equal(actual, expected);
  assertNoDoubleSlashExceptProtocol(actual);
}

const { comparePackVersions, latestPerPersona, parsePackVersion } = loadTsModule('src/dialogue/packVersion.ts');
assert.equal(parsePackVersion('v1'), 1);
assert.equal(parsePackVersion('v10'), 10);
for (const invalid of ['v1.2', '10', 'v10-beta', 'latest', 'v01']) assert.equal(parsePackVersion(invalid), null);
assert.equal(comparePackVersions('v10', 'v2') > 0, true);
assert.equal(comparePackVersions('v2', 'v1') > 0, true);

const warnings = [];
const latest = latestPerPersona(
  [
    { personaId: 'yui', packVersion: 'v1', topics: [], levels: [] },
    { personaId: 'yui', packVersion: 'v10', topics: [], levels: [] },
    { personaId: 'yui', packVersion: 'v2', topics: [], levels: [] },
    { personaId: 'ren', packVersion: 'v10-beta', topics: [], levels: [] },
    { personaId: 'ren', packVersion: 'v3', topics: [], levels: [] },
    { personaId: 'aki', packVersion: 'latest', topics: [], levels: [] },
  ],
  { onInvalid: (pack, reason) => warnings.push(`${pack.personaId}/${pack.packVersion}: ${reason}`) },
);
assert.equal(Array.from(latest, (p) => `${p.personaId}:${p.packVersion}`).join(','), 'ren:v3,yui:v10');
assert.equal(warnings.length, 2);
assert.throws(() => latestPerPersona([{ personaId: 'aki', packVersion: 'latest', topics: [], levels: [] }]), /No valid dialogue packs/);

const dialogueJsonFiles = walkJsonFiles(join(root, 'assets/dialogue_fixture'));
assert.ok(dialogueJsonFiles.length > 0, 'No bundled dialogue fixture JSON files found');
for (const file of dialogueJsonFiles) {
  const payload = JSON.parse(readFileSync(file, 'utf8'));
  if (payload.packVersion) assert.notEqual(parsePackVersion(payload.packVersion), null, `${file} has invalid packVersion ${payload.packVersion}`);
  for (const scenario of payload.scenarios ?? []) {
    assert.notEqual(parsePackVersion(scenario.packVersion), null, `${file} has invalid scenario packVersion ${scenario.packVersion}`);
  }
}

const { STRINGS, setUiLocale } = loadTsModule('src/i18n.ts');
setUiLocale('zh-Hant');

const settingsSource = readFileSync(join(root, 'src/screens/SettingsScreen.tsx'), 'utf8');
const appSource = readFileSync(join(root, 'App.tsx'), 'utf8');
const settingsKeys = [...settingsSource.matchAll(/\bs\.([A-Za-z0-9_]+)/g)].map((m) => m[1]);
const commonKeys = [...appSource.matchAll(/STRINGS\.common\.([A-Za-z0-9_]+)/g)].map((m) => m[1]);

for (const key of new Set(settingsKeys)) {
  const value = STRINGS.settings[key];
  assert.ok(value, `Missing zh-Hant settings.${key}`);
  const rendered = typeof value === 'function' ? value(1) : value;
  assert.equal(typeof rendered, 'string', `settings.${key} did not render to a string`);
  assert.notEqual(rendered, key, `settings.${key} leaked a fallback key`);
}
for (const key of new Set(commonKeys)) {
  assert.equal(typeof STRINGS.common[key], 'string', `Missing zh-Hant common.${key}`);
  assert.notEqual(STRINGS.common[key], key, `common.${key} leaked a fallback key`);
}

const forbiddenSettingsLabels = [
  '내 플랜',
  '소셜 · 개인정보',
  '보안',
  '학습 데이터 초기화',
  '마스터 (무제한 체험)',
  '친구 추천에 내 노출 허용',
  '친구 초대 받기',
  '주간 XP를 친구에게 공개',
];
for (const label of forbiddenSettingsLabels) {
  assert.equal(settingsSource.includes(label), false, `Hardcoded Settings label still present: ${label}`);
}

console.log('PASS: frontend regression guards passed.');
