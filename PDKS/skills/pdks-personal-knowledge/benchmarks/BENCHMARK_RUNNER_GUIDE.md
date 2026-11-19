# Benchmark Runner Prompt / 操作说明

每个宿主只接收 `prompts/` 目录中对应的单个 `.md` 文件，以及完整 Skill 包。不要把 `cases/` 中的评分元数据交给被测 Agent。`cases/` 是评估人员使用的私有评估侧数据（公开仓库中仍然是合成案例，但测试时应隔离评分标签）。

## 执行前
- 确认 Skill 0.3.3 已加载。
- 确认 `SKILL.md` 和引用资源能被宿主读取。
- 记录宿主、模型、工具权限、连接器、安装方式、Skill ZIP SHA-256。
- C12 必须在没有钉钉、录音、持久化工具的受限配置下执行。

## 每次运行
1. 新建独立会话。
2. 将对应 prompt 文件内容原样提交给 Agent。
3. 要求只返回 `OUTPUT_CONTRACT.md` 定义的 JSON envelope。
4. 不要在运行时向 Agent 暗示 expected_record_types、required_terms、forbidden_terms 或 review_focus。
5. 保存原始结果和 SHA-256；敏感内容不得进入公开仓库。
6. 用评估侧 `cases/<case_id>.json` 和 `scripts/evaluate_benchmark.py` 做机器检查。
7. 使用 `EVALUATION_RUBRIC.md` 做人工评分。

## 运行隔离
- 每个 case 重复 3 次，尽可能使用独立会话。
- 两个宿主使用同一版本 Skill、同一 prompt 文件和可比工具权限。
- 不允许 Agent 读取评估侧 case JSON 或本测试的评分报告。
