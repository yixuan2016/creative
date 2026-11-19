# PDKS 0.2.0 Integrated Skill — Quick Start

## What the user does
The user speaks or writes naturally, shares a transcript/document, or asks for a review. The agent handles structure in the background.

## What the agent does
1. Identify source and its reliability.
2. Extract only supported people, projects, events, assertions, knowledge, personal context, actions, and relations.
3. Preserve source/evidence references.
4. Classify events using the pinned PDKS taxonomy.
5. Apply conservative identity resolution and least-privilege governance.
6. Validate records.
7. Present a plain-language summary and disclose whether records were saved or only drafted.

## Never confuse
- Event = happened; Action = planned / promised.
- Source Asset = original carrier; Evidence Segment = a locatable fragment.
- Assertion = a claim; it is not automatically a fact.
- Reported = explicitly said; inferred = agent interpretation.
- Current context = time-qualified; not a permanent personality label.
- Similar names = not confirmed identity.
- Work-related = not automatically organization-shareable.

## Minimal user prompt
"请按照 PDKS 标准整理这段内容，自动识别事件、人物、项目、观点、知识和后续行动，保留来源证据，区分事实与推断，默认仅本人可见。"

## Output for ordinary users
- What was captured
- Important events / decisions / knowledge / actions
- One or two material uncertainties, if any
- Validation status
- Save status: drafted / saved with receipt / export prepared
