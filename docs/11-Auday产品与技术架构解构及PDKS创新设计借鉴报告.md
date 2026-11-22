# Auday 产品与技术架构解构及 PDKS 创新设计借鉴报告

> 报告编号：PDKS-REF-AUDAY-001  
> 版本：V1.0 · Research  
> 日期：2026-11-22  
> 研究性质：公开产品资料、官方文档与公开代码仓库的静态调研；不是实机测试报告，也不代表对 Auday 内部未公开实现的判断。

## 一、执行摘要

### 1.1 核心结论

Auday 值得 PDKS 研究，但不应被当作 PDKS 的整体架构模板。

Auday 的关键价值不只是“Apple Watch 录音”，而是把日常声音与时间、活动、身体状态、地点和个人记忆联系起来，再通过桌面 Skill 将手机中的个人上下文交给 AI Agent 使用。它已经形成一条相对完整的产品链路：

**低干预采集 → 设备端处理 → 时间线与上下文关联 → 高光/反思/记忆 → 可追溯检索 → Agent 工作流接入。**

它验证了一个重要方向：个人 AI 要真正理解一个人，不能只依赖用户主动输入的文字，也需要在用户授权、可见、可控的前提下，持续获得真实生活与工作的上下文。

但 Auday 仍是一个以 Apple Watch 音频为中心的个人应用，不等于跨来源、跨平台、跨主体的个人数智底座。它没有完整覆盖个人目标与承诺运行模型、通用事件本体、企业授权投影、多 Agent 受控执行和组织级治理。

**对 PDKS 的建议：吸收 Auday 的低摩擦采集、原始证据回溯、本地优先、增量同步和 Agent 接入经验；在此基础上继续发展多源事件融合、覆盖完整性、记忆血缘、可撤回授权和个人—企业安全协同。**

### 1.2 本报告的主要判断

1. **采集入口不是底座本身。** Apple Watch、手机、录音卡、会议、日历、邮件和协作工具都是来源；PDKS 应建立统一的来源与采集契约，而不是围绕某个硬件设计。
2. **原始记录、事件、记忆、目标和行动必须分层。** Auday 已将音频、转录、AI 结果和记忆分开处理；PDKS 应进一步把证据、事件断言、长期记忆、承诺任务和 Agent 动作区分为不同对象。
3. **时间线必须有证据和完整性语义。** 记录到声音不代表事件完整，未保存静音、录音中断、待同步、转录失败和无语音是不同状态。
4. **本地优先不等于没有外部数据流。** AI 服务商、地理编码服务和可选云端转录仍可能接收数据，必须按功能、接收方和用途单独授权。
5. **个人记忆不能自动成为企业资产。** 个人侧可以保留完整工作与生活上下文；企业侧只接收经授权、最小必要且符合业务责任边界的投影。
6. **PDKS 当前预览版仍有明确工程边界。** 当前 0.5.3 是过渡阶段预览，原生初始化、可选采集运行时和真实连接器验证必须分别看待，不能把架构设计等同于生产能力。

## 二、调研范围、方法与证据边界

本报告检查了以下公开材料：

- Auday 官方产品页、FAQ、隐私政策与中国区 App Store 页面；
- Auday Skill 的公开 GitHub 仓库，包括 Skill 说明、连接协议、本地资料库、语义检索、音频分析和首次安装验证文档；
- creative 仓库中的 PDKS 当前 README、Agent-native Bootstrap、Storage、Runtime、Connectors 说明；
- ADS-WORK-08《企业工作本体与事件驱动的个人—企业—领域协同标准研究》；
- ADS-WORK-09《个人数智底座的持续记忆、事件账本与自主智能体架构研究》；
- ADS-WORK-10《个人数智底座的产品形态、多终端感知入口与个人助理 OS 交互架构研究》。

**证据边界：**
- 产品功能和版本信息以调研日期可访问的官方页面为准，价格、评分和版本会变化。
- GitHub 代码与文档能够说明公开实现意图和工程边界，但不能代替真实设备、真实网络和真实数据的验收。
- 本次没有实际购买、安装和连续使用 Auday，也没有验证不同 Apple Watch 型号上的录音质量、续航或连接稳定性。
- 本报告中的 PDKS 新增标准建议是研究提案，不代表已经合并到当前标准或已完成研发。

## 三、Auday 产品解构：从录音工具到个人上下文系统

### 3.1 当前产品定位与版本观察

截至 2026-11-22，中国区 App Store 页面显示 Auday 版本 1.1.0，版本日期为 2026-11-14，价格页面显示人民币 ¥68，产品采用一次购买、无 Auday 会员订阅的模式；AI 服务商费用由用户按自己的配置承担。页面显示需要 iOS 18+ 与 watchOS 11+。价格和评分均为动态信息，应以购买时 App Store 页面为准。

1.1.0 重点更新包括：
- 录音抗打断机制：按指引配置后，闹钟、Siri、来电等中断结束时可自动接续录音；
- 与睡眠计划、专注模式和快捷指令联动；
- 改进后台连续转录、进度、搜索和聊天历史的加载；
- 已保存记忆独立于原始记录，原始录音修改或删除后，记忆仍可用于 AI 对话；
- 优化云端/自建转录恢复，以及与兼容 Auday Skill 的桌面音频读取效率。

这说明产品迭代重点正在从“能录下来”转向“长期运行可靠、数据处理可恢复、记忆能够持续使用”。

### 3.2 产品能力拆解

| 能力层 | Auday 的产品实践 | 对用户的价值 | 需要注意的边界 |
|---|---|---|---|
| 采集 | 用户在 Apple Watch 主动开始录音、标记重要时刻 | 降低额外设备和主动记笔记成本 | 不是保证 24 小时无中断的被动采集 |
| 传输 | Watch 录音传到 iPhone，通常按约 15 分钟节奏准备同步，也可能在整点、暂停或结束时提前准备 | 让录音在手机端进入处理流程 | 受连接和 Apple 后台调度影响，不是实时逐字转写 |
| 转录 | iPhone 本地转录；提供高效和高精度模式 | 将音频转成可搜索文本 | 准确率受语言、口音、噪声和重叠语音影响 |
| 说话人 | 可选本人声纹匹配，部分转录服务也支持说话人分段 | 帮助区分本人发言和其他发言 | 本人声纹匹配不等于识别所有真实说话人身份 |
| 上下文 | 可选关联 Apple Health 身体/活动数据与 Watch 位置观察 | 让回顾不只依赖文字 | 压力是生理状态估计，不是情绪识别；地点是近似场景，不是精确轨迹 |
| 理解 | Highlights、小时/每日 Summary、Daily Reflection、AI Chat | 降低长录音回顾成本 | 生成结果属于 AI 派生内容，不等于已确认事实 |
| 记忆 | 保存人物、偏好、计划等记忆，可查看、编辑或停用 | 让后续对话不必每次从零开始 | 记忆可能独立于原始录音保留，必须明确来源和删除策略 |
| 检索 | 关键词搜索与本地语义搜索 | 能按原词或含义找回内容 | 语义相似度不是事实置信度 |
| 导出 | 按日期/小时批量导出 M4A、TXT 与 Markdown AI 内容 | 便于迁移和跨工具分析 | 导出文件可能脱离 App 原有权限与生命周期 |
| Agent 接入 | Auday Skill 将已保存内容接入兼容桌面 AI 助手 | 让个人记忆进入更广泛的工作流 | 手机端接入只读，不能把 Agent 接入理解为可写回手机 |

### 3.3 关键数据流

**Apple Watch → iPhone → 本地处理 → AI 记忆与回顾 → 桌面 Agent**

1. Watch 侧产生录音片段、时间和用户标记。
2. iPhone 接收录音并管理原始音频。
3. 本地转录生成文字和时间对齐信息，形成关键词/语义索引。
4. 用户可选择加入身体状态和位置上下文。
5. 配置 AI 服务后，生成 Highlights、Summary、Daily Reflection 和 Chat。
6. 通过 Auday Skill 将授权范围内的文字或音频接入电脑端 Agent。
7. 电脑端建立自己的 SQLite 缓存、Markdown 资料库和可选语义索引。

其中，“录音”“同步”“转录”“AI 生成”和“桌面同步”是不同阶段。不能把 Watch 正在录音理解为 iPhone 已经收到，也不能把录音完成理解为转录和 AI 结果已经完成。

### 3.4 身体与地点上下文的价值及边界

Auday 可在用户授权后读取 Apple Health 中的心率、HRV（SDNN）、静息心率、步数、睡眠和锻炼数据，并在设备端结合个人历史形成生理状态估计。其 FAQ 说明，基线会参考最多 14 天的历史数据，但可用性取决于测量密度和同步情况。

位置方面，Watch 在录音期间采集可用的位置观察，iPhone 将其聚合为近似地点；为了得到可读地名，会向 Apple 地理编码服务发送坐标。

这些信息有助于回答“当时大概处于什么活动或场景”，但不能证明某次对话导致压力、不能推断真实情绪，也不能证明用户进入了某栋建筑。PDKS 应借鉴“上下文辅助回忆”，而不是复制敏感数据采集本身。

## 四、Auday Skill 解构：真正值得 PDKS 研究的技术部分

### 4.1 桌面 Skill 的定位

Auday Skill 是公开的桌面 AI 工作流扩展，目标是把 Auday iPhone 中已保存的转录、Highlights、反思、记忆和录音接入电脑上的兼容 Agent。公开仓库采用 MIT License。

它支持 macOS、Windows 10/11 x64 和 Windows 11 ARM64。首次配置由桌面 Agent 协助完成环境检查、工具准备、模型下载校验和手机连接，不要求用户先自行准备完整 Python 开发环境。不同宿主 Agent 的 Skill 安装位置和发现方式仍然不同。

### 4.2 手机与电脑之间的连接

公开协议说明：
- iPhone 与电脑通过同一局域网直接连接，不经过 Auday 云端中继；
- 使用手机生成的 16 字符通信密钥，协议使用 HKDF-SHA256 和 TLS 1.2 ECDHE-PSK / ChaCha20-Poly1305；
- 用户在手机端选择“全部文字”或“文字与音频”只读范围；
- 手机接入页面需要在传输期间保持打开；
- 音频按需获取，不要求首次同步就下载所有音频；
- 手机端数据不会因为桌面 Skill 接入而获得写入或删除权限。

这套设计的价值在于：把“手机个人资料库”变成“Agent 可授权读取的上下文源”，同时将传输范围、设备连接和用户授权分开处理。

### 4.3 桌面端存储与文件库

Auday Skill 在电脑端维护 SQLite 数据库，并同步生成可读的 Markdown 文件库。公开文档给出的典型结构包括：

- 总目录与索引；
- 按日期和记录类型组织的 Markdown 记录；
- 来源清单、版本和文件哈希；
- 独立的用户 notes 目录；
- 已替换、移除或迁移文件的 archive；
- 人工修改与生成文件冲突的 conflicts。

值得借鉴的工程细节：
1. 原始同步数据库与可读文件库分工明确。
2. 用户笔记与系统生成记录分开，避免自动刷新覆盖个人编辑。
3. 文件使用稳定来源 ID 和哈希维护，变化时尽量只更新受影响内容。
4. 默认增量同步：核对轻量清单，只传输新增、变更或本地损坏的文字正文。
5. 单次同步固定一个快照，避免边同步边追逐不断变化的数据。
6. 语义索引与原始数据库分开维护，索引可从源数据重建。

### 4.4 本地语义检索与音频分析

Auday Skill 的公开语义检索文档使用本地 EmbeddingGemma 300M 模型，模型文件约 333.59 MB，配合本地运行时生成持久向量索引，不依赖外部 Embedding API。索引记录保留来源 ID、时间、状态和文本片段定位；检索结果仍可回读原始记录。

录音分析按需准备本地转写模型，并可使用说话人分段工具。公开文档列出 Whisper small Q5_1（约 190 MB）和 large-v3-turbo Q5_0（约 574 MB）等路线。它将转写结果、原始时间线和说话人候选作为独立派生物保存，而不是覆盖源音频。

**值得借鉴的不是某个具体模型，而是模型按需安装、哈希校验、能力独立验证、索引可重建、音频按需获取和来源定位可回溯的工程方法。**

### 4.5 Skill 的已知边界

- 只读接入，不是完整双向同步或手机端写回接口。
- 连接依赖局域网、手机授权页和本地配对密码。
- 协议当前没有逐台电脑的独立身份授权与撤销机制。
- 桌面文件库不独立加密，主要依赖操作系统账户权限保护。
- 公开文档将合成连接测试与真实 iPhone 无线实机验证明确区分；CI 通过不能代替实机验收。
- 本地传输不代表桌面云端 Agent 的推理也在本地；被送入云端 Agent 的上下文片段仍可能离开本机。

## 五、与当前 PDKS 及 ADS 研究的对照

### 5.1 当前 PDKS 工程基线

截至本次调研，creative 仓库中的 PDKS README 标明当前版本为 **0.5.3 Node-native Agent Bootstrap Preview**，阶段为 transitional_skill_development，成熟度为 Experimental / Preview。

当前工程说明包括：
- Record Schema 0.1.x、Event Taxonomy 0.1.0、Ontology 0.2.1；
- Node-native Agent Bridge / MCP Tools，可选 MCP Apps；
- Node-native Bootstrap 可初始化 File-first Vault；
- 可选 Personal Capture Runtime 仍是独立 Python 组件；
- 存储采用 Markdown + YAML、JSON/JSONL、内容哈希附件，SQLite 用于可选 Runtime 的运行数据；
- 当前 File Store Adapter 0.1.0 是 Runtime 到 Vault 的单向投影，不是双向同步；
- DWS 官方 CLI Connector 仍处于预览，真实租户验证和历史分页回填尚未完成；
- Vault 当前没有静态加密；原生初始化不连接数据源、不导入历史、不启动后台采集、不启用云同步。

因此，PDKS 当前已具备标准、Agent 初始化和 File-first 存储方向，但不能描述为已经具备 Auday 那样的全天候设备采集、可靠同步和完整端到端运行能力。

### 5.2 能力对照矩阵

| 对照维度 | Auday / Auday Skill | PDKS 当前基线与既有设计 | 研究判断 |
|---|---|---|---|
| 产品目标 | 个人日常记录、回顾与记忆 | 个人数据知识底座，向 Personal AI Life OS 演进 | PDKS 范围更广 |
| 采集入口 | Apple Watch 录音为核心，辅以 Health/Location | 手动输入、连接器和可选 Capture Runtime；多终端感知是架构目标 | PDKS 应保持来源无关 |
| 采集可靠性 | 已实现中断恢复、传输恢复和处理进度优化 | 当前预览尚无 Node-native 后台设备采集 | Auday 有真实产品经验，PDKS 需补工程验证 |
| 数据模型 | App 专用记录、转录、Highlights、记忆和来源 ID | Record Schema、Event Taxonomy、Ontology | PDKS 应承担跨来源统一语义 |
| 事件理解 | 以录音时间线、Highlights、Summary 和反思组织 | ADS-WORK-08 明确区分 Signal、Event、Activity、Task、Commitment、Decision | PDKS 语义边界更完整 |
| 证据回溯 | 文字可关联原话、录音时间线和来源记录 | ADS-WORK-09 以 Event Ledger、Source Vault 和 Evidence 为基础 | 两者方向一致，PDKS 应扩展血缘标准 |
| 记忆管理 | 已保存记忆可独立于原始录音保留 | 记忆生命周期包含 candidate、active、stale、disputed、superseded、withdrawn、expired、archived | PDKS 应明确记忆与来源删除的依赖规则 |
| 目标与承诺 | 可通过 AI 对话理解计划，但不是完整个人运行模型 | ADS-WORK-09 定义 Goal、Commitment、Task、Routine、Project | PDKS 应把“理解”推进到“持续管理” |
| 文件存储 | SQLite + 维护型 Markdown Library + 用户 notes | File-first Vault、Markdown/YAML、JSON/JSONL、内容哈希附件 | 可借鉴维护型文件库与冲突保护 |
| 语义检索 | 已有本地向量检索与来源回读 | PDKS 具备标准与 Skill 方向，需按实际版本逐项验收检索能力 | 不能只看有无向量库，要验收来源定位和索引一致性 |
| Agent 接入 | 专用 Auday Skill，桌面 Agent 只读接入 | Node MCP Bridge、Agent Skills、可选 MCP Apps | PDKS 更适合做通用接入与治理层 |
| Agent 行动 | 主要用于检索、分析和内容加工；手机端只读 | ADS-WORK-09 定义 L0—L3 风险分级、审批、执行验证和事件回写 | PDKS 可进一步形成受约束行动闭环 |
| 隐私与安全 | 本地优先、可选范围、加密传输；存在备份和设备撤销边界 | PDKS 有 Consent Grant 和最小权限设计；当前 Vault 未静态加密 | 两者都需要从原型走向安全验收 |
| 企业协同 | 不是企业级工作上下文平台 | ADS-WORK-08 定义个人到企业的授权最小必要投影 | PDKS/ADS 的核心差异化方向 |

### 5.3 与 ADS-WORK-08/09/10 的映射

| Auday 能力 | ADS-WORK-08 五层本体 | ADS-WORK-09 七层 PDKS 架构 | ADS-WORK-10 产品闭环 |
|---|---|---|---|
| Watch 录音、Health/Location 信号 | L1 Signal & Observation | L1 多源感知与采集 | 自然感知 |
| 转录、时间戳、原始音频引用 | L1 / L2 | L2 Source Vault & Event Ledger | 自动理解 |
| 人物、时间、地点和活动关联 | L2 / L3 | L3 身份、时间与语义解析 | 自动理解 |
| Highlights、Summary、Reflection | L4 Context & Decision | L4 持续记忆与知识视图、L6 Context Plane | 持续记忆 |
| AI Memory | L3 / L4 | L4 Memory Store | 持续记忆 |
| Auday Skill | L5 Capability & Execution | L6 / L7 | 受控执行前的 Agent 接入 |
| 从对话提取行动线索 | L2 / L4 | L5 Personal Intent Model | 主动服务 |
| 个人内容向企业侧授权投影 | 本体映射与治理 | 个人—企业协同 | 企业协同扩展 |

该映射是架构分析，不意味着 Auday 已实现 ADS-WORK-08/09/10 的全部能力。尤其是 Goal、Commitment、Agent Approval、企业投影和完整治理仍是 PDKS 需要继续建设的部分。

## 六、PDKS 应该借鉴什么、避免什么

### 6.1 建议吸收的七项能力

1. **低干预采集体验**：采集状态清晰、操作极少、可标记重要时刻、可中断恢复。
2. **采集—处理—理解分阶段状态**：明确显示录音、同步、转录、索引和 AI 生成各自的进度与失败。
3. **证据回溯体验**：从 AI 摘要和记忆一键回到原始记录、时间段和来源。
4. **本地优先与按需处理**：能本地完成的转录、索引和检索不依赖云端；大模型、云端转录按需授权。
5. **增量同步与快照一致性**：使用清单、哈希、断点恢复和固定快照，避免反复全量搬运。
6. **维护型文件库**：源记录、用户笔记、归档和冲突分区，保持 Obsidian 等 Markdown 工具可读。
7. **Agent 原生接入**：让不同 Agent 在用户授权范围内读取标准上下文，而不是把用户锁定在单一 App。

### 6.2 不应直接复制的设计

- 不把 Apple Watch 或任何单一录音设备设为 PDKS 必需入口。
- 不把持续录音当作默认授权，更不能以隐蔽采集换取覆盖率。
- 不把生理信号推断成情绪、动机或因果事实。
- 不把转录、摘要或模型推断直接变成已确认承诺和正式业务事件。
- 不把“本地传输”宣传为“全链路本地处理”。
- 不把个人生活数据默认带入企业侧。
- 不让记忆脱离来源血缘和删除策略而无限期保留。
- 不把某个产品的内部记录结构当成跨行业通用事件本体。

## 七、PDKS 的创新机会：从产品功能借鉴升级为标准建设

建议将 Auday 研究转化为以下七项标准或架构增强。它们是新增研究提案，需经过 Schema、Ontology、隐私和安全评审后再进入正式版本。

### 7.1 P0：Capture Source Contract（采集来源契约）

统一描述任何来源如何产生数据、允许采集什么、何时采集、如何暂停、如何恢复和如何撤销。

建议字段：
- source_id / source_type / source_device_id；
- capture_session_id；
- permission_scope / consent_grant_id；
- capture_started_at / capture_ended_at；
- observed_at / recorded_at / time_zone；
- capture_mode / sampling_policy；
- source_record_id / source_revision；
- transfer_state / last_acknowledged_offset；
- retention_policy / revocation_state；
- source_health / error_code。

验收重点：不同来源都能被统一描述，但不强迫它们拥有相同采集能力。

### 7.2 P0：Capture Coverage & Gap（采集覆盖与缺口语义）

把“没有数据”拆成可区分的状态：

| 状态 | 含义 |
|---|---|
| captured | 已取得原始数据 |
| quiet_omitted | 系统按策略省略了可确认的静音区间，时间线仍保留 |
| no_speech | 有音频，但未识别到语音 |
| interrupted | 录音过程被系统或用户中断 |
| pending_transfer | 来源设备已有数据，但尚未传到主设备 |
| transfer_failed | 传输失败或校验失败 |
| transcription_pending | 音频已取得，转录尚未完成 |
| transcription_failed | 转录失败，需要重试或人工处理 |
| permission_off | 用户未授权或已关闭该来源 |
| unknown | 无法确定缺失原因 |

核心要求：**系统不能把未知、缺失或未采集描述为“没有发生”。** 任何日总结、事件抽取和 Agent 上下文都应能感知覆盖缺口。

### 7.3 P0：Evidence & Provenance Contract（证据与来源血缘契约）

让每个事件、记忆和结论都能回答：
- 来自哪个源记录、哪个文件或哪个音频片段？
- 原始时间戳、时区和片段偏移是什么？
- 经历了哪些转录、摘要、抽取和人工修改？
- 使用了哪个模型、版本和处理配置？
- 说话人是用户本人、匿名候选还是未知？
- 当前断言是 observed、inferred、confirmed、disputed 还是 stale？
- 是否能回到原始证据，原始证据是否仍可用？

建议每个派生对象携带 parent_source_ids、evidence_refs、transform_chain、model_version、content_hash 和 assertion_status。

### 7.4 P0：Memory Lineage & Deletion Policy（记忆血缘与删除策略）

Auday 1.1.0 将已保存记忆与原始录音解耦，这对持续使用有价值，但也暴露出一个必须明确的设计问题：删除原始记录后，派生记忆是否继续保留、继续被检索和继续被发送给模型？

PDKS 应支持显式策略：
- source_deleted_but_memory_retained：原始来源删除，记忆按用户选择保留；
- cascade_delete：删除来源及依赖它的派生内容；
- detach_and_review：来源删除后，相关记忆进入待复核；
- legal_hold_or_policy_hold：仅在明确制度依据下保留最小必要副本。

每条记忆应有来源依赖清单、用户选择、保留期限、删除传播状态和审计结果。不能让“删除录音”与“删除记忆”之间的关系成为隐含行为。

### 7.5 P0：Device Trust & Local Link Contract（设备信任与本地连接契约）

吸收 Auday 的本地加密传输和只读范围设计，同时补足设备撤销和静态数据保护：

- 每台设备独立身份和密钥；
- 设备配对、授权范围、最后活动时间和状态；
- 单台设备撤销、密钥轮换和失窃处置；
- TLS 或等效安全传输；
- 本地数据库和文件库静态加密策略；
- 快照身份、增量同步、校验和断点恢复；
- 最小权限、只读默认、可审计授权；
- 连接断开后的缓存访问和过期策略。

### 7.6 P1：Context Enrichment Contract（上下文增强契约）

允许在用户明确授权后关联活动、健康、地点、设备状态和日历上下文，但必须：
- 每类来源独立授权、独立关闭；
- 保留采集范围、精度和不确定性；
- 区分原始测量、派生标签和模型解释；
- 不将相关性描述成因果关系；
- 敏感数据默认不投影到企业侧；
- 明确哪些上下文会被送往外部模型。

### 7.7 P1：Agent Context & Action Contract（Agent 上下文与行动契约）

将 Auday 的只读上下文接入与 PDKS 的 L0—L3 受控行动结合：
- Context Package 只包含当前任务必要的信息；
- 每个事实带来源和确认状态；
- 任务候选与正式承诺分开；
- 动作提案绑定目标对象、参数、工具和有效期；
- 高风险动作需要逐次审批；
- 执行后核验真实结果，并写回新的事件；
- Agent 不得因读取权限自动获得写入权限。

## 八、建议的 PDKS 参考架构增强

建议将现有 ADS-WORK-09 七层架构补充为“七层业务能力 + 横向采集可靠性与治理控制面”，而不是另造一个与现有体系冲突的新架构。

**数据主链路：**

多终端与应用来源  
→ Capture Adapter / Source Contract  
→ Source Vault（原始音频、文件、消息和快照）  
→ Personal Event Ledger（事件、时间、证据与状态）  
→ Identity / Time / Semantic Resolution  
→ Memory Compiler（可追溯记忆视图）  
→ Personal Intent Model（目标、承诺、任务和例程）  
→ Context Builder（任务级最小必要上下文）  
→ Personal Agent / Skills  
→ Authorized Projection（经授权的企业侧投影）。

**横向控制面：**
- Consent & Scope：授权、目的、范围、暂停和撤销；
- Provenance & Evidence：来源、证据、处理链和版本；
- Coverage & Quality：采集覆盖、缺口、同步与转录状态；
- Security：设备身份、密钥、静态加密和传输保护；
- Lifecycle：保留、纠错、撤回、删除传播和归档；
- Governance：数据分类、审计、本体/Schema 版本和责任边界。

这一架构与 ADS-WORK-08 的五层本体、ADS-WORK-09 的七层 PDKS 架构、ADS-WORK-10 的五个产品闭环保持兼容。

## 九、与现有 PDKS 工程的落地顺序

| 优先级 | 工作项 | 目标交付 | 验收标准 |
|---|---|---|---|
| P0 | Auday 参考能力矩阵 | 采集、同步、证据、记忆、Agent、安全的对照表 | 每项能力有来源、实现状态和限制 |
| P0 | Capture Source Contract 草案 | JSON Schema + 示例 + 授权字段 | 手动记录、日历、音频至少可表达 |
| P0 | Coverage & Gap 语义 | 事件状态词表和缺口示例 | 能区分静音、省略、中断、未同步、转录失败 |
| P0 | Evidence & Provenance 扩展 | 来源引用、片段定位、处理链和模型版本 | 从记忆可回到原始来源或明确说明不可用 |
| P0 | Memory Lineage 规则 | 来源删除、记忆保留、级联删除和复核策略 | 删除行为可预测、可审计、可验证 |
| P1 | Auday 导入适配器研究 | ZIP/Markdown/TXT/M4A 导入映射 | 不依赖未承诺的私有接口，保留时间和来源 |
| P1 | 本地连接安全评审 | 设备身份、撤销、加密和快照同步要求 | 单设备授权和撤销可验证 |
| P1 | Agent Context Package 验证 | 只读查询、证据引用和最小必要上下文 | Agent 输出能说明依据和不确定性 |
| P2 | 多源融合试点 | 日历 + 用户主动语音/会议记录 + 文档 | 能关联同一事件但不强行合并 |
| P2 | 企业投影试点 | 用户授权的工作事件投影 | 个人生活信息不进入企业侧 |

### 9.1 Auday 接入建议

首期不建议直接依赖 Auday Skill 的内部 SQLite 结构或未承诺稳定的私有实现细节。建议按以下顺序验证：

1. **批量导入路径**：使用用户主动导出的 ZIP、M4A、TXT、Markdown，建立 PDKS Import Adapter。
2. **保留来源信息**：保留日期、小时、原始记录 ID（如导出内容提供）、转录时间、音频文件名、时间偏移和导出批次。
3. **事件化加工**：将转录先作为 Evidence/Source Record，再抽取 Event Candidate，不直接把摘要当作事实。
4. **用户确认**：对人物、承诺、决策和重要事件保留候选状态。
5. **可选 Skill 互操作**：若未来需要直接读取 Auday 桌面资料库，应通过公开、稳定、明确授权的接口或双方确认的集成契约，不复制内部协议作为长期依赖。

## 十、实测验证计划

### 10.1 实测原则

- 先由愿意参与的用户自愿试用；
- 只使用用户本人有权记录的场景，录制他人前遵守告知和同意要求；
- 首轮使用非敏感或合成数据；
- 不采集无关健康、家庭和位置内容；
- 明确手机丢失、导出文件和云端 Agent 的数据风险；
- 将公开文档验证、模拟测试和真实设备测试分开记录。

### 10.2 建议的两阶段试验

**阶段 A：产品与采集可靠性（约 1 周）**
- Watch 连续录音与不同使用场景；
- 中断恢复、手动暂停、睡眠/专注模式联动；
- Watch 到 iPhone 的同步延迟与积压恢复；
- 电量、存储、静音省略和录音缺口；
- 中文多人对话、远近场、噪声和混合语言转录。

**阶段 B：事件、记忆与 Agent 价值（约 1—2 周）**
- 从原始音频定位到转录片段；
- 从转录片段抽取事件候选；
- 区分讨论、建议、承诺、任务和已批准决策；
- 验证本人声纹标签与匿名说话人分段的错误边界；
- 验证语义检索是否能找回不同表述的同一事件；
- 验证删除音频后记忆如何继续使用；
- 验证桌面 Skill 的只读授权、同步、来源引用和本地音频读取。

### 10.3 评测指标

| 维度 | 建议指标 | 评测方式 |
|---|---|---|
| 采集完整性 | 录音覆盖率、缺口率、中断恢复率 | 对照人工记录的测试时段 |
| 同步可靠性 | 同步成功率、平均/最大延迟、断点恢复率 | 记录设备时间和手机接收时间 |
| 转录质量 | CER/WER、时间对齐误差 | 人工标注样本 |
| 说话人归属 | 本人识别 Precision/Recall、误归属率 | 有明确本人/非本人标注的样本 |
| 事件质量 | Event Precision / Recall、事件边界准确度 | 人工标注事件集 |
| 语义关联 | 人物/对象匹配准确率、错误合并率 | 交叉来源样本 |
| 记忆质量 | 记忆正确率、过期识别率、纠错成功率 | 用户抽查与反馈 |
| 证据可追溯 | 结论可回溯比例、时间定位误差 | 随机抽查 AI 输出 |
| Agent 价值 | 任务上下文完整性、建议采纳率、错误行动候选率 | 用户任务评估 |
| 隐私与信任 | 授权理解度、撤销成功率、未授权访问次数 | 用户测试和安全测试 |
| 运行成本 | 电量、存储、模型资源、处理等待时间 | 设备监测和日志 |

具体目标值应在首轮基线测量后确定，不应在没有实测数据时预设“已达到”的准确率或可靠性。

## 十一、风险与待验证事项

| 风险 | 具体表现 | PDKS 应对 |
|---|---|---|
| 采集不完整 | 系统中断、设备未启动、同步延迟 | 覆盖状态与缺口语义 |
| 语音误识别 | 噪声、方言、多人重叠 | 保留原音、时间定位和人工纠错 |
| 说话人误归属 | 声纹或分段错误 | 匿名候选、归属状态和来源证据 |
| 记忆脱离来源 | 原始音频删除但记忆继续使用 | 记忆血缘和删除传播策略 |
| 敏感上下文外发 | AI 请求包含转录、健康、位置或个人资料 | 按接收方和用途独立授权 |
| 设备丢失 | 个人档案没有云端恢复副本 | 用户控制的加密备份与恢复演练 |
| 桌面资料泄露 | 本地文件库未独立加密 | 静态加密、设备撤销和访问审计 |
| 企业越权 | 个人生活或完整录音进入企业系统 | 最小必要投影和个人确认 |
| 过度自动化 | 把口头提及误判为任务或承诺 | 候选状态、确认闭环和动作审批 |

## 十二、最终建议

### 12.1 研究结论

Auday 是一个值得纳入 PDKS 参考样本库的产品案例，尤其在低干预语音采集、设备端处理、时间线回顾、记忆独立管理、增量同步、本地语义检索和 Agent 接入方面具有参考价值。

但 PDKS 不应变成“开源版 Auday”或“录音卡 + 个人知识库”。PDKS 的核心任务是建立跨来源、跨设备、跨 Agent 的个人数据与知识基础设施，并通过统一事件语义、证据血缘、持续记忆和受约束行动，形成可持续演进的 Personal AI Life OS 基础。

### 12.2 建议形成的架构决策

1. 将 Auday 纳入 PDKS 外部参考产品与技术样本，标记为“个人上下文采集与 Agent 接入案例”。
2. 保持 PDKS 的来源无关架构，录音是重要入口但不是唯一入口。
3. 在现有 Record Schema、Event Taxonomy 和 Ontology 基础上，优先研究 Capture Source Contract、Coverage & Gap、Evidence & Provenance 三项标准扩展。
4. 将 Memory Lineage & Deletion Policy 作为持续记忆标准的必备部分。
5. 将设备配对、撤销、静态加密和快照同步纳入本地优先安全基线。
6. 将 Auday 批量导出作为一个可选导入样本，先验证数据映射，不把其内部协议作为 PDKS 的唯一依赖。
7. 个人工作事件进入企业数智底座，必须经过明确授权、最小必要投影和企业业务责任方确认；个人生活数据默认留在个人侧。

**最终定位：Auday 证明了“个人上下文可以被持续采集并交给 AI 使用”；PDKS 要进一步解决“多源上下文如何成为可信事件、可纠错记忆、可推进目标和可治理的个人智能资产”。**

---

## 附录 A：建议优先进入标准讨论的数据字段

以下字段是本报告提出的候选项，不是现有 PDKS Schema 的既有承诺。

| 字段组 | 候选字段 |
|---|---|
| 来源身份 | source_id、source_type、source_device_id、source_record_id、source_revision |
| 采集会话 | capture_session_id、capture_mode、capture_started_at、capture_ended_at |
| 时间语义 | occurred_at、observed_at、recorded_at、time_zone、valid_from、valid_to |
| 覆盖状态 | coverage_status、gap_reason、transfer_state、transcription_state |
| 证据定位 | raw_asset_ref、segment_start、segment_end、content_hash、source_locator |
| 处理血缘 | transform_chain、model_id、model_version、runtime_version、derived_from |
| 主体归属 | speaker_ref、speaker_type、attribution_status |
| 断言与确认 | assertion_status、confidence、reviewed_by、reviewed_at |
| 授权与生命周期 | consent_grant_id、purpose、permission_scope、retention_policy、revocation_state |
| 记忆依赖 | parent_source_ids、memory_lineage、deletion_policy、deletion_status |

## 附录 B：主要公开资料

### Auday 官方资料
- [Auday 官方产品页](https://auday.ai/)
- [Auday 官方 FAQ](https://auday.ai/faq)
- [Auday 隐私政策（2026-10-20 更新）](https://auday.ai/privacy)
- [中国区 App Store 页面与版本历史](https://apps.apple.com/cn/app/auday-watch%E5%85%A8%E5%A4%A9ai%E5%BD%95%E9%9F%B3/id6814210373)

### Auday Skill
- [GitHub 仓库 README](https://github.com/666ghj/auday-skill)
- [Skill 操作规范](https://github.com/666ghj/auday-skill/blob/main/SKILL.md)
- [本地连接协议](https://github.com/666ghj/auday-skill/blob/main/docs/protocol.md)
- [维护型本地资料库](https://github.com/666ghj/auday-skill/blob/main/references/library.md)
- [本地语义检索](https://github.com/666ghj/auday-skill/blob/main/references/semantic-search.md)
- [音频分析流程](https://github.com/666ghj/auday-skill/blob/main/references/audio.md)
- [首次安装与实机验证](https://github.com/666ghj/auday-skill/blob/main/docs/device-testing.md)

### PDKS / ADS 现有研究
- [creative 仓库总览](https://github.com/yixuan2016/creative)
- [PDKS 当前工程基线](https://github.com/yixuan2016/creative/blob/main/PDKS/README.md)
- [PDKS Agent-native Bootstrap](https://github.com/yixuan2016/creative/blob/main/PDKS/agent-native/README.md)
- [PDKS Storage](https://github.com/yixuan2016/creative/blob/main/PDKS/storage/README.md)
- [PDKS Capture Runtime](https://github.com/yixuan2016/creative/blob/main/PDKS/runtime/README.md)
- [PDKS Connectors](https://github.com/yixuan2016/creative/blob/main/PDKS/connectors/README.md)
- [ADS-WORK-08：工作本体与事件协同](https://github.com/yixuan2016/creative/blob/main/docs/08-企业工作本体与事件驱动的个人企业领域协同标准研究.md)
- [ADS-WORK-09：个人事件账本、持续记忆与 Agent](https://github.com/yixuan2016/creative/blob/main/docs/09-个人数智底座的持续记忆事件账本与自主智能体架构研究.md)
- [ADS-WORK-10：Personal Assistant OS 产品与交互架构](https://github.com/yixuan2016/creative/blob/main/docs/10-个人数智底座的产品形态多终端感知入口与个人助理OS交互架构研究.md)
