# 给 Codex / WorkBuddy 的 PDKS 全量 GitHub 同步任务

把 PDKS 0.5.3.1 完整工程同步到 `yixuan2016/creative` 仓库独立目录 `PDKS/`。

## 输入
- ZIP：`PDKS_0.5.3.1_完整综合工程包.zip`
- Git：`https://github.com/yixuan2016/creative.git`
- 工具：ZIP 内 `PDKS/tools/sync-release.py`
- SHA-256：`1a67e8f296b81e8aeb381c43afeaf7aa64a3141a3bf15391f4d0fe47d186b4ea`

## 必须按顺序执行
1. 检查 Python 3.10+、Git 和仓库工作区状态。若有用户未提交改动，停止，不要 reset/clean。
2. 确保仓库为 creative 的 main；fetch 并检查，不要 force-push。
3. 核对 ZIP SHA-256。
4. 先执行 dry-run：`python PDKS/tools/sync-release.py --archive "<ZIP>" --repo "<creative>"`。
5. 展示校验结果、文件数量和目标目录，等待用户确认。
6. 用户确认后执行 `--apply`。
7. 展示 `git diff --cached --stat` 和 `git diff --cached --name-status`；确认变更仅在 PDKS，且无凭据、.env、Vault 私人数据、录音原始文件、备份、node_modules 或构建产物。
8. 再次向用户确认是否 commit/push。未确认不得提交。
9. 获得确认后普通 commit + `git push origin main`；禁止 force-push。
10. 推送后重新读取 GitHub main/PDKS，校验 MANIFEST.json、MANIFEST.sha256、文件数、文件大小和 SHA-256。只有全部通过才报告“全量同步完成”。

## 禁止事项
- 不读取、不上传真实个人 Vault、录音、邮件或其他个人采集数据。
- 不连接钉钉 DWS 或其他数据源，不启动采集服务。
- 不删除仓库已有文件，不覆盖用户未提交改动。
- 遇到任何冲突或校验失败立即停止。
- 本任务只同步研发源代码、标准、文档、测试和示例。

PDKS 仍处于 `transitional_skill_development` / Experimental Preview，不是生产就绪的 Personal AI Life OS。
