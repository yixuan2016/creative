# PDKS Setup Confirmation Policy

| Level | Examples | Default |
|---|---|---|
| L0 Read-only | OS, Python, disk, bundle, DWS presence, existing install check | Agent may run automatically |
| L1 Local setup | Create a new user-level install directory, virtual environment, install approved runtime dependencies | Show exact plan; require one explicit approval bound to plan hash |
| L2 External identity / permissions | DWS installation, DingTalk OAuth login, Agent skill directory changes, background service, OS login item | Separate confirmation for each action |
| L3 Data-impacting | Subscribe to chat streams, import historical data, export, delete, cloud backup, cross-device sync | Separate scoped confirmation; describe data categories, destination, retention and reversibility |

Never infer permission for a higher level from approval at a lower level. A user may approve PDKS installation while declining DWS or data collection.
