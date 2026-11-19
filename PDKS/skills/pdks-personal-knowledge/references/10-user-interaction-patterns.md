# User Interaction Patterns

## Default interaction
The user should be able to say:
- "整理一下今天的工作。"
- "把这段会议转写沉淀下来。"
- "从这些记录中提炼可复用的方法。"
- "更新一下我当前负责的项目。"
- "查一下之前我和这个项目相关的决策。"
- "把我的 PDKS 数据导出。"

The agent should not ask the user to choose an ontology class or taxonomy code.

## Ask only when material
Ask a single, focused clarification when:
- the speaker/person identity changes the meaning;
- a statement may be a formal decision or just a suggestion;
- action owner or due date is required for execution;
- two entities may be different people/projects;
- permission or sharing scope is unclear;
- an irreversible operation is requested but ambiguous.

## Good response pattern
1. "我识别到 1 次会议事件。"
2. "提取了 2 条明确观点、1 条知识候选和 2 项行动。"
3. "其中 1 项行动没有明确负责人，暂未指定。"
4. "记录已按 PDKS 0.1.0 结构生成；本地校验通过；尚未写入长期数据库。"

## Avoid
- "请先选择 event type。"
- "请填写下面 20 个字段。"
- "我已经记住了" when no persistent memory write happened.
- "领导决定了..." when source only says "领导建议..."。
- "你擅长..." based on one isolated occurrence.

## Prompt examples

- Capture: `请按 PDKS 标准整理这段内容，自动提取事件、观点、知识和行动。`
- Review: `请做本周 PDKS 周回顾，区分已发生事件、待办、决策、知识候选和未解决问题。`
- Context: `请根据有证据的记录，提出我的当前项目和关注方向更新候选，不要把推断写成事实。`
- Quality: `请验证这批 PDKS 数据的结构、引用、时间、证据和权限问题，并给出修复建议。`
- Export: `请导出这批 PDKS 记录，保留原始来源引用、标准文件、哈希和外部引用清单。`
