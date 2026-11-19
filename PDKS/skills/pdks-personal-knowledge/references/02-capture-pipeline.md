# Capture Pipeline

## Purpose
Capture is not just transcription. It converts available source material into source assets, evidence segments, events, assertions, knowledge candidates, actions, and context candidates.

## Pipeline
1. **Acquire** — identify what material is actually available and whether user authorization exists.
2. **Preserve** — retain original file or source locator; compute SHA-256 if file bytes are accessible.
3. **Segment** — split long content into locatable chunks while retaining offsets, timestamps, page/paragraph/message IDs.
4. **Attribute** — distinguish direct speaker, quoted speaker, author, uploader, and AI processor.
5. **Extract** — identify candidate records.
6. **Classify** — assign domains and event taxonomy codes.
7. **Resolve** — match people/projects only with sufficient evidence.
8. **Link** — connect events, evidence, entities, assertions, actions and knowledge.
9. **Govern** — apply sensitivity, access scope, consent and retention.
10. **Validate** — run schema and semantic checks.
11. **Present** — summarize simply and ask only critical questions.
12. **Persist** — write to an authorized destination, or clearly mark as draft/export-only.

## Source handling rules
- Audio: retain audio source, transcript version, speaker diarization quality, and time offsets if available.
- Chat: retain platform, conversation/thread ID if available, message IDs, sender and message timestamps.
- Documents: retain filename, MIME type, source locator, content hash, page/heading/paragraph locators where possible.
- Email: retain message/thread identifiers, sender/recipient roles and sent/received time; avoid exposing unnecessary recipients.
- Web: retain URL, retrieval time, title, relevant excerpt and access restrictions.
- Manual note: mark source type as user-provided text / manual note; do not invent an external file.

## Segmenting long sources
Use semantic chunks that preserve context. Avoid chunks so small that speaker/meaning is lost. Every evidence segment should point to its parent source and a locator. If exact offsets are unavailable, use the best available page, message, heading or paragraph locator and mark precision.

## Audio speaker confidence
Do not bind an unknown speaker to a real person based only on voice similarity or context guess. Use speaker candidates and request confirmation only when identity matters.
