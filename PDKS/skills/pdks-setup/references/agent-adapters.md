# PDKS Setup Agent Adapter Notes

The setup protocol is host-neutral. Do not assume every Agent has the same local execution permissions or Skill directory.

## Codex local

- Use the host's supported local command-execution mechanism.
- Prefer the project-local `SKILL.md` when the host supports Agent Skills.
- Run only the documented PDKS Setup Engine commands.
- Ask for approval in the conversation before the install command; do not treat a sandbox/tool permission prompt as consent to data collection.
- A cloud-hosted execution environment is not the user's laptop. Do not claim local installation unless the command ran on the user's machine.

## WorkBuddy desktop

- Use only documented local file/terminal capabilities available in the installed WorkBuddy version.
- First verify that the current session can access the extracted PDKS bundle and run a local command.
- If WorkBuddy supports importing an Agent Skill, import this `SKILL.md` only after user approval. If it does not, use the protocol as the task instructions; do not guess a proprietary Skill path or configuration format.
- Ask separately before adding the DWS Skill or modifying any Agent configuration directory.

## Other Agents

An Agent is compatible when it can:
1. Read the PDKS Setup Skill and bundle files.
2. Run local commands on the user's machine (not only in a remote sandbox).
3. Show the exact plan and wait for explicit approval.
4. Pass the exact plan hash to the engine.
5. Report actual verification results.

If any capability is missing, the Agent is guidance-only for that session.


## Local MCP Agent Bridge (0.5.2.2 preview)

- Preferred after one-time bridge build: connect the host to `agent-native/bin/pdks-agent.js mcp` using its documented local MCP STDIO configuration.
- Use `pdks_doctor` → `pdks_bootstrap_plan` → explicit approval → `pdks_bootstrap_apply` → `pdks_verify`.
- `pdks_setup_wizard` provides a richer MCP Apps panel only in hosts that support the MCP Apps extension.
- If MCP Apps is unsupported, continue with ordinary MCP tools and conversational confirmation.
- `pdks_agent_config_preview` prints a generic config snippet only; it does not modify host configuration.
- Host-specific MCP config file paths and app support must be verified against the installed host version. Do not claim Codex, WorkBuddy, Claude, Cursor or ChatGPT has passed end-to-end testing unless an actual test record exists.
