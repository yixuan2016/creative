# Personal Context Engine

## Purpose
Personal Context helps an assistant understand a person over time. It is not a permanent psychological profile and must not be inferred casually.

## Context candidates
- current role or role assignment;
- active goals and responsibilities;
- current focus or project involvement;
- skills/capabilities demonstrated in work;
- preferences explicitly stated or repeatedly evidenced;
- working patterns that are relevant and non-sensitive;
- commitments and constraints that affect assistance.

## Verification states
- `self_declared`: user directly stated it;
- `confirmed`: user confirmed an agent proposal;
- `inferred`: agent-derived from evidence;
- `contested`: evidence conflicts or user disputes it;
- `expired`: no longer valid.

## Confidence and evidence
An inferred context must link to evidence. Use confidence conservatively. Do not infer sensitive traits or protected characteristics. A single occurrence usually supports an event, not a stable capability or preference.

## Temporal validity
Use validity intervals or review policies. Examples:
- "Currently leading Project A" should expire or be reviewed when the project ends.
- "Interested in topic B" may be a temporary focus rather than a permanent preference.
- "Has skill C" should be supported by demonstrated evidence or user confirmation.

## Update rules
- Prefer proposing a context update over silently overwriting.
- If new evidence conflicts with old context, mark contested or create a new version.
- Preserve old validity history when relevant.
- Respect user correction and retraction.
- Ask before retaining sensitive or high-impact context as a stable memory.
