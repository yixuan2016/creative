# PALOS SQLite Read-only Adapter 集成契约 V0.1

## 1. 目标与边界

本契约定义 Event Intelligence Lab 如何在不修改 PALOS 数据库的前提下，检查真实 PALOS SQLite Schema 并验证字段映射。

V0.1 Adapter 是**只读结构与统计预览**，不是生产数据同步器。

## 2. 安全约束

- 通过 SQLite URI `mode=ro` 打开数据库；
- 执行 `PRAGMA query_only=ON`；
- 拒绝符号链接和非普通文件；
- 不接收自由 SQL、WHERE 片段、表达式或任意 JOIN；
- 表名和字段名必须存在于已检查的数据库 Schema；
- Profile 固定 `mode=read_only`；
- 可选 `expected_schema_fingerprint` 不匹配时 fail closed；
- 预览仅输出行数、映射字段、空值计数和 Schema 指纹，不返回业务字段值；
- 不执行任何 PALOS 写操作，也不向 EIL 导入事件正文。

## 3. Profile 结构

模板：`examples/palos-adapter-profile.template.json`  
Schema：`schemas/palos-adapter-profile-v0.1.schema.json`

核心结构：

- `profile_version`：当前固定为 `0.1`；
- `mode`：必须为 `read_only`；
- `expected_schema_fingerprint`：首次检查后由负责人审核并填入；
- `tables.events.table`：PALOS 事件表物理名称；
- `tables.events.columns`：共同事件语义字段到物理字段的映射。

至少需要映射 `event_id` 与 `event_type`。其他字段按真实 Schema 逐项确认，不能仅因字段同名就假设语义一致。

## 4. Schema 指纹

指纹由表/视图名称、对象类型、字段名、字段类型、非空约束、主键和外键结构计算。索引变化、表结构变化可能要求重新审核 Profile。

指纹不是数据完整性证明，也不代表本体语义兼容。语义映射仍需 PALOS 责任方评审。

## 5. 使用方式

先检查 Schema：

```bash
PYTHONPATH=. python scripts/inspect_palos_schema.py \
  --db /path/to/palos-sanitized-copy.sqlite3 \
  --output reports/palos-schema.json
```

再复制并审核 Profile，执行只读预览：

```bash
PYTHONPATH=. python scripts/preview_palos_adapter.py \
  --db /path/to/palos-sanitized-copy.sqlite3 \
  --profile manifests/palos-adapter-profile.template.json
```

## 6. 后续升级门槛

只有在以下事项完成后，才讨论事件读取或写入桥接：

1. PALOS Schema 和迁移版本已确认；
2. 两级本体 URI 和版本治理已确认；
3. 主键、租户/Workspace、用户主体和权限边界已确认；
4. 事件、证据、断言和来源之间的关系已确认；
5. 数据保留、撤权删除、备份和恢复策略已确认；
6. PALOS 责任方批准字段映射和 Adapter 行为。

生产 Adapter 应通过 PALOS Repository / Service 接口，而不是让 EIL 直接操作 PALOS 生产数据库。
