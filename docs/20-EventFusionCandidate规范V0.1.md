# Event Fusion Candidate 规范 V0.1

## 1. 定义

Event Fusion Candidate 表示两个已有 Event 可能描述同一现实发生事项的待审查假设。Candidate 不是 Event，不具有事实效力。

## 2. 输入特征

- event_family / event_type；
- title / description 文本相似度；
- occurred_from 时间接近度；
- participant 提及重合度；
- project_id 上下文；
- 来源集合，用于排除完全相同的来源集合。

## 3. Alpha 评分

| 特征 | 权重 |
|---|---:|
| 文本相似度 | 0.38 |
| 时间接近度 | 0.28 |
| 参与者重合 | 0.14 |
| 事件族一致 | 0.10 |
| 事件类型一致 | 0.06 |
| 项目一致 | 0.04 |

缺失特征动态归一化。中文采用字符二元/三元组 Jaccard，英文和数字使用 token Jaccard。已知时间相距超过 14 天时不生成同一发生候选；没有时间信息时要求参与者重合提供独立锚点；文本重合低于 0.25 不进入候选。

默认阈值 0.62，范围 0.35—0.95。分数是排序分，不是概率。

## 4. 人工裁决

- pending：待审查；
- same_occurrence：确认同一发生；
- distinct：确认不同事件；
- rejected：驳回候选。

确认同一发生后只创建已批准的 EventRelation（same_occurrence_candidate）。当前不合并 Event ID、不选主事件、不迁移断言、不删除任何 Event。

## 5. 评测要求

建立正样本、难负样本、周期性会议、时间缺失、时区差异、否定/取消、同名参与者和转述样本。至少测量 Precision、Recall、F1、误合并率、漏合并率和每百候选人工审核时间。未经独立黄金集评测，不得启用自动合并。