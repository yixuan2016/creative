# PDKS 0.5.1 验证报告

> 过渡阶段 Skill 开发（Experimental / Preview）。

## 自动化测试

| 测试套件 | 总数 | 通过 | 跳过 | 失败 |
|---|---:|---:|---:|---:|
| Skill 回归 | 39 | 38 | 1 | 0 |
| ADS / Personal Runtime 回归 | 33 | 32 | 1 | 0 |
| Capture Runtime + DWS Connector | 53 | 53 | 0 | 0 |
| **合计** | **125** | **123** | **2** | **0** |

两个跳过项是本地环境未安装 pySHACL 的 SHACL 测试。GitHub Actions 尚未执行。

## 阶段与 Ontology

- 阶段声明校验：12/12，valid。
- Ontology 0.2.1：valid；运行时术语引用与声明 98/98。
- 受控词汇代码：67；事件分类代码：72。
- 历史术语桥接：71/71。
- 需要人工复核的约束放宽：14 项。
- Ontology Manifest：8/8 文件校验通过。
- PDKS Standard、JSON Schema、Ontology、Event Taxonomy 均未升级。

## DWS Connector 0.1.0

已通过 26 项模拟 CLI / NDJSON 自动化测试，覆盖命令参数、profile、认证字段脱敏、事件目录、Schema allowlist、Consent 门禁、事件来源映射、幂等、Calendar biz_id、ready marker、NDJSON 解析和优雅退出。

**真实 DWS 连接尚未验收：**当前开发容器没有安装 DWS，也没有用户 OAuth 会话。因此没有声称真实账号已接通、企业事件已开通或已收到实际消息。

## 尚未实现

- 历史查询分页回填；目前仅有只读命令 Schema 发现。
- 后台服务、开机自启、崩溃自动重启和持久化同步游标。
- 媒体下载、附件抽取、完整听记转写自动化。
- 其他来源 Connector、生产级加密、远程 Relay、多设备同步。
- 原生 ChatGPT / Claude / Codex / Cursor 宿主连接器。

## 结论

本版本完成了 DWS 官方 CLI 的本地参考适配器与 PDKS 来源映射，但尚未完成真实租户的端到端验收。只有在用户自己的 DWS 安装、OAuth、企业 CLI 访问权限和事件投递均验证通过后，才能标记为已连接。
