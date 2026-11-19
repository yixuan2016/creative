#!/usr/bin/env node
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  applyPlan, buildMcpConfig, createPlan, doctor, getBundleInfo,
  getDefaultPaths, verifyInstall, CONFIRMATION_PHRASE
} from '../src/core/bootstrap.js';
import { applyNativePlan, createNativePlan, nativeDoctor, verifyNativeInstall, getNativeDefaultPaths, CONFIRMATION_PHRASE as NATIVE_CONFIRMATION_PHRASE } from '../src/core/native-bootstrap.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const serverEntry = path.resolve(here, 'pdks-agent.js');
const args = process.argv.slice(2);
const command = args.shift() || 'help';
function value(name, fallback) { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : fallback; }
function flag(name) { return args.includes(name); }
function paths() {
  const defaults = getDefaultPaths();
  return { installRoot: value('--install-root', defaults.installRoot), vaultRoot: value('--vault-root', defaults.vaultRoot) };
}
function nativePaths() {
  const defaults = getNativeDefaultPaths();
  return { installRoot: value('--install-root', defaults.installRoot), vaultRoot: value('--vault-root', defaults.vaultRoot) };
}
function print(data) { process.stdout.write(JSON.stringify(data, null, 2) + '\n'); }

try {
  if (command === 'mcp') {
    await import('../src/server.js');
  } else if (command === 'doctor') {
    print({ bundle: getBundleInfo(), ...doctor(paths()) });
  } else if (command === 'plan') {
    print(createPlan(paths()));
  } else if (command === 'apply') {
    const plan = createPlan(paths());
    print(applyPlan({ ...paths(), currentPlanHash: plan.plan_sha256,
      approvedPlanHash: value('--approve-plan', ''),
      confirmationPhrase: value('--confirm', ''),
      acknowledgeUnencryptedStorage: flag('--acknowledge-unencrypted-storage') }));
  } else if (command === 'verify') {
    print(verifyInstall(paths()));
  } else if (command === 'native-doctor') {
    print(nativeDoctor(nativePaths()));
  } else if (command === 'native-plan') {
    print(createNativePlan(nativePaths()));
  } else if (command === 'native-apply') {
    const plan = createNativePlan(nativePaths());
    print(applyNativePlan({ ...nativePaths(), approvedPlanSha256: value('--approve-plan', ''),
      confirmationPhrase: value('--confirm', ''),
      acknowledgeUnencryptedStorage: flag('--acknowledge-unencrypted-storage') }));
  } else if (command === 'native-verify') {
    print(verifyNativeInstall(nativePaths()));
  } else if (command === 'config') {
    const info = getBundleInfo();
    print(buildMcpConfig({ serverEntry, bundleRoot: info.bundleRoot, host: value('--host', 'generic') }));
  } else if (command === 'help' || command === '--help' || command === '-h') {
    process.stdout.write(`PDKS Agent-native Bootstrap 0.2.0 · PDKS ${'0.5.3'}\n\nCommands:\n  pdks-agent doctor [--install-root PATH] [--vault-root PATH]\n  pdks-agent plan [--install-root PATH] [--vault-root PATH]\n  pdks-agent apply --approve-plan HASH --confirm "${CONFIRMATION_PHRASE}" --acknowledge-unencrypted-storage\n  pdks-agent verify                  # legacy Python Runtime verification\n  pdks-agent native-doctor           # Node-native File-first prerequisites\n  pdks-agent native-plan             # Node-native Vault initialization plan\n  pdks-agent native-apply --approve-plan HASH --confirm "${NATIVE_CONFIRMATION_PHRASE}" --acknowledge-unencrypted-storage\n  pdks-agent native-verify\n  pdks-agent config --host generic|claude-desktop|cursor|codex-cli\n  pdks-agent mcp\n\nThis is an experimental transitional-stage installer. Native initialization does not require Python. The optional Capture Runtime still uses Python. No data collection is enabled by default.\n`);
  } else {
    throw new Error(`Unknown command: ${command}. Run pdks-agent help.`);
  }
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
