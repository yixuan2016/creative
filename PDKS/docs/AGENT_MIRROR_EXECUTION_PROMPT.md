# 给 Codex / WorkBuddy 的 PDKS 全量 GitHub 同步任务

把 PDKS 0.5.3.1 完整工程同步到 `yixuan2016/creative` 仓库独立目录 `PDKS/`。

- ZIP：`PDKS_0.5.3.1_完整综合工程包.zip`
- Git：`https://github.com/yixuan2016/creative.git`
- 工具：`PDKS/tools/sync-release.py`
- SHA-256：`1a67e8f296b81e8aeb381c43afeaf7aa64a3141a3bf15391f4d0fe47d186b4ea`

## 执行步骤
1. 检查 Python 3.10+、Git 和仓库状态。若工作区有未提交改动，停止；不要 reset/clean。
2. fetch 并检查 main，不要 force-push。
3. 核对 ZIP SHA-256。
4. 先 dry-run：`python PDKS/tools/sync-release.py --archive "<ZIP>" --repo "<creative>"`。
5. 展示校验结果和文件数量，等待用户确认。
6. 用户确认后执行 `--apply`。
7. 展示 staged diff；确认只涉及 PDKS 且不含凭据、.env、个人 Vault、录音原始文件、备份、node_modules 或构建产物。
8. 再次向用户确认 commit/push。未确认不得提交。
9. 获得确认后普通 commit + `git push origin main`，禁止 force-push。
10. 推送后核验 GitHub main/PDKS 的 manifest、文件数、大小及 SHA-256；全部通过才可称全量同步完成。

禁止读取/上传真实个人 Vault、录音、邮件；不连接 DWS、不启动采集服务、不删除仓库文件。发生冲突或校验失败立即停止。

PDKS 仍处于 `transitional_skill_development` / Experimental Preview，不是生产就绪的 Personal AI Life OS。
