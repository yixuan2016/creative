import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';
import { tmpdir } from 'node:os';
import {
  buildMcpConfig, getDefaultPaths, isPathInsideHome, isSupportedNodeVersion, pathsOverlap,
  validateApplyApproval, CONFIRMATION_PHRASE
} from '../src/core/bootstrap.js';

test('default install and Vault paths are user-scoped on Windows', () => {
  const result = getDefaultPaths({ platform: 'win32', homeDir: 'C:/Users/Ada', env: { LOCALAPPDATA: 'C:/Users/Ada/AppData/Local' } });
  assert.equal(result.installRoot, path.join('C:/Users/Ada/AppData/Local', 'PDKS', '0.5.2.2'));
  assert.equal(result.vaultRoot, path.join('C:/Users/Ada', 'PDKS-Vault'));
});

test('default install path is user-scoped on macOS', () => {
  const result = getDefaultPaths({ platform: 'darwin', homeDir: '/Users/ada', env: {} });
  assert.equal(result.installRoot, '/Users/ada/Library/Application Support/PDKS/0.5.2.2');
});

test('Linux respects XDG_DATA_HOME', () => {
  const result = getDefaultPaths({ platform: 'linux', homeDir: '/home/ada', env: { XDG_DATA_HOME: '/home/ada/.local/share' } });
  assert.equal(result.installRoot, '/home/ada/.local/share/pdks/0.5.2.2');
});

test('path containment rejects targets outside the home directory', () => {
  assert.equal(isPathInsideHome('/home/ada/PDKS-Vault', '/home/ada'), true);
  assert.equal(isPathInsideHome('/tmp/PDKS-Vault', '/home/ada'), false);
});

test('apply requires exact plan hash, exact phrase and storage acknowledgement', () => {
  assert.throws(() => validateApplyApproval({ planHash: 'a'.repeat(64), approvedPlanHash: 'b'.repeat(64), confirmationPhrase: CONFIRMATION_PHRASE, acknowledgeUnencryptedStorage: true }), /plan hash/);
  assert.throws(() => validateApplyApproval({ planHash: 'a'.repeat(64), approvedPlanHash: 'a'.repeat(64), confirmationPhrase: 'yes', acknowledgeUnencryptedStorage: true }), /Explicit confirmation/);
  assert.throws(() => validateApplyApproval({ planHash: 'a'.repeat(64), approvedPlanHash: 'a'.repeat(64), confirmationPhrase: CONFIRMATION_PHRASE, acknowledgeUnencryptedStorage: false }), /acknowledge/);
  assert.equal(validateApplyApproval({ planHash: 'a'.repeat(64), approvedPlanHash: 'a'.repeat(64), confirmationPhrase: CONFIRMATION_PHRASE, acknowledgeUnencryptedStorage: true }), true);
});

test('MCP config preview does not mutate host configuration', () => {
  const result = buildMcpConfig({ serverEntry: '/bundle/agent-native/src/server.js', bundleRoot: '/bundle', host: 'generic' });
  assert.equal(result.configuration.mcpServers.pdks.command, 'node');
  assert.deepEqual(result.configuration.mcpServers.pdks.args, ['/bundle/agent-native/src/server.js', 'mcp']);
  assert.equal(result.configuration.mcpServers.pdks.env.PDKS_BUNDLE_ROOT, '/bundle');
  assert.match(result.note, /does not modify/);
});


test('Node version gate matches the Vite 7 toolchain baseline', () => {
  assert.equal(isSupportedNodeVersion('20.19.0'), false);
  assert.equal(isSupportedNodeVersion('22.11.9'), false);
  assert.equal(isSupportedNodeVersion('22.12.0'), true);
  assert.equal(isSupportedNodeVersion('24.0.0'), true);
});


test('path containment resolves existing symlinks before approval', (t) => {
  const base = fs.mkdtempSync(path.join(tmpdir(), 'pdks-path-safety-'));
  t.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const home = path.join(base, 'home');
  const outside = path.join(base, 'outside');
  fs.mkdirSync(home); fs.mkdirSync(outside);
  const link = path.join(home, 'linked-vault');
  try { fs.symlinkSync(outside, link, 'dir'); }
  catch { t.skip('Directory symlinks are not available in this environment'); return; }
  assert.equal(isPathInsideHome(link, home), false);
});

test('install and Vault paths cannot overlap', () => {
  assert.equal(pathsOverlap('/home/ada/.local/share/pdks', '/home/ada/PDKS-Vault'), false);
  assert.equal(pathsOverlap('/home/ada/pdks', '/home/ada/pdks/vault'), true);
  assert.equal(pathsOverlap('/home/ada/pdks', '/home/ada/pdks'), true);
});

