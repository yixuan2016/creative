import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const AGENT_BRIDGE_VERSION = '0.2.0';
export const PDKS_TRACK = '0.5.2.2';
export const CONFIRMATION_PHRASE = 'CONFIRM INSTALL PDKS';

const moduleDir = path.dirname(fileURLToPath(import.meta.url));
const packageRoot = path.resolve(moduleDir, '../..');

export function resolveBundleRoot(env = process.env) {
  const configured = env.PDKS_BUNDLE_ROOT;
  return path.resolve(configured || path.resolve(packageRoot, '..'));
}

export function isSupportedNodeVersion(version = process.versions.node) {
  const [major, minor] = String(version).split('.').map(Number);
  return major > 22 || (major === 22 && minor >= 12);
}

export function getDefaultPaths({ platform = process.platform, homeDir = os.homedir(), env = process.env } = {}) {
  let installRoot;
  if (platform === 'win32') {
    installRoot = path.join(env.LOCALAPPDATA || path.join(homeDir, 'AppData', 'Local'), 'PDKS', PDKS_TRACK);
  } else if (platform === 'darwin') {
    installRoot = path.join(homeDir, 'Library', 'Application Support', 'PDKS', PDKS_TRACK);
  } else {
    installRoot = path.join(env.XDG_DATA_HOME || path.join(homeDir, '.local', 'share'), 'pdks', PDKS_TRACK);
  }
  // Keep the default outside common auto-synced Documents folders.
  return { installRoot, vaultRoot: path.join(homeDir, 'PDKS-Vault') };
}

function canonicalizeForSafety(target) {
  const absolute = path.resolve(target);
  let cursor = absolute;
  const suffix = [];
  while (!fs.existsSync(cursor)) {
    const parent = path.dirname(cursor);
    if (parent === cursor) break;
    suffix.unshift(path.basename(cursor));
    cursor = parent;
  }
  let realExisting;
  try {
    realExisting = fs.realpathSync.native(cursor);
  } catch {
    realExisting = cursor;
  }
  return path.resolve(realExisting, ...suffix);
}

function isSameOrDescendant(parent, candidate) {
  const relative = path.relative(parent, candidate);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

export function isPathInsideHome(target, homeDir = os.homedir()) {
  const home = canonicalizeForSafety(homeDir);
  const resolved = canonicalizeForSafety(target);
  return isSameOrDescendant(home, resolved);
}

export function pathsOverlap(first, second) {
  const a = canonicalizeForSafety(first);
  const b = canonicalizeForSafety(second);
  return isSameOrDescendant(a, b) || isSameOrDescendant(b, a);
}

export function validateApplyApproval({ planHash, approvedPlanHash, confirmationPhrase, acknowledgeUnencryptedStorage }) {
  if (!planHash || !approvedPlanHash || planHash !== approvedPlanHash) {
    throw new Error('The approved plan hash is missing or does not match the current plan. Generate and review a fresh plan.');
  }
  if (confirmationPhrase !== CONFIRMATION_PHRASE) {
    throw new Error(`Explicit confirmation is required. Ask the user to enter: ${CONFIRMATION_PHRASE}`);
  }
  if (acknowledgeUnencryptedStorage !== true) {
    throw new Error('The user must explicitly acknowledge that this experimental Runtime does not encrypt data at rest.');
  }
  return true;
}

export function buildMcpConfig({ command = 'node', serverEntry, bundleRoot, host = 'generic' }) {
  const args = [path.resolve(serverEntry), 'mcp'];
  const config = {
    command,
    args,
    env: { PDKS_BUNDLE_ROOT: path.resolve(bundleRoot) }
  };
  return {
    host,
    maturity: 'experimental_preview',
    configuration: { mcpServers: { pdks: config } },
    note: 'Preview only. This returns a configuration snippet; it does not modify the Agent configuration file.'
  };
}

function findPython() {
  const candidates = [];
  if (process.env.PDKS_PYTHON) candidates.push({ command: process.env.PDKS_PYTHON, prefix: [] });
  if (process.platform === 'win32') candidates.push({ command: 'py', prefix: ['-3'] });
  candidates.push({ command: process.platform === 'win32' ? 'python' : 'python3', prefix: [] });
  candidates.push({ command: 'python', prefix: [] });
  for (const candidate of candidates) {
    const probe = spawnSync(candidate.command, [...candidate.prefix, '-c', 'import sys; print("%d.%d.%d" % sys.version_info[:3])'], {
      encoding: 'utf8', windowsHide: true, timeout: 5000
    });
    if (probe.status !== 0 || !probe.stdout?.trim()) continue;
    const version = probe.stdout.trim();
    const [major, minor] = version.split('.').map(Number);
    if (major > 3 || (major === 3 && minor >= 10)) return { ...candidate, version };
  }
  return null;
}

export function getPythonStatus() {
  const found = findPython();
  return found
    ? { available: true, version: found.version, command: found.command, prefix: found.prefix }
    : { available: false, minimum: '3.10', detail: 'Python 3.10+ was not found. No system packages have been installed or modified.' };
}

function setupScript(bundleRoot) {
  return path.join(bundleRoot, 'skills', 'pdks-setup', 'scripts', 'pdks_setup.py');
}

export function runSetupCommand(command, options = {}) {
  if (!isSupportedNodeVersion()) return { status: 'blocked', node: { supported: false, version: process.versions.node, minimum: '22.12.0' }, next_step: 'Install Node.js 22.12+ and rerun PDKS doctor.' };
  const bundleRoot = path.resolve(options.bundleRoot || resolveBundleRoot());
  const defaults = getDefaultPaths();
  const installRoot = path.resolve(options.installRoot || defaults.installRoot);
  const vaultRoot = path.resolve(options.vaultRoot || defaults.vaultRoot);
  if (!isPathInsideHome(installRoot) || !isPathInsideHome(vaultRoot)) {
    throw new Error('For safety, PDKS install and Vault paths must remain inside the current user home directory, including after resolving existing symlinks.');
  }
  if (pathsOverlap(installRoot, vaultRoot)) {
    throw new Error('The PDKS install directory and Vault directory must be separate and must not contain one another. Choose two distinct user-level folders.');
  }
  const python = findPython();
  if (!python) return { status: 'blocked', python: getPythonStatus(), next_step: 'Install Python 3.10+ for the current user, then rerun PDKS doctor. This preview does not install Python automatically.' };
  const script = setupScript(bundleRoot);
  if (!fs.existsSync(script)) throw new Error(`PDKS setup engine was not found at ${script}. Set PDKS_BUNDLE_ROOT to the extracted PDKS package directory.`);
  const args = [
    ...python.prefix,
    script,
    '--bundle-root', bundleRoot,
    '--install-root', installRoot,
    '--vault-root', vaultRoot,
    command
  ];
  if (command === 'install') {
    args.push('--approve-plan', String(options.approvedPlanHash || ''));
    if (options.acknowledgeUnencryptedStorage === true) args.push('--acknowledge-unencrypted-storage');
  }
  const result = spawnSync(python.command, args, {
    cwd: bundleRoot,
    encoding: 'utf8',
    windowsHide: true,
    timeout: command === 'install' ? 15 * 60 * 1000 : 30 * 1000,
    env: { ...process.env, PYTHONUTF8: '1' }
  });
  if (result.error) throw new Error(`Could not run PDKS setup engine: ${result.error.message}`);
  const stdout = (result.stdout || '').trim();
  let payload;
  try { payload = JSON.parse(stdout); }
  catch { throw new Error(`PDKS setup engine returned a non-JSON response (exit ${result.status}): ${(result.stderr || stdout).slice(-2000)}`); }
  if (result.status !== 0 && payload.status !== 'blocked' && payload.status !== 'degraded' && payload.status !== 'not_installed') {
    throw new Error(`PDKS setup failed (exit ${result.status}): ${(result.stderr || stdout).slice(-2000)}`);
  }
  return { ...payload, python: { available: true, version: python.version } };
}

export function doctor(options = {}) {
  const paths = { ...getDefaultPaths(), ...options };
  const nodeCheck = { name: 'node_version', ok: isSupportedNodeVersion(), detail: `${process.versions.node} (minimum 22.12.0)` };
  const python = getPythonStatus();
  if (!nodeCheck.ok || !python.available) {
    const checks = [nodeCheck, { name: 'python_3_10_plus', ok: python.available, detail: python.detail || python.version }];
    return { status: 'blocked', checks, defaults: paths, next_step: !nodeCheck.ok ? 'Install Node.js 22.12+.' : 'Install Python 3.10+ for the current user.' };
  }
  const result = runSetupCommand('doctor', paths);
  const checks = [nodeCheck, ...(result.checks || [])];
  return { ...result, checks, status: checks.every((item) => item.ok) ? 'ready' : 'blocked', defaults: paths, agentBridgeVersion: AGENT_BRIDGE_VERSION };
}

export function createPlan(options = {}) {
  const paths = { ...getDefaultPaths(), ...options };
  if (!isSupportedNodeVersion()) return { status: 'blocked', node: { supported: false, version: process.versions.node, minimum: '22.12.0' } };
  const result = runSetupCommand('plan', paths);
  return { ...result, agentBridgeVersion: AGENT_BRIDGE_VERSION };
}

export function applyPlan(options = {}) {
  validateApplyApproval({
    planHash: options.currentPlanHash,
    approvedPlanHash: options.approvedPlanHash,
    confirmationPhrase: options.confirmationPhrase,
    acknowledgeUnencryptedStorage: options.acknowledgeUnencryptedStorage
  });
  return runSetupCommand('install', {
    ...options,
    approvedPlanHash: options.approvedPlanHash,
    acknowledgeUnencryptedStorage: true
  });
}

export function verifyInstall(options = {}) {
  return runSetupCommand('verify', { ...getDefaultPaths(), ...options });
}

export function getBundleInfo() {
  const bundleRoot = resolveBundleRoot();
  return {
    pdksTrack: PDKS_TRACK,
    agentBridgeVersion: AGENT_BRIDGE_VERSION,
    bundleRoot,
    setupScriptPresent: fs.existsSync(setupScript(bundleRoot)),
    nodeVersion: process.versions.node,
    nodeSupported: isSupportedNodeVersion(),
    python: getPythonStatus()
  };
}
