import { App } from '@modelcontextprotocol/ext-apps';
import './style.css';

const app = new App({ name: 'PDKS Setup Wizard', version: '0.2.0' });
const $ = (id) => document.getElementById(id);
let currentPlan = null;
let initialArgs = {};

function asObject(result) {
  if (result?.structuredContent && typeof result.structuredContent === 'object') return result.structuredContent;
  const text = result?.content?.find((item) => item.type === 'text')?.text;
  if (text) { try { return JSON.parse(text); } catch { /* text fallback */ } }
  return { status: result?.isError ? 'error' : 'unknown', message: text || 'No structured response returned.' };
}
function setState(target, value, tone = 'neutral') {
  const node = $(target);
  node.className = `state ${tone}`;
  node.textContent = value;
}
function renderChecks(data) {
  const checks = data?.checks || data?.doctor?.checks || [];
  const status = data?.status || data?.doctor?.status || 'unknown';
  const ok = checks.filter((item) => item.ok).length;
  const failed = checks.filter((item) => !item.ok);
  const node = $('doctorState');
  node.innerHTML = '';
  const top = document.createElement('div');
  top.className = `check-summary ${status === 'ready' ? 'good' : 'warn'}`;
  top.textContent = status === 'ready' ? `环境可用 · ${ok} 项检查通过` : `需要处理 · ${failed.length} 项检查未通过`;
  node.append(top);
  for (const item of checks) {
    const row = document.createElement('div'); row.className = 'check-row';
    const dot = document.createElement('span'); dot.className = item.ok ? 'dot good-dot' : 'dot bad-dot';
    const name = document.createElement('span'); name.className = 'check-name'; name.textContent = item.name;
    const detail = document.createElement('span'); detail.className = 'check-detail'; detail.textContent = String(item.detail ?? '');
    row.append(dot, name, detail); node.append(row);
  }
  if (!checks.length) node.textContent = data?.next_step || data?.message || '未获得环境检查结果。';
}
function renderPlan(plan) {
  currentPlan = plan;
  $('planPanel').hidden = false;
  $('resultPanel').hidden = true;
  const summary = $('planSummary'); summary.innerHTML = '';
  const rows = [
    ['应用配置位置', plan.paths?.installRoot], ['知识库位置', plan.paths?.vaultRoot],
    ['初始化方式', plan.bootstrap_mode], ['本体版本', plan.ontology?.version],
    ['目标状态', JSON.stringify(plan.target_state || {})], ['网络访问', (plan.network_access || []).join('；') || '无']
  ];
  for (const [key, value] of rows) {
    const row = document.createElement('div'); row.className = 'summary-row';
    const label = document.createElement('span'); label.textContent = key;
    const val = document.createElement('strong'); val.textContent = String(value ?? '—');
    row.append(label, val); summary.append(row);
  }
  const actions = document.createElement('ol'); actions.className = 'actions';
  for (const action of plan.actions || []) { const li = document.createElement('li'); li.textContent = action; actions.append(li); }
  summary.append(actions);
  $('planJson').textContent = JSON.stringify(plan, null, 2);
  updateApplyButton();
}
function updateApplyButton() {
  $('applyBtn').disabled = !(currentPlan && $('ackBox').checked && $('confirmPhrase').value.trim() === 'CONFIRM INSTALL PDKS');
}
async function callTool(name, args = {}) {
  const result = await app.callServerTool({ name, arguments: args });
  if (result?.isError) throw new Error(asObject(result).message || result.content?.[0]?.text || 'Tool call failed');
  return asObject(result);
}
async function runDoctor() {
  setState('doctorState', '正在检查本机环境…');
  try {
    const data = await callTool('pdks_native_doctor', {
      installRoot: $('installRoot').value.trim(), vaultRoot: $('vaultRoot').value.trim()
    });
    renderChecks(data);
    if (data.defaults) {
      if (!$('installRoot').value) $('installRoot').value = data.defaults.installRoot || '';
      if (!$('vaultRoot').value) $('vaultRoot').value = data.defaults.vaultRoot || '';
    }
  } catch (error) { setState('doctorState', error.message, 'bad'); }
}
async function runPlan() {
  $('planBtn').disabled = true; $('planBtn').textContent = '正在生成计划…';
  try {
    const paths = { installRoot: $('installRoot').value.trim(), vaultRoot: $('vaultRoot').value.trim() };
    const check = await callTool('pdks_native_doctor', paths);
    renderChecks(check);
    if (check.status !== 'ready') throw new Error('当前环境未满足安装条件，请先处理上方检查结果。');
    const plan = await callTool('pdks_native_plan', paths);
    renderPlan(plan);
    $('planPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) { setState('doctorState', error.message, 'bad'); }
  finally { $('planBtn').disabled = false; $('planBtn').innerHTML = '生成安装计划 <span>→</span>'; }
}
async function runApply() {
  if (!currentPlan) return;
  $('applyBtn').disabled = true; $('applyBtn').textContent = '正在初始化…';
  $('resultPanel').hidden = false; $('resultTag').textContent = '处理中'; $('resultBody').textContent = '正在创建本地 PDKS 配置、Obsidian 兼容 Vault 和 Ontology 资产。此步骤不安装 Python Runtime，也不采集数据。请保持 Agent 连接。';
  try {
    const result = await callTool('pdks_native_apply', {
      installRoot: $('installRoot').value.trim(), vaultRoot: $('vaultRoot').value.trim(),
      approvedPlanSha256: currentPlan.plan_sha256,
      confirmationPhrase: $('confirmPhrase').value.trim(),
      acknowledgeUnencryptedStorage: $('ackBox').checked
    });
    $('resultTag').textContent = '文件知识库初始化完成'; $('resultTag').className = 'tag good';
    $('resultBody').innerHTML = '';
    const title = document.createElement('h3'); title.textContent = '你的 PDKS 文件知识库已完成初始化';
    const desc = document.createElement('p'); desc.textContent = '本轮完成的是 Node.js 原生 File-first 初始化。Python Capture Runtime、数据源连接和自动采集仍未启用。你可以使用 Obsidian 打开下面的知识库目录。';
    const paths = document.createElement('pre'); paths.textContent = `知识库：${result.file_vault_root}\n应用配置：${result.install_root}\nRuntime：${result.runtime_status}`;
    const warning = document.createElement('p'); warning.className = 'hint'; warning.textContent = result.warning || '实验性预览：请勿存放敏感数据。';
    $('resultBody').append(title, desc, paths, warning);
    const verification = await callTool('pdks_native_verify', { installRoot: $('installRoot').value.trim(), vaultRoot: $('vaultRoot').value.trim() });
    if (verification.status !== 'healthy') {
      $('resultTag').textContent = '安装完成，验收待处理'; $('resultTag').className = 'tag bad';
      const checks = document.createElement('pre'); checks.textContent = JSON.stringify(verification.checks || verification, null, 2);
      $('resultBody').append(checks);
    }
  } catch (error) {
    $('resultTag').textContent = '需要处理'; $('resultTag').className = 'tag bad';
    $('resultBody').textContent = error.message;
  } finally { $('applyBtn').textContent = '确认并初始化 PDKS'; updateApplyButton(); }
}

$('doctorBtn').addEventListener('click', runDoctor);
$('planBtn').addEventListener('click', runPlan);
$('ackBox').addEventListener('change', updateApplyButton);
$('confirmPhrase').addEventListener('input', updateApplyButton);
$('applyBtn').addEventListener('click', runApply);

app.ontoolresult = (result) => {
  const data = asObject(result);
  initialArgs = data.defaults || {};
  $('installRoot').value = initialArgs.installRoot || '';
  $('vaultRoot').value = initialArgs.vaultRoot || '';
  renderChecks(data.doctor || data);
};
app.connect().catch((error) => setState('doctorState', `无法连接 Agent 宿主：${error.message}`, 'bad'));
