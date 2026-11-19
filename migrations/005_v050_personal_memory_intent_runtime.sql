-- V0.5.0 Alpha additive migration reference.
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

CREATE TABLE IF NOT EXISTS memory_items (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
 memory_type TEXT NOT NULL CHECK(memory_type IN ('profile_fact','preference','principle','decision','lesson','experience','relationship','skill','commitment')),
 title TEXT NOT NULL, content TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'proposed' CHECK(status IN ('proposed','active','needs_review','superseded','retracted','rejected')),
 epistemic_status TEXT NOT NULL DEFAULT 'inferred' CHECK(epistemic_status IN ('observed','inferred','confirmed','disputed','retracted')),
 confidence REAL NOT NULL DEFAULT 0.6 CHECK(confidence>=0 AND confidence<=1),
 sensitivity TEXT NOT NULL DEFAULT 'P1' CHECK(sensitivity IN ('P0','P1','P2','P3')),
 owner_scope TEXT NOT NULL DEFAULT 'personal' CHECK(owner_scope='personal'),
 purpose_scopes_json TEXT NOT NULL DEFAULT '["personal_knowledge","personal_assistant"]',
 valid_from TEXT, valid_to TEXT, expires_at TEXT,
 origin_kind TEXT NOT NULL CHECK(origin_kind IN ('manual','reflection')),
 revision INTEGER NOT NULL DEFAULT 1, created_by TEXT NOT NULL, updated_by TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memory_items_lookup ON memory_items(workspace_id,status,memory_type,updated_at DESC);

CREATE TABLE IF NOT EXISTS memory_supports (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
 memory_id TEXT NOT NULL REFERENCES memory_items(id) ON DELETE CASCADE,
 event_id TEXT, evidence_id TEXT, support_role TEXT NOT NULL DEFAULT 'derived_from',
 support_status TEXT NOT NULL DEFAULT 'active' CHECK(support_status IN ('active','invalidated')),
 created_at TEXT NOT NULL, invalidated_at TEXT, invalidation_reason TEXT,
 UNIQUE(memory_id,event_id,evidence_id,support_role)
);
CREATE INDEX IF NOT EXISTS idx_memory_support_event ON memory_supports(workspace_id,event_id,support_status);
CREATE INDEX IF NOT EXISTS idx_memory_support_evidence ON memory_supports(workspace_id,evidence_id,support_status);

CREATE TABLE IF NOT EXISTS memory_revisions (
 id TEXT PRIMARY KEY, memory_id TEXT NOT NULL REFERENCES memory_items(id) ON DELETE CASCADE,
 revision_no INTEGER NOT NULL, snapshot_json TEXT NOT NULL, change_reason TEXT NOT NULL,
 changed_by TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(memory_id,revision_no)
);

CREATE TABLE IF NOT EXISTS intent_items (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
 intent_type TEXT NOT NULL CHECK(intent_type IN ('goal','commitment','plan','milestone','task','aspiration')),
 title TEXT NOT NULL, description TEXT,
 status TEXT NOT NULL DEFAULT 'proposed' CHECK(status IN ('proposed','active','blocked','on_hold','completed','cancelled','superseded')),
 priority INTEGER NOT NULL DEFAULT 3 CHECK(priority BETWEEN 1 AND 5),
 project_id TEXT, parent_intent_id TEXT REFERENCES intent_items(id) ON DELETE SET NULL,
 start_at TEXT, due_at TEXT, next_action TEXT,
 sensitivity TEXT NOT NULL DEFAULT 'P1' CHECK(sensitivity IN ('P0','P1','P2','P3')),
 owner_scope TEXT NOT NULL DEFAULT 'personal' CHECK(owner_scope='personal'),
 purpose_scopes_json TEXT NOT NULL DEFAULT '["personal_assistant","task_support"]',
 review_required INTEGER NOT NULL DEFAULT 0 CHECK(review_required IN (0,1)),
 origin_kind TEXT NOT NULL DEFAULT 'manual' CHECK(origin_kind IN ('manual','reflection')),
 created_by TEXT NOT NULL, updated_by TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_intent_items_state ON intent_items(workspace_id,status,priority,due_at);

CREATE TABLE IF NOT EXISTS intent_event_links (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
 intent_id TEXT NOT NULL REFERENCES intent_items(id) ON DELETE CASCADE,
 event_id TEXT NOT NULL,
 relation_type TEXT NOT NULL CHECK(relation_type IN ('derived_from','motivated_by','updates','fulfills','blocks','evidences_progress')),
 link_status TEXT NOT NULL DEFAULT 'active' CHECK(link_status IN ('active','invalidated')),
 created_at TEXT NOT NULL, invalidated_at TEXT, invalidation_reason TEXT,
 UNIQUE(intent_id,event_id,relation_type)
);
CREATE INDEX IF NOT EXISTS idx_intent_event_links_event ON intent_event_links(workspace_id,event_id,link_status);

CREATE TABLE IF NOT EXISTS intent_transitions (
 id TEXT PRIMARY KEY, intent_id TEXT NOT NULL REFERENCES intent_items(id) ON DELETE CASCADE,
 from_status TEXT NOT NULL, to_status TEXT NOT NULL, action TEXT NOT NULL,
 reason TEXT NOT NULL, actor_id TEXT NOT NULL, created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reflection_runs (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL, window_start TEXT, window_end TEXT,
 status TEXT NOT NULL CHECK(status IN ('previewed','materialized','failed')),
 input_event_refs_json TEXT NOT NULL, output_memory_ids_json TEXT NOT NULL DEFAULT '[]',
 output_intent_ids_json TEXT NOT NULL DEFAULT '[]', created_by TEXT NOT NULL,
 created_at TEXT NOT NULL, completed_at TEXT, ruleset_version TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_reflection_runs_workspace ON reflection_runs(workspace_id,created_at DESC);

INSERT OR IGNORE INTO schema_migrations(version,applied_at,description)
VALUES('eil_personal_runtime_001',datetime('now'),'Personal memory, intent, reflection and state runtime');
COMMIT;