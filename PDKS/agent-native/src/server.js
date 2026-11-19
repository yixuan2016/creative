import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { McpServer, inputRequired, acceptedContent, inputResponse } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import { registerAppResource, registerAppTool, RESOURCE_MIME_TYPE } from '@modelcontextprotocol/ext-apps/server';
import * as z from 'zod/v4';
import {
  applyPlan, buildMcpConfig, createPlan, doctor, getBundleInfo,
  getDefaultPaths, verifyInstall
} from './core/bootstrap.js';
import {
  applyNativePlan, createNativePlan, nativeDoctor, verifyNativeInstall,
  CONFIRMATION_PHRASE as NATIVE_CONFIRMATION_PHRASE, getNativeDefaultPaths
} from './core/native-bootstrap.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const appUri = 'ui://pdks/setup-wizard.html';
const appHtmlPath = path.resolve(here, '../dist/mcp-app.html');

const pathSchema = z.object({
  installRoot: z.string().optional().describe('Optional user-level PDKS application directory. Must remain inside the current user home directory.'),
  vaultRoot: z.string().optional().describe('Optional user-visible PDKS Vault directory. Must remain inside the current user home directory.')
});

function textResult(value) {
  return {
    content: [{ type: 'text', text: JSON.stringify(value, null, 2) }],
    structuredContent: value
  };
}

function createServer() {
  const server = new McpServer({ name: 'pdks-agent-native-bootstrap', version: '0.2.0' });

  server.registerTool('pdks_native_doctor', {
    title: 'Check Node-native PDKS initialization prerequisites',
    description: 'Read-only checks for the Node-native File-first bootstrap. Does not require Python, connect data sources or collect data.',
    inputSchema: pathSchema
  }, async (args) => textResult(nativeDoctor(args)));

  server.registerTool('pdks_native_plan', {
    title: 'Create Node-native PDKS initialization plan',
    description: 'Read-only deterministic plan for creating the PDKS user configuration and Obsidian-compatible File-first Vault. Present exact paths, no-network behavior and unencrypted-storage warning before approval.',
    inputSchema: pathSchema
  }, async (args) => textResult(createNativePlan(args)));

  server.registerTool('pdks_native_apply', {
    title: 'Initialize PDKS File-first Vault using Node.js',
    description: `MUTATING ACTION. Call only after the user reviews the exact plan and explicitly enters ${NATIVE_CONFIRMATION_PHRASE} (or confirms in the PDKS setup panel). Requires the exact plan SHA-256 and acknowledgement that the Vault is not encrypted at rest. Creates local folders and Ontology assets only; does not install Python Runtime, connect data sources, import history, enable background services or cloud sync.`,
    inputSchema: pathSchema.extend({
      approvedPlanSha256: z.string().min(64).max(64),
      confirmationPhrase: z.string().optional(),
      acknowledgeUnencryptedStorage: z.boolean().optional()
    })
  }, async (args, ctx) => {
    let confirmationPhrase = args.confirmationPhrase;
    let acknowledgeUnencryptedStorage = args.acknowledgeUnencryptedStorage === true;
    if (!confirmationPhrase || !acknowledgeUnencryptedStorage) {
      const response = inputResponse(ctx.mcpReq.inputResponses, 'approval');
      if (response.kind === 'missing') {
        return inputRequired({
          inputRequests: {
            approval: inputRequired.elicit({
              message: '请确认已审阅 PDKS 初始化计划，并理解本地 Vault 尚未提供静态加密。未确认前不会写入文件。',
              requestedSchema: {
                type: 'object',
                properties: {
                  confirmationPhrase: { type: 'string', title: '输入确认短语', enum: [NATIVE_CONFIRMATION_PHRASE] },
                  acknowledgeUnencryptedStorage: { type: 'boolean', title: '我理解本地文件尚未加密的风险' }
                },
                required: ['confirmationPhrase', 'acknowledgeUnencryptedStorage']
              }
            })
          }
        });
      }
      if (response.kind === 'elicit' && response.action !== 'accept') {
        return textResult({ status: 'cancelled', message: '用户未确认；没有执行初始化或写入。' });
      }
      const accepted = acceptedContent(ctx.mcpReq.inputResponses, 'approval', z.object({
        confirmationPhrase: z.string(), acknowledgeUnencryptedStorage: z.boolean()
      }));
      if (!accepted) return textResult({ status: 'cancelled', message: '没有收到有效确认；没有执行初始化或写入。' });
      confirmationPhrase = accepted.confirmationPhrase;
      acknowledgeUnencryptedStorage = accepted.acknowledgeUnencryptedStorage === true;
    }
    return textResult(applyNativePlan({ ...args, confirmationPhrase, acknowledgeUnencryptedStorage }));
  });

  server.registerTool('pdks_native_verify', {
    title: 'Verify Node-native PDKS initialization',
    description: 'Read-only SHA-256 verification of protected Ontology assets, PDKS Vault manifest and standard folder structure.',
    inputSchema: pathSchema
  }, async (args) => textResult(verifyNativeInstall(args)));

  server.registerTool('pdks_doctor', {
    title: 'Check PDKS installation prerequisites',
    description: 'Read-only environment and path safety check. Does not install software, access data sources or collect data.',
    inputSchema: pathSchema
  }, async (args) => textResult({ bundle: getBundleInfo(), ...doctor(args) }));

  server.registerTool('pdks_bootstrap_plan', {
    title: 'Create PDKS installation plan',
    description: 'Read-only. Creates a deterministic plan for the exact application and Vault paths. Show the actions, network use, path choices and storage warning to the user before asking for approval.',
    inputSchema: pathSchema
  }, async (args) => textResult(createPlan(args)));

  server.registerTool('pdks_bootstrap_apply', {
    title: 'Install and initialize PDKS',
    description: `MUTATING ACTION. Call only after the user has reviewed the exact plan and explicitly typed ${'CONFIRM INSTALL PDKS'} (or clicked the confirmation in the PDKS setup UI). Requires the exact plan SHA-256 and explicit acknowledgement that local storage is not encrypted at rest. Does not log into DingTalk, subscribe to sources, import history, enable background services or cloud sync.`,
    inputSchema: pathSchema.extend({
      approvedPlanSha256: z.string().min(64).max(64),
      confirmationPhrase: z.string().optional(),
      acknowledgeUnencryptedStorage: z.boolean().optional()
    })
  }, async (args, ctx) => {
    let confirmationPhrase = args.confirmationPhrase;
    let acknowledgeUnencryptedStorage = args.acknowledgeUnencryptedStorage === true;
    if (!confirmationPhrase || !acknowledgeUnencryptedStorage) {
      const response = inputResponse(ctx.mcpReq.inputResponses, 'approval');
      if (response.kind === 'missing') {
        return inputRequired({
          inputRequests: {
            approval: inputRequired.elicit({
              message: '请确认 PDKS 安装计划，并知悉当前 Runtime 的 SQLite 与本地文件尚未提供静态加密。未确认前不会安装。',
              requestedSchema: {
                type: 'object',
                properties: {
                  confirmationPhrase: { type: 'string', title: '输入确认短语', enum: ['CONFIRM INSTALL PDKS'] },
                  acknowledgeUnencryptedStorage: { type: 'boolean', title: '我理解本地数据未加密的风险' }
                },
                required: ['confirmationPhrase', 'acknowledgeUnencryptedStorage']
              }
            })
          }
        });
      }
      if (response.kind === 'elicit' && response.action !== 'accept') {
        return textResult({ status: 'cancelled', message: '用户未确认；没有执行安装或写入。' });
      }
      const accepted = acceptedContent(ctx.mcpReq.inputResponses, 'approval', z.object({
        confirmationPhrase: z.string(),
        acknowledgeUnencryptedStorage: z.boolean()
      }));
      if (!accepted) return textResult({ status: 'cancelled', message: '没有收到有效确认；没有执行安装或写入。' });
      confirmationPhrase = accepted.confirmationPhrase;
      acknowledgeUnencryptedStorage = accepted.acknowledgeUnencryptedStorage === true;
    }
    const current = createPlan(args);
    const result = applyPlan({
      ...args,
      confirmationPhrase,
      acknowledgeUnencryptedStorage,
      currentPlanHash: current.plan_sha256,
      approvedPlanHash: args.approvedPlanSha256
    });
    return textResult(result);
  });

  server.registerTool('pdks_verify', {
    title: 'Verify PDKS installation',
    description: 'Read-only check of the local Runtime, launcher, database and portable Vault manifest.',
    inputSchema: pathSchema
  }, async (args) => textResult(verifyInstall(args)));

  server.registerTool('pdks_vault_status', {
    title: 'Inspect PDKS Vault',
    description: 'Read-only summary of the selected PDKS Vault manifest. Does not read or expose personal note contents.',
    inputSchema: z.object({ vaultRoot: z.string().optional() })
  }, async ({ vaultRoot }) => {
    const defaults = getNativeDefaultPaths();
    const root = path.resolve(vaultRoot || defaults.vaultRoot);
    const manifestPath = path.join(root, 'PDKS-MANIFEST.json');
    try {
      const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
      return textResult({ status: 'initialized', vaultRoot: root,
        vaultVersion: manifest.pdks_vault_version,
        portableFileCount: manifest.file_count ?? Object.keys(manifest.files || {}).length,
        storageMode: manifest.storage_mode,
        ontologyVersion: '0.2.1',
        note: 'This status check reads manifest metadata only; it does not inspect note content.' });
    } catch {
      return textResult({ status: 'not_initialized', vaultRoot: root,
        nextStep: 'Run pdks_bootstrap_plan and ask the user to review the proposed Vault path.' });
    }
  });

  server.registerTool('pdks_agent_config_preview', {
    title: 'Preview Agent connection configuration',
    description: 'Returns a generic local MCP configuration snippet. It never edits Agent configuration files. Host-specific syntax and installation paths must be checked by the user/Agent.',
    inputSchema: z.object({ host: z.enum(['generic', 'claude-desktop', 'cursor', 'codex-cli', 'workbuddy']).default('generic') })
  }, async ({ host }) => {
    const info = getBundleInfo();
    return textResult(buildMcpConfig({
      serverEntry: path.resolve(here, '../bin/pdks-agent.js'),
      bundleRoot: info.bundleRoot,
      host
    }));
  });

  registerAppTool(server, 'pdks_setup_wizard', {
    title: 'PDKS Interactive Setup',
    description: 'Open an interactive setup panel. The panel can check the environment, choose safe local paths, preview the exact plan, and require explicit confirmation before installation. If the host does not support MCP Apps, use pdks_doctor and pdks_bootstrap_plan in conversation instead.',
    inputSchema: pathSchema,
    _meta: { ui: { resourceUri: appUri } }
  }, async (args) => textResult({
    product: 'PDKS Agent-native Bootstrap',
    version: '0.2.0',
    pdksTrack: '0.5.3',
    stage: 'transitional_skill_development',
    defaults: { ...getNativeDefaultPaths(), ...args },
    doctor: nativeDoctor(args),
    warning: 'Experimental preview. Native File-first initialization does not require Python. Local Vault files are not encrypted at rest. No data collection is enabled by default.'
  }));

  registerAppResource(server, 'PDKS Setup Wizard', appUri,
    { mimeType: RESOURCE_MIME_TYPE, description: 'Interactive PDKS installation and configuration wizard.' },
    async () => {
      const html = await fs.readFile(appHtmlPath, 'utf8');
      return { contents: [{ uri: appUri, mimeType: RESOURCE_MIME_TYPE, text: html }] };
    }
  );

  server.registerResource('pdks://setup/contract', 'pdks://setup/contract', {
    title: 'PDKS Setup Safety Contract',
    description: 'Read-only machine-readable installation and approval boundaries.',
    mimeType: 'application/json'
  }, async (uri) => {
    const contractPath = path.resolve(here, '../../setup/agent-setup-contract.json');
    const contract = await fs.readFile(contractPath, 'utf8');
    return { contents: [{ uri: uri.href, mimeType: 'application/json', text: contract }] };
  });

  return server;
}

serveStdio(() => createServer());
