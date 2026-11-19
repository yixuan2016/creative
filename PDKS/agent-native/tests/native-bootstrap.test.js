import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  CONFIRMATION_PHRASE, applyNativePlan, createNativePlan, getNativeDefaultPaths,
  isInsideHome, nativeDoctor, pathsOverlap, verifyNativeInstall
} from '../src/core/native-bootstrap.js';

function fixture(t) {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), 'pdks-native-home-'));
  const bundle = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
  const installRoot = path.join(home, '.local', 'share', 'pdks', '0.5.3');
  const vaultRoot = path.join(home, 'PDKS-Vault');
  t.after(() => fs.rmSync(home, { recursive: true, force: true }));
  return { home, homeDir: home, bundleRoot: bundle, installRoot, vaultRoot };
}

test('native defaults are user-scoped across supported operating systems', () => {
  const home = '/users/demo';
  assert.match(getNativeDefaultPaths({ platform: 'win32', homeDir: home, env: {} }).installRoot, /PDKS/);
  assert.match(getNativeDefaultPaths({ platform: 'darwin', homeDir: home, env: {} }).installRoot, /Application Support/);
  assert.match(getNativeDefaultPaths({ platform: 'linux', homeDir: home, env: { XDG_DATA_HOME: '/users/demo/.data' } }).installRoot, /\.data/);
});

test('path safety canonicalizes symlinks and rejects escape or overlap', (t) => {
  const f = fixture(t);
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'pdks-outside-'));
  t.after(() => fs.rmSync(outside, { recursive: true, force: true }));
  const link = path.join(f.home, 'escape');
  fs.symlinkSync(outside, link, 'dir');
  assert.equal(isInsideHome(path.join(link, 'vault'), f.home), false);
  assert.equal(pathsOverlap(path.join(f.home, 'a'), path.join(f.home, 'a', 'nested')), true);
  assert.throws(() => createNativePlan({ ...f, vaultRoot: path.join(f.installRoot, 'nested') }), /must be separate/);
});

test('doctor is Node-native and does not require Python', (t) => {
  const f = fixture(t);
  const result = nativeDoctor({ ...f, nodeVersion: '22.16.0' });
  assert.equal(result.status, 'ready');
  assert.equal(result.runtime.status, 'optional_not_installed');
  assert.equal(result.checks.find((x) => x.name === 'ontology_assets').ok, true);
});

test('plan is deterministic for the same untouched targets', (t) => {
  const f = fixture(t);
  const a = createNativePlan({ ...f, nodeVersion: '22.16.0' });
  const b = createNativePlan({ ...f, nodeVersion: '22.16.0' });
  assert.equal(a.plan_sha256, b.plan_sha256);
  assert.equal(a.data_collection_enabled, false);
  assert.deepEqual(a.network_access, []);
});

test('apply refuses missing or incorrect user approval without writing files', (t) => {
  const f = fixture(t);
  const plan = createNativePlan({ ...f, nodeVersion: '22.16.0' });
  assert.throws(() => applyNativePlan({ ...f, approvedPlanSha256: plan.plan_sha256 }), /Explicit user confirmation/);
  assert.equal(fs.existsSync(f.vaultRoot), false);
  assert.throws(() => applyNativePlan({ ...f, approvedPlanSha256: '0'.repeat(64), confirmationPhrase: CONFIRMATION_PHRASE, acknowledgeUnencryptedStorage: true }), /no longer matches/);
});

test('apply creates an Obsidian-compatible File-first Vault and verifies Ontology assets', (t) => {
  const f = fixture(t);
  const plan = createNativePlan({ ...f, nodeVersion: '22.16.0' });
  const result = applyNativePlan({ ...f, nodeVersion: '22.16.0', approvedPlanSha256: plan.plan_sha256,
    confirmationPhrase: CONFIRMATION_PHRASE, acknowledgeUnencryptedStorage: true });
  assert.equal(result.status, 'initialized');
  assert.equal(result.runtime_status, 'optional_not_installed');
  assert.equal(result.data_collection_enabled, false);
  assert.ok(fs.existsSync(path.join(f.vaultRoot, 'PDKS-MANIFEST.json')));
  assert.ok(fs.existsSync(path.join(f.vaultRoot, '00-System', 'Ontology', '0.2.1', 'pdks-core-ontology-0.2.ttl')));
  assert.equal(verifyNativeInstall(f).status, 'healthy');
});

test('reinitialization preserves user-edited Markdown instead of overwriting it', (t) => {
  const f = fixture(t);
  let plan = createNativePlan({ ...f, nodeVersion: '22.16.0' });
  applyNativePlan({ ...f, nodeVersion: '22.16.0', approvedPlanSha256: plan.plan_sha256,
    confirmationPhrase: CONFIRMATION_PHRASE, acknowledgeUnencryptedStorage: true });
  const readme = path.join(f.vaultRoot, 'README.md');
  fs.writeFileSync(readme, '# My customized Vault\n');
  plan = createNativePlan({ ...f, nodeVersion: '22.16.0' });
  const result = applyNativePlan({ ...f, nodeVersion: '22.16.0', approvedPlanSha256: plan.plan_sha256,
    confirmationPhrase: CONFIRMATION_PHRASE, acknowledgeUnencryptedStorage: true });
  assert.equal(fs.readFileSync(readme, 'utf8'), '# My customized Vault\n');
  assert.equal(result.status, 'initialized');
});

test('verification detects modified Ontology assets', (t) => {
  const f = fixture(t);
  const plan = createNativePlan({ ...f, nodeVersion: '22.16.0' });
  applyNativePlan({ ...f, nodeVersion: '22.16.0', approvedPlanSha256: plan.plan_sha256,
    confirmationPhrase: CONFIRMATION_PHRASE, acknowledgeUnencryptedStorage: true });
  const ontology = path.join(f.vaultRoot, '00-System', 'Ontology', '0.2.1', 'pdks-core-ontology-0.2.ttl');
  fs.appendFileSync(ontology, '\n# tampered\n');
  assert.equal(verifyNativeInstall(f).status, 'degraded');
});

test('unmanaged non-empty targets are rejected', (t) => {
  const f = fixture(t);
  fs.mkdirSync(f.vaultRoot, { recursive: true });
  fs.writeFileSync(path.join(f.vaultRoot, 'important.md'), 'keep me');
  assert.throws(() => createNativePlan({ ...f, nodeVersion: '22.16.0' }), /non-empty unmanaged/);
});
