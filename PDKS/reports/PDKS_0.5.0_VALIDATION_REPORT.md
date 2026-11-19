# PDKS 0.5.0 验证报告

> 研发阶段：过渡阶段 Skill 开发（Experimental / Preview）

## 自动化测试

| 测试套件 | 总数 | 通过 | 跳过 | 失败 |
|---|---:|---:|---:|---:|
| Skill 回归 | 39 | 38 | 1 | 0 |
| ADS / Personal Runtime 回归 | 33 | 32 | 1 | 0 |
| Personal Capture Runtime | 26 | 26 | 0 | 0 |
| **合计** | **98** | **96** | **2** | **0** |

两个跳过项是本地环境缺少 pySHACL 的 SHACL 测试。GitHub CI 工作流会安装 `requirements-dev.txt`，但本轮 GitHub Actions 尚未取得运行结果。

## 阶段与 Ontology

- 阶段声明校验：12/12，valid。
- Ontology 0.2.1：valid。
- Runtime 术语覆盖：98/98。
- 历史术语桥接：71/71。
- 仍需人工审查的约束放宽：14 项。
- Ontology Manifest：8/8 文件校验通过。
- PDKS 0.1.0、JSON Schema 0.1.x、Ontology 0.2.1、Event Taxonomy 0.1.0 均未升级。

## Runtime 演示

本地合成数据端到端演示通过：文本采集 → Source Asset / Evidence → 候选 Event → 用户确认 → PDKS Bundle 导出 → 哈希验证。

CLI 手工采集 Smoke Test 通过。

## 尚未完成

- 真实 ChatGPT、Claude、Codex、Cursor 等宿主适配和跨 Agent 实测尚未执行。
- 原生钉钉、微信、企业微信、邮件、日历等连接器未实现。
- ASR、OCR、PDF、视频及其他 Office 深度提取未实现。
- 设备后台采集、远程/TLS、云端 Relay、多设备同步未实现。
- 生产级加密、身份、密钥管理、授权服务和跨备份删除未实现。
- Runtime 0.1.0 执行 JSON Schema、owner/source/evidence/consent 校验；Ontology 推理和 SHACL 不在 Runtime 内执行，继续使用独立工具链。

## 结论

本版本已完成一个可运行、可测试的本地个人采集 Runtime 参考实现，但还不能宣称已完成全域自动采集、多宿主真实集成或生产级个人数智底座。
