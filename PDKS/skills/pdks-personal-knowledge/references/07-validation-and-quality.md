# Validation and Quality

## Validation layers

### 1. Structural
- JSON Schema Draft 2020-12.
- Required fields, types, formats, enums and payload shapes.
- Unique object IDs.

### 2. Cross-record
- References resolve inside the bundle or are explicitly external/unresolved.
- No duplicate IDs.
- Event end is not earlier than event start.
- Evidence locator ranges are valid.
- Event taxonomy code exists in the pinned taxonomy.
- Inferred Personal Context has evidence.
- Source/evidence chains are preserved.

### 3. Semantic
- Planned work is not mislabeled as completed Event.
- Assertions are attributed to the correct speaker.
- AI inferences are not marked as direct reports.
- Similar names are not auto-merged.
- Access scope has not been widened.
- Knowledge Assets carry applicability and limitations.
- Expired context is not represented as current.

### 4. Migration
- All source files are represented in manifest.
- SHA-256 hashes match.
- IDs and references are preserved or mapped.
- Unsupported fields and lossy conversions are reported.
- Permissions are not widened.

## Quality labels
Use plain statuses:
- `valid`: machine checks passed;
- `valid_with_warnings`: structural checks passed, but some unresolved references or semantic cautions remain;
- `invalid`: one or more required checks failed;
- `not_machine_checked`: no validator was available.

Do not report an accuracy percentage unless a defined evaluation dataset and metric exist.
