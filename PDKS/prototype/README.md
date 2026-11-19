
## 7. PDKS 与个人运行时持久化原型（新增）

- `personal_memory_sqlite.py`：在既有 `PersonalMemoryEngine` 业务规则上增加 SQLite 持久化、owner 分区、revision 乐观并发、元数据审计和备份。
- `pdks_ads_adapter.py`：将 PDKS Event / Knowledge Asset / Personal Context / Action 保守映射为 ADS Event Ledger / candidate Memory / candidate Intent。
- `personal_memory_cli.py`：提供初始化、PDKS 投影、原子写入、上下文构建、审计、备份、快照和完整性检查命令。
- `test_personal_memory_sqlite.py`：覆盖重启持久化、幂等、owner 隔离、并发冲突、来源抑制、Intent 和动作审批。
- `test_pdks_ads_adapter.py`：覆盖正常映射、设备/连接器授权门禁、时间/身份校验、候选状态和原子投影。
- `../docs/12-PDKS个人数据持久化运行时与ADS-WORK-09接入设计.md`：完整架构、映射规则、运行命令、限制与后续路线。

在仓库根目录运行：

```bash
python prototype/personal_memory_cli.py init --db ./data/personal-memory.sqlite3 --owner <owner-ref>
python prototype/personal_memory_cli.py project-pdks --records-dir ./my-pdks-export/records --owner <owner-ref> --output ./data/projection.json
python prototype/personal_memory_cli.py apply-projection --db ./data/personal-memory.sqlite3 --owner <owner-ref> --projection ./data/projection.json
python prototype/personal_memory_cli.py context --db ./data/personal-memory.sqlite3 --owner <owner-ref> --purpose personal_planning
```

### 原型边界

CLI 默认执行 PDKS JSON Schema 与 Event Taxonomy 校验；仅合成测试数据可显式使用 --skip-pdks-validation。

该实现仅用于单机本地逻辑验证。SQLite 文件没有内建加密或身份认证；`owner_ref` 是数据分区键，不是身份认证。授权引用必须由可信授权服务/适配器提供。来源 suppression 会阻止派生记忆召回和再生成，但不代表原始事件、录音文件或备份已物理删除。PDKS 投影不会自动创建 Agent Action Proposal，也不会自动创建企业投影。
