---
document_id: PDKS-SKILL-ACCEPTANCE-001
title: PDKS Agent Skills 验收矩阵
version: 1.0
status: review-draft
date: 2026-11-20
---

# PDKS-SKILL-ACCEPTANCE-001：Agent Skills 验收矩阵

**版本：** V1.0 评审稿  
**适用范围：** PDKS 0.5.x 及后续版本中的 Setup、Capture、Processing、Knowledge Management、Application 和 Publishing Skills

## 1. 验收原则

1. 验收对象是具体版本、具体操作系统、具体 Agent Host 和具体来源，不接受笼统的“支持所有 Agent / 所有平台”声明。
2. 代码存在、单元测试通过、真实来源接入成功和生产就绪是不同成熟度，必须分开记录。
3. 每个验收项必须有可复现步骤、测试输入、预期结果、实际结果、日志/截图/报告和责任版本。
4. 测试默认使用合成数据；真实个人数据测试必须单独授权并使用最小范围。
5. 安全与授权测试为阻断项。任何未授权写入、越权读取、凭据泄露或不可控外传均判定不通过。
6. 未执行的测试必须标记为“未执行”，不得计为通过。

## 2. 成熟度状态定义

| 状态 | 定义 |
|---|---|
| `implemented` | 已有实现，且有对应测试证据 |
| `experimental` | 有原型或部分测试，但关键集成、兼容性或安全门槛未完成 |
| `planned` | 已进入设计或路线图，尚无可验收实现 |
| `blocked` | 存在明确依赖或阻断问题 |
| `not-tested` | 有实现线索，但当前没有足够测试证据 |

测试结果状态另行记录：`pass`、`fail`、`skipped`、`not-run`。

## 3. 当前基线与已知事实

依据仓库当前 PDKS 0.5.3 / 0.5.3.1 预览资料：

- 阶段：`transitional_skill_development`。
- 成熟度：Experimental / Preview，非生产就绪。
- Node-native Bootstrap 已有实现和自动化测试证据；初始化采用 plan / approval / apply / verify。
- `pdks-setup` Skill 已在当前 GitHub 镜像目录中。
- 可选 Capture Runtime 0.1.1 仍为独立 Python 组件；Node-native Vault 初始化不要求 Python。
- DingTalk DWS 官方 CLI 适配器已有实现路径和测试报告记录，但真实租户交付尚未验证，历史分页/回补未实现。
- File Store Adapter 0.1.0 是单向 Runtime-to-Vault 投影，不是双向同步。
- Vault 文件当前未实现静态加密；预览阶段只应用合成或非敏感数据。
- 当前发布验证报告记录 162 项测试：160 项通过、2 项跳过、0 项失败；其中 npm 构建、MCP Inspector、MCP Apps 渲染、跨宿主和真实 DWS 租户测试仍未执行。
- GitHub 镜像状态说明完整源工程尚未逐文件展开到仓库；因此不能仅凭目录入口或 README 推断完整工程已在 GitHub 可审查。

以上是当前预览资料所记录的状态，不等同于本轮对所有源代码重新运行测试。发布前必须在目标环境重新验证。

## 4. Skills 清单与状态矩阵

| Skill / 能力 | 优先级 | 当前状态 | 主要验收重点 |
|---|---:|---|---|
| `pdks-setup` | P0 | `experimental` | 安装前诊断、计划、精确审批、初始化、校验、拒绝路径无写入 |
| `pdks-personal-knowledge` | P0 | `not-tested` / 需核对发布包 | 标准知识工作流、证据、保存、检索和迁移；先核实实际 Skill 文件与版本 |
| `dingtalk-capture` | P0 | `experimental` | DWS 授权、增量采集、消息 ID、断点、错误处理、真实租户验证 |
| `file-capture` | P0 | `planned` | 文件格式覆盖、哈希、页码/段落定位、目录边界和恶意文件处理 |
| `event-extractor` | P0 | `planned` | 事件类型映射、主体/时间/对象、证据引用、误提漏提 |
| `knowledge-classifier` | P0 | `planned` | 多轴分类、未知类处理、置信度和人工纠正 |
| `knowledge-archiver` | P0 | `planned` | 候选/确认区隔、文件安全写入、幂等和版本更新 |
| `personal-recall` | P0 | `planned` | 授权过滤、证据排序、引用准确性和敏感内容隔离 |
| `email-capture` | P1 | `planned` | 邮件线程、附件、OAuth 授权、撤销 |
| `calendar-capture` | P1 | `planned` | 时区、重复日程、计划与实际时间区分 |
| `meeting-capture` | P1 | `planned` | ASR 时间戳、说话人不确定性、音频保留策略 |
| `browser-capture` | P1 | `planned` | URL、来源时间、网页正文与引用定位 |
| `ai-conversation-capture` | P1 | `planned` | 用户输入、模型输出和工具结果严格区分 |
| `knowledge-validator` | P1 | `planned` | 来源核验、冲突检测、事实状态和质量报告 |
| `knowledge-deduplicator` | P1 | `planned` | 内容哈希、来源 ID、语义近重复与人工合并 |
| `obsidian-publisher` | P1 | `planned` | Markdown/YAML 兼容、链接稳定、只发布获准内容 |
| `knowledge-lifecycle` | P1 | `planned` | 更新、替代、过期、撤回、删除和备份边界 |
| `daily-review` / `weekly-review` | P2 | `planned` | 时间范围、证据完整、行动闭环和用户可修正 |
| `project-memory` / `experience-reuse` | P2 | `planned` | 适用范围、反例、跨项目迁移边界 |
| `knowledge-insight` | P2 | `planned` | 相关性、因果谨慎、样本量和推断标记 |

状态矩阵必须随代码和发布包更新。若发现某 Skill 已经在发布包中实现，应补充具体文件路径、版本、测试证据后再调整状态。

## 5. 通用验收矩阵

### 5.1 标准与数据契约

| ID | 验收项 | 通过条件 | 阻断级别 |
|---|---|---|---|
| STD-01 | Schema 校验 | 所有必填字段、类型、枚举和约束通过当前 Record Schema | Blocker |
| STD-02 | 版本兼容 | 记录明确 schema_version；旧版本读取/迁移有测试 | Blocker |
| STD-03 | Taxonomy 映射 | 未知事件类型不得静默伪装成已知类型 | High |
| STD-04 | Ontology 兼容 | 不修改冻结术语含义；变更具备迁移与回滚 | Blocker |
| STD-05 | 时间语义 | occurred_at、captured_at、recorded_at 和时区不混淆 | High |
| STD-06 | 来源追溯 | 每条重要知识可追溯 source_id 与证据定位 | Blocker |
| STD-07 | 认知状态 | 明确声明、观察、推断、假设和已验证状态可区分 | Blocker |

### 5.2 连接器与采集

| ID | 验收项 | 通过条件 | 阻断级别 |
|---|---|---|---|
| CAP-01 | 独立授权 | 未授权来源无法开始采集 | Blocker |
| CAP-02 | 最小范围 | 只读取用户授权的对象、时间范围和字段 | Blocker |
| CAP-03 | 增量采集 | 保存游标/检查点，重启后可继续 | High |
| CAP-04 | 幂等 | 同一来源记录重复采集不产生重复资产 | Blocker |
| CAP-05 | 分页与边界 | 分页完整性、时间窗口和边界条件有测试 | High |
| CAP-06 | 失败恢复 | 网络错误、限流、令牌失效可报告并恢复 | High |
| CAP-07 | 撤销 | 撤销授权后停止后续采集并执行既定数据策略 | Blocker |
| CAP-08 | 历史回补 | 若未支持必须明确标记，不得声称完整历史同步 | Medium |
| CAP-09 | 来源版本 | 原始记录编辑或更新能识别版本变化 | High |

### 5.3 事件与知识加工

| ID | 验收项 | 通过条件 | 阻断级别 |
|---|---|---|---|
| KNO-01 | 原文保留 | 摘要和抽取结果不覆盖原始资料 | Blocker |
| KNO-02 | 证据绑定 | 事件、事实和决策候选有可定位证据 | Blocker |
| KNO-03 | 角色识别 | 不混淆发言者、被提及者、负责人和参与者 | High |
| KNO-04 | 时间识别 | 能区分事件发生时间、消息时间和计划时间 | High |
| KNO-05 | 事实与推断 | 推断不自动升级为确认事实 | Blocker |
| KNO-06 | 冲突处理 | 冲突保留双方来源并进入待审状态 | High |
| KNO-07 | 去重 | 重复和近重复识别有可解释依据 | Medium |
| KNO-08 | 质量报告 | 输出缺失项、置信信息、来源和处理版本 | High |
| KNO-09 | 用户纠正 | 用户可修正候选，系统保留修正记录 | High |

### 5.4 存储、导出和生命周期

| ID | 验收项 | 通过条件 | 阻断级别 |
|---|---|---|---|
| STO-01 | File-first 可读 | Markdown 可由 Obsidian 和普通编辑器打开 | High |
| STO-02 | 机器交换 | JSON/JSONL 可按 Schema 解析 | High |
| STO-03 | 权威边界 | SQLite、文件库和语义资产职责明确，无双写权威冲突 | Blocker |
| STO-04 | 附件完整性 | 内容哈希可验证，路径穿越被拒绝 | Blocker |
| STO-05 | 幂等归档 | 重复发布不会覆盖用户手工内容 | Blocker |
| STO-06 | 导出完整 | 导出包含必要记录、来源、附件引用和版本信息 | High |
| STO-07 | 备份恢复 | 恢复后记录数、哈希和关系完整性可验证 | Blocker |
| STO-08 | 生命周期 | 更新、替代、过期、删除和索引清理有测试 | High |

### 5.5 安全与治理

| ID | 验收项 | 通过条件 | 阻断级别 |
|---|---|---|---|
| SEC-01 | 未授权访问 | 所有越权读取/写入测试均被拒绝 | Blocker |
| SEC-02 | 精确审批 | 写入、删除、共享和外部动作绑定具体计划 | Blocker |
| SEC-03 | 凭据保护 | 日志、对话、报告和导出不泄露凭据 | Blocker |
| SEC-04 | 敏感级别 | P0-P3 或兼容枚举正确传播并执行策略 | Blocker |
| SEC-05 | 数据出境 | 未授权不得上传、共享或云端同步 | Blocker |
| SEC-06 | 删除边界 | 删除范围、备份残留和索引清理可审计 | High |
| SEC-07 | 审计 | 操作者、Agent、来源、时间和结果可追溯 | High |
| SEC-08 | 恶意内容 | 文件和来源内容不能覆盖系统指令或触发越权工具调用 | Blocker |
| SEC-09 | 加密 | 正式版本必须完成静态加密、密钥管理和恢复测试 | Blocker |

**特别说明：** SEC-09 当前未通过。PDKS 0.5.3 预览版 Vault 尚未实现静态加密，因此不能以真实 P2/P3 数据进行验收或生产部署。

### 5.6 Agent Host 与安装

| ID | 验收项 | 通过条件 | 阻断级别 |
|---|---|---|---|
| AGT-01 | Skill 加载 | SKILL.md 可被目标宿主正确识别 | High |
| AGT-02 | 工具发现 | MCP 工具可发现、可调用、返回结构符合 Schema | High |
| AGT-03 | 文本回退 | 不支持 MCP Apps 的宿主仍能完成核心流程 | High |
| AGT-04 | 本地桥接 | 云端宿主不能绕过本地授权直接访问文件 | Blocker |
| AGT-05 | 宿主配置 | 安装器不擅自修改 Agent 配置 | Blocker |
| AGT-06 | 多宿主一致性 | 相同输入在不同宿主使用同一标准结果结构 | High |
| INS-01 | macOS 安装 | 安装、升级、卸载和恢复通过 | High |
| INS-02 | Windows 安装 | PowerShell 安装、路径、权限和恢复通过 | High |
| INS-03 | Linux 安装 | Shell 安装、路径、权限和恢复通过 | High |
| INS-04 | 依赖隔离 | 初始化 Vault 不强制安装可选采集依赖 | High |
| INS-05 | 安装可回滚 | 失败后不破坏用户现有文件 | Blocker |

## 6. PDKS 0.5.3 预览版专项验证状态

| 验证项 | 当前记录 | 结论 |
|---|---|---|
| Setup / Skill / Release Smoke | 47 项，46 通过，1 跳过 | 已有自动化证据 |
| Ontology / ADS Prototype | 33 项，32 通过，1 跳过 | 已有自动化证据 |
| Capture Runtime + DWS + File Store | 64 项全部通过 | 有组件级测试证据；不代表真实租户验证 |
| Node Agent Bridge + Native Bootstrap | 18 项全部通过 | 有组件级测试证据 |
| 总计 | 162 项，160 通过，2 跳过，0 失败 | 预览版自动化测试记录 |
| npm Build | 未执行，缺少 Vite / 网络依赖 | 未通过验收，不计通过 |
| MCP Inspector | 未执行 | 未通过验收，不计通过 |
| MCP Apps 渲染 | 未执行 | 未通过验收，不计通过 |
| Windows / macOS / Linux 完整安装 | 未执行 | 未通过验收，不计通过 |
| Claude / Cursor / Codex / WorkBuddy 宿主验证 | 未执行 | 未通过验收，不计通过 |
| 真实 DWS 租户交付 | 未执行 | 未通过验收，不计通过 |
| Vault 静态加密 | 未实现 | 阻断生产使用敏感数据 |

## 7. 分阶段准入门槛

### G0 — 规范与契约冻结

- 总体标准、Record Schema、Event Taxonomy、Ontology 和 Skills 契约有明确版本。
- 每个字段和术语有定义、示例、约束和兼容说明。
- 至少一组端到端合成样例可完成 Schema 与语义验证。

### G1 — 可安全初始化

- doctor / plan / approval / apply / verify 全流程通过。
- 拒绝、取消、计划变更和路径冲突时不得产生未授权写入。
- 保留用户已有文件；安装、升级和卸载不删除用户 Vault。
- 安装文档可由普通用户或 Agent 按步骤完成。

### G2 — 首个数据采集闭环

- 钉钉 DWS 和本地文件至少各完成一条可复现采集链。
- 来源授权、增量、幂等、证据定位、失败恢复和撤销通过。
- 未实现的历史回补、平台权限或来源能力明确披露。

### G3 — 事件与知识闭环

- 标准记录、事件、事实候选、决策候选、任务候选可关联。
- 重要抽取项有证据；推断与事实分离。
- 冲突、纠错、用户确认、更新和过期有端到端测试。

### G4 — 多 Agent 与治理闭环

- 至少两个不同 Agent Host 使用同一 Vault 和同一数据契约。
- 权限过滤、敏感等级、审计、数据导出和删除测试通过。
- Skill 安装和工具执行不依赖单一模型或单一宿主。

### G5 — 生产就绪

- 静态加密、OS Keychain、备份恢复、保留和删除策略完成。
- Windows、macOS、Linux 安装升级与回滚通过。
- 真实来源集成、Agent Host 兼容、MCP 协议和安全测试通过。
- 性能、可靠性、隐私、安全评审和发布签署完成。
- 不存在未披露的 Blocker。

## 8. AI 抽取质量的评估建议

在建立人工标注的黄金测试集之前，不得以模型自评作为质量验收。

建议先建立覆盖以下场景的合成黄金集：

- 明确时间、相对时间、无时间和多时区；
- 多人发言、被 @、被提及、负责人和旁观者；
- 计划、承诺、决策、建议和已完成结果；
- 反讽、否定、撤回、纠错和引用他人话语；
- 多来源共同描述同一事件；
- 互相矛盾和过期信息；
- 高敏感内容和提示注入内容。

初始目标值（需在标注集建立后校准）：

- 来源和证据定位准确率：100%；
- 未授权操作：0；
- 事实/推断状态混淆：0 个阻断级错误；
- 关键事件字段 Precision：≥0.90；
- 关键事件字段 Recall：≥0.80；
- 重复采集造成的重复权威记录：0。

以上是建议准入目标，不是当前模型已经达到的实测结果。

## 9. 单个 Skill 的发布验收包

每个 Skill 发布必须附：

1. Skill ID、版本、适用宿主和运行环境；
2. `SKILL.md` 与完整使用说明；
3. 输入输出 JSON Schema 或明确的结构化契约；
4. 工具权限、授权范围和副作用清单；
5. 单元测试、契约测试、集成测试和安全测试结果；
6. 至少一个合成端到端示例；
7. 错误码、重试、幂等和恢复说明；
8. 已知限制、未执行测试和依赖项；
9. 文件清单与 SHA-256；
10. 更新、迁移、卸载和回滚说明。

## 10. 验收结论模板

每次验收报告必须采用以下结构：

```text
项目 / Skill：
版本：
Agent Host / OS：
数据源与授权范围：
测试环境：
测试集版本：
总测试数：
通过 / 失败 / 跳过 / 未执行：
Blocker：
High：
未验证风险：
证据链接：
验收结论：PASS / CONDITIONAL PASS / FAIL
```

- **PASS：** 所有适用的 Blocker 和 High 项通过，且无未披露的重大限制。
- **CONDITIONAL PASS：** Blocker 通过，但存在明确列出的非阻断限制和到期整改计划。
- **FAIL：** 任一 Blocker 失败、出现越权行为或关键证据缺失。

---

**验收声明：** 本矩阵是准入规则，不是测试结果。只有附带可复现证据的测试项才能标记为通过。
