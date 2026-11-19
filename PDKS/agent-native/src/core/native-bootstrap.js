import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const NATIVE_BOOTSTRAP_VERSION = '0.2.0';
export const PDKS_TRACK = '0.5.3';
export const CONFIRMATION_PHRASE = 'CONFIRM INITIALIZE PDKS';
const moduleDir = path.dirname(fileURLToPath(import.meta.url));
const defaultBundleRoot = path.resolve(moduleDir, '../../..');

export function getNativeDefaultPaths({ platform = process.platform, homeDir = os.homedir(), env = process.env } = {}) {
  let installRoot;
  if (platform === 'win32') {
    installRoot = path.join(env.LOCALAPPDATA || path.join(homeDir, 'AppData', 'Local'), 'PDKS', PDKS_TRACK);
  } else if (platform === 'darwin') {
    installRoot = path.join(homeDir, 'Library', 'Application Support', 'PDKS', PDKS_TRACK);
  } else {
    installRoot = path.join(env.XDG_DATA_HOME || path.join(homeDir, '.local', 'share'), 'pdks', PDKS_TRACK);
  }
  return { installRoot, vaultRoot: path.join(homeDir, 'PDKS-Vault') };
}

function canonicalize(target) {
  const absolute = path.resolve(target);
  let cursor = absolute;
  const suffix = [];
  while (!fs.existsSync(cursor)) {
    const parent = path.dirname(cursor);
    if (parent === cursor) break;
    suffix.unshift(path.basename(cursor));
    cursor = parent;
  }
  let real;
  try { real = fs.realpathSync.native(cursor); } catch { real = cursor; }
  return path.resolve(real, ...suffix);
}

function sameOrChild(parent, candidate) {
  const relative = path.relative(parent, candidate);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}

export function isInsideHome(target, homeDir = os.homedir()) {
  return sameOrChild(canonicalize(homeDir), canonicalize(target));
}

export function pathsOverlap(first, second) {
  const a = canonicalize(first);
  const b = canonicalize(second);
  return sameOrChild(a, b) || sameOrChild(b, a);
}

export function isSupportedNodeVersion(version = process.versions.node) {
  const [major, minor] = String(version).split('.').map(Number);
  return major > 22 || (major === 22 && minor >= 12);
}

function sha256(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function targetState(target) {
  if (!fs.existsSync(target)) return 'absent';
  if (!fs.statSync(target).isDirectory()) return 'not_directory';
  const names = fs.readdirSync(target);
  if (!names.length) return 'empty_directory';
  if (fs.existsSync(path.join(target, 'PDKS-MANIFEST.json')) || fs.existsSync(path.join(target, 'config', 'pdks.config.json'))) return 'managed_pdks';
  return 'nonempty_unmanaged';
}

function validatePaths({ installRoot, vaultRoot, homeDir = os.homedir() }) {
  const install = canonicalize(installRoot);
  const vault = canonicalize(vaultRoot);
  if (!isInsideHome(install, homeDir) || !isInsideHome(vault, homeDir)) {
    throw new Error('PDKS paths must remain inside the current user home directory, including after resolving symlinks.');
  }
  if (pathsOverlap(install, vault)) {
    throw new Error('The PDKS application directory and Vault directory must be separate and must not contain one another.');
  }
  for (const [label, target] of [['install', install], ['Vault', vault]]) {
    const state = targetState(target);
    if (state === 'not_directory') throw new Error(`The ${label} target exists but is not a directory: ${target}`);
    if (state === 'nonempty_unmanaged') throw new Error(`The ${label} target is a non-empty unmanaged directory. Choose another path or back it up first: ${target}`);
  }
  return { installRoot: install, vaultRoot: vault };
}

function listOntologyAssets(bundleRoot) {
  const ontologyRoot = path.join(bundleRoot, 'skills', 'pdks-personal-knowledge', 'assets', 'ontology', '0.2.1');
  if (!fs.existsSync(ontologyRoot)) return [];
  return fs.readdirSync(ontologyRoot).filter((name) => fs.statSync(path.join(ontologyRoot, name)).isFile()).sort();
}

function buildPlanCore(options = {}) {
  const defaults = getNativeDefaultPaths();
  const paths = validatePaths({
    installRoot: options.installRoot || defaults.installRoot,
    vaultRoot: options.vaultRoot || defaults.vaultRoot,
    homeDir: options.homeDir || os.homedir()
  });
  const bundleRoot = path.resolve(options.bundleRoot || process.env.PDKS_BUNDLE_ROOT || defaultBundleRoot);
  const nodeSupported = isSupportedNodeVersion(options.nodeVersion || process.versions.node);
  const ontologyAssets = listOntologyAssets(bundleRoot);
  const installState = targetState(paths.installRoot);
  const vaultState = targetState(paths.vaultRoot);
  return {
    plan_version: '0.2.0',
    pdks_track: PDKS_TRACK,
    development_stage: 'transitional_skill_development',
    maturity: 'experimental_preview',
    bootstrap_mode: 'node_native_file_first',
    node: { version: options.nodeVersion || process.versions.node, minimum: '22.12.0', supported: nodeSupported },
    paths,
    target_state: { install: installState, vault: vaultState },
    ontology: { version: '0.2.1', bundled_assets: ontologyAssets },
    actions: [
      'Create user-scoped PDKS application configuration and local state directory.',
      'Create a portable Markdown Vault with standard folders and starter guidance.',
      'Copy the bundled PDKS Ontology 0.2.1 assets into the Vault.',
      'Write a PDKS-MANIFEST.json with SHA-256 checksums for generated system assets.',
      'Run post-initialization integrity verification.'
    ],
    network_access: [],
    data_sources_connected: [],
    data_collection_enabled: false,
    background_services_enabled: false,
    cloud_sync_enabled: false,
    runtime_status: 'not_installed_optional_python_runtime',
    storage_warning: 'The native File-first Vault is not encrypted at rest in this preview. Use synthetic or non-sensitive data only.',
    user_approval_required: true
  };
}

export function createNativePlan(options = {}) {
  const core = buildPlanCore(options);
  const planSha256 = sha256(stableJson(core));
  return { ...core, plan_sha256: planSha256 };
}

export function nativeDoctor(options = {}) {
  const defaults = getNativeDefaultPaths();
  const plan = createNativePlan(options);
  const checks = [
    { name: 'node_version', ok: plan.node.supported, detail: `${plan.node.version} (minimum ${plan.node.minimum})` },
    { name: 'install_path', ok: plan.target_state.install !== 'nonempty_unmanaged' && plan.target_state.install !== 'not_directory', detail: `${plan.paths.installRoot} (${plan.target_state.install})` },
    { name: 'vault_path', ok: plan.target_state.vault !== 'nonempty_unmanaged' && plan.target_state.vault !== 'not_directory', detail: `${plan.paths.vaultRoot} (${plan.target_state.vault})` },
    { name: 'path_separation', ok: true, detail: 'Application and Vault paths are separate and user-scoped.' },
    { name: 'ontology_assets', ok: plan.ontology.bundled_assets.length >= 1, detail: `${plan.ontology.bundled_assets.length} Ontology 0.2.1 assets found in bundle.` }
  ];
  return {
    status: checks.every((item) => item.ok) ? 'ready' : 'blocked',
    checks,
    defaults: { ...defaults, ...options },
    runtime: { status: 'optional_not_installed', note: 'Python Capture Runtime remains a separate optional installation.' },
    plan_sha256: plan.plan_sha256,
    next_step: checks.every((item) => item.ok) ? 'Generate and review the native initialization plan.' : 'Resolve the failed checks before initialization.'
  };
}

function writeIfAbsent(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  if (fs.existsSync(filePath)) {
    const existing = fs.readFileSync(filePath, 'utf8');
    if (existing === content) return { path: filePath, status: 'unchanged' };
    throw new Error(`Refusing to overwrite an existing file with different content: ${filePath}`);
  }
  fs.writeFileSync(filePath, content, { encoding: 'utf8', flag: 'wx' });
  return { path: filePath, status: 'created' };
}

function writePreservingExisting(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  if (fs.existsSync(filePath)) return { path: filePath, status: 'preserved_user_file' };
  fs.writeFileSync(filePath, content, { encoding: 'utf8', flag: 'wx' });
  return { path: filePath, status: 'created' };
}

function collectHashes(root, relativePaths) {
  const files = {};
  for (const relative of relativePaths.sort()) {
    const full = path.join(root, relative);
    files[relative.split(path.sep).join('/')] = {
      size_bytes: fs.statSync(full).size,
      sha256: sha256(fs.readFileSync(full))
    };
  }
  return files;
}

function writeStarterFiles(vaultRoot, bundleRoot) {
  const created = [];
  const generated = [];
  const folders = [
    '00-System', '00-System/Ontology/0.2.1', '00-System/Templates',
    '00-Inbox', '10-Events', '20-Knowledge', '30-Entities', '40-Tasks',
    '50-Projects', '60-Reflections', '70-Archive',
    '90-Source-Records/sources', '90-Source-Records/evidence', '90-Source-Records/attachments',
    '.pdks/index'
  ];
  for (const folder of folders) fs.mkdirSync(path.join(vaultRoot, folder), { recursive: true });
  const starter = {
    'README.md': '# PDKS Vault\n\n这是你的个人知识资产文件夹。可以使用 Obsidian、VS Code 或任何 Markdown 编辑器打开。\n\n- `00-Inbox`：待整理内容\n- `10-Events`：工作与生活事件\n- `20-Knowledge`：经过整理的知识\n- `30-Entities`：人物、组织、地点等实体\n- `40-Tasks`：任务与承诺\n- `50-Projects`：项目\n- `60-Reflections`：复盘与反思\n- `70-Archive`：归档\n- `90-Source-Records`：来源、证据与附件\n\n**注意：当前为过渡阶段预览，文件尚未加密。不要放入敏感数据。**\n',
    '00-System/PROFILE.md': '# Personal Profile\n\n此文件由用户自行填写。初始化不会推断或收集个人身份信息。\n',
    '00-System/DATA-SOURCES.md': '# Data Sources\n\n尚未连接任何数据源。每个数据源必须单独授权、单独配置采集范围。\n',
    '00-Inbox/README.md': '# Inbox\n\n先收集，后整理。Agent 不应在未经确认时把推测写成事实。\n',
    '10-Events/README.md': '# Events\n\n按 PDKS Event Taxonomy 记录工作与生活事件，并保留来源证据。\n',
    '20-Knowledge/README.md': '# Knowledge\n\n保存可复用的知识、经验、决策和方法。\n',
    '30-Entities/README.md': '# Entities\n\n保存人物、组织、地点、产品和其他实体的稳定信息。\n',
    '40-Tasks/README.md': '# Tasks\n\n保存待办、承诺、提醒和行动项。\n',
    '50-Projects/README.md': '# Projects\n\n保存项目上下文、目标、进展和交付。\n',
    '60-Reflections/README.md': '# Reflections\n\n保存日、周、月复盘与个人反思。\n',
    '70-Archive/README.md': '# Archive\n\n保存已结束或不再活跃的内容。\n',
    '90-Source-Records/sources/README.md': '# Source Records\n\n保留采集来源与来源定位信息。\n',
    '90-Source-Records/evidence/README.md': '# Evidence\n\n保留支持知识断言的原始片段或引用定位。\n',
    '90-Source-Records/attachments/README.md': '# Attachments\n\n附件采用内容哈希寻址；请勿直接覆盖原始附件。\n',
    '00-System/Templates/Knowledge.md': '---\npdks_type: knowledge\nstatus: draft\n---\n\n# 标题\n\n## 结论\n\n## 依据与来源\n\n## 适用范围\n\n## 关联事件\n',
    '00-System/Templates/Event.md': '---\npdks_type: event\nstatus: draft\ndomain: work|life\n---\n\n# 事件标题\n\n## 发生了什么\n\n## 参与者\n\n## 结果\n\n## 来源证据\n'
  };
  for (const [relative, content] of Object.entries(starter)) {
    const result = writePreservingExisting(path.join(vaultRoot, relative), content);
    created.push(result);
    generated.push(relative);
  }
  const ontologySource = path.join(bundleRoot, 'skills', 'pdks-personal-knowledge', 'assets', 'ontology', '0.2.1');
  if (fs.existsSync(ontologySource)) {
    for (const name of fs.readdirSync(ontologySource).sort()) {
      const source = path.join(ontologySource, name);
      if (!fs.statSync(source).isFile()) continue;
      const relative = path.join('00-System', 'Ontology', '0.2.1', name);
      const bytes = fs.readFileSync(source);
      const destination = path.join(vaultRoot, relative);
      fs.mkdirSync(path.dirname(destination), { recursive: true });
      if (fs.existsSync(destination)) {
        const existing = fs.readFileSync(destination);
        if (!existing.equals(bytes)) throw new Error(`Refusing to overwrite modified Ontology asset: ${destination}`);
        created.push({ path: destination, status: 'unchanged' });
      } else {
        fs.writeFileSync(destination, bytes, { flag: 'wx' });
        created.push({ path: destination, status: 'created' });
      }
      generated.push(relative);
    }
  }
  return { created, generated };
}

export function applyNativePlan(options = {}) {
  const current = createNativePlan(options);
  if (!options.approvedPlanSha256 || options.approvedPlanSha256 !== current.plan_sha256) {
    throw new Error('The approved plan hash is missing or no longer matches. Generate and review a fresh plan.');
  }
  if (options.confirmationPhrase !== CONFIRMATION_PHRASE) {
    throw new Error(`Explicit user confirmation is required: ${CONFIRMATION_PHRASE}`);
  }
  if (options.acknowledgeUnencryptedStorage !== true) {
    throw new Error('The user must explicitly acknowledge that the local Vault is not encrypted at rest.');
  }
  if (!current.node.supported) throw new Error(`Node.js ${current.node.minimum}+ is required.`);
  const { installRoot, vaultRoot } = current.paths;
  fs.mkdirSync(installRoot, { recursive: true });
  fs.mkdirSync(vaultRoot, { recursive: true });
  const bundleRoot = path.resolve(options.bundleRoot || process.env.PDKS_BUNDLE_ROOT || defaultBundleRoot);
  const { created, generated } = writeStarterFiles(vaultRoot, bundleRoot);
  const configPath = path.join(installRoot, 'config', 'pdks.config.json');
  const config = {
    pdks_track: PDKS_TRACK,
    bootstrap_version: NATIVE_BOOTSTRAP_VERSION,
    development_stage: 'transitional_skill_development',
    install_root: installRoot,
    vault_root: vaultRoot,
    storage_mode: 'file_first_markdown_jsonl_attachments',
    ontology_version: '0.2.1',
    runtime: { status: 'optional_not_installed', implementation: 'python_capture_runtime_0.1.1' },
    data_collection_enabled: false,
    cloud_sync_enabled: false
  };
  if (fs.existsSync(configPath)) {
    const existing = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    if (existing.install_root !== installRoot || existing.vault_root !== vaultRoot) {
      throw new Error('Existing PDKS configuration points to different paths. Refusing to rewrite it automatically.');
    }
  } else {
    writeIfAbsent(configPath, `${JSON.stringify({ ...config, initialized_at: new Date().toISOString() }, null, 2)}\n`);
  }
  const initializedPath = path.join(installRoot, 'state', 'initialized.json');
  if (!fs.existsSync(initializedPath)) {
    writeIfAbsent(initializedPath, `${JSON.stringify({ status: 'initialized', bootstrap_version: NATIVE_BOOTSTRAP_VERSION, vault_root: vaultRoot, initialized_at: new Date().toISOString() }, null, 2)}\n`);
  }
  const protectedGenerated = generated.filter((relative) => relative.startsWith(path.join('00-System', 'Ontology')));
  const files = collectHashes(vaultRoot, protectedGenerated);
  const manifest = {
    pdks_vault_version: '0.2.0',
    pdks_track: PDKS_TRACK,
    development_stage: 'transitional_skill_development',
    storage_mode: 'file_first_markdown_jsonl_attachments',
    ontology_version: '0.2.1',
    created_at: new Date().toISOString(),
    file_count: Object.keys(files).length,
    files,
    runtime_status: 'optional_not_installed',
    data_collection_enabled: false,
    encryption_at_rest: false
  };
  const manifestPath = path.join(vaultRoot, 'PDKS-MANIFEST.json');
  if (fs.existsSync(manifestPath)) {
    const previous = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    for (const [relative, meta] of Object.entries(previous.files || {})) {
      const currentMeta = files[relative];
      if (currentMeta && currentMeta.sha256 !== meta.sha256) {
        throw new Error(`Ontology asset has changed since the last manifest: ${relative}. Refusing to overwrite it.`);
      }
    }
  } else {
    writeIfAbsent(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  }
  const verification = verifyNativeInstall({ installRoot, vaultRoot });
  return {
    status: verification.status === 'healthy' ? 'initialized' : 'degraded',
    install_root: installRoot,
    file_vault_root: vaultRoot,
    created_or_preserved: created.length,
    generated_file_count: Object.keys(files).length,
    ontology_asset_count: current.ontology.bundled_assets.length,
    runtime_status: 'optional_not_installed',
    data_collection_enabled: false,
    cloud_sync_enabled: false,
    verification,
    warning: '过渡阶段预览：本地文件尚未加密。请仅使用合成数据或非敏感测试材料。'
  };
}

export function verifyNativeInstall(options = {}) {
  const defaults = getNativeDefaultPaths();
  const installRoot = path.resolve(options.installRoot || defaults.installRoot);
  const vaultRoot = path.resolve(options.vaultRoot || defaults.vaultRoot);
  const checks = [];
  const configPath = path.join(installRoot, 'config', 'pdks.config.json');
  checks.push({ name: 'native_config', ok: fs.existsSync(configPath), detail: configPath });
  const manifestPath = path.join(vaultRoot, 'PDKS-MANIFEST.json');
  let manifest;
  try { manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8')); }
  catch { manifest = null; }
  checks.push({ name: 'vault_manifest', ok: Boolean(manifest), detail: manifest ? `Vault ${manifest.pdks_vault_version}` : 'PDKS-MANIFEST.json not found or invalid.' });
  let verified = 0;
  let missing = 0;
  let mismatched = 0;
  if (manifest) {
    for (const [relative, expected] of Object.entries(manifest.files || {})) {
      const full = path.resolve(vaultRoot, relative);
      if (!sameOrChild(path.resolve(vaultRoot), full) || !fs.existsSync(full)) { missing += 1; continue; }
      const bytes = fs.readFileSync(full);
      if (bytes.length !== expected.size_bytes || sha256(bytes) !== expected.sha256) mismatched += 1;
      else verified += 1;
    }
  }
  checks.push({ name: 'manifest_files', ok: Boolean(manifest) && missing === 0 && mismatched === 0, detail: `${verified} verified; ${missing} missing; ${mismatched} modified.` });
  checks.push({ name: 'vault_structure', ok: ['00-Inbox','10-Events','20-Knowledge','30-Entities','40-Tasks','50-Projects','60-Reflections','70-Archive','90-Source-Records'].every((name) => fs.existsSync(path.join(vaultRoot, name))), detail: 'Standard folders present.' });
  return { status: checks.every((item) => item.ok) ? 'healthy' : 'degraded', checks, runtime_status: 'optional_not_installed', data_collection_enabled: false };
}
