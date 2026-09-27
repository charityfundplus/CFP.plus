-- CMP 267 controlled implementation only. These tables do not activate any publisher, consumer, queue, dispatch, lease, provider/MCP call or automation.
CREATE TABLE IF NOT EXISTS cmp_work_definition_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  work_order_ref TEXT NOT NULL,
  source_authority TEXT NOT NULL CHECK (source_authority = 'notion_control_plane'),
  source_record_id TEXT NOT NULL,
  source_authority_version TEXT NOT NULL,
  source_url TEXT NOT NULL,
  retrieved_at TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  canonical_payload_json TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  captured_by_principal_id TEXT,
  captured_by_connector_id TEXT,
  authority_version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  UNIQUE(work_order_ref, source_record_id, source_authority_version, content_hash)
);

CREATE TABLE IF NOT EXISTS cmp_core_commands (
  command_id TEXT PRIMARY KEY,
  command_type TEXT NOT NULL CHECK (command_type = 'INTAKE_REGISTER'),
  command_status TEXT NOT NULL CHECK (command_status IN ('RECEIVED','VALIDATED','DEDUPED','REJECTED','QUARANTINED')),
  work_order_ref TEXT NOT NULL,
  work_definition_snapshot_id TEXT,
  source_message_id TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  idempotency_record_id TEXT NOT NULL,
  actor_principal_id TEXT NOT NULL,
  command_hash TEXT NOT NULL,
  authority_version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(work_definition_snapshot_id) REFERENCES cmp_work_definition_snapshots(snapshot_id),
  FOREIGN KEY(idempotency_record_id) REFERENCES cmp_idempotency_registry(idempotency_record_id)
);

CREATE TABLE IF NOT EXISTS cmp_runtime_intake_state (
  command_id TEXT PRIMARY KEY,
  current_state TEXT NOT NULL CHECK (current_state IN ('RECEIVED','VALIDATED','DEDUPED','REJECTED','QUARANTINED')),
  state_version INTEGER NOT NULL DEFAULT 1,
  last_event_id TEXT,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(command_id) REFERENCES cmp_core_commands(command_id)
);

CREATE TABLE IF NOT EXISTS cmp_audit_events (
  audit_event_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  actor_principal_id TEXT NOT NULL,
  actor_principal_type TEXT NOT NULL CHECK (actor_principal_type IN ('human','service','system')),
  auth_context_id TEXT NOT NULL,
  record_type TEXT NOT NULL,
  record_id TEXT NOT NULL,
  authority_name TEXT NOT NULL,
  action TEXT NOT NULL,
  correlation_id TEXT,
  causation_id TEXT,
  authority_version_before INTEGER,
  authority_version_after INTEGER,
  payload_hash TEXT NOT NULL,
  previous_event_hash TEXT NOT NULL,
  event_hash TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  schema_version TEXT NOT NULL DEFAULT 'cmp.audit_event.v1'
);

CREATE TABLE IF NOT EXISTS cmp_transactional_outbox (
  outbox_event_id TEXT PRIMARY KEY,
  aggregate_type TEXT NOT NULL CHECK (aggregate_type = 'CoreCommand'),
  aggregate_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('CMP_INTAKE_ACCEPTED','CMP_INTAKE_REJECTED','CMP_INTAKE_QUARANTINED')),
  event_version INTEGER NOT NULL DEFAULT 1,
  correlation_id TEXT NOT NULL,
  causation_id TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  payload_hash TEXT NOT NULL,
  occurred_at TEXT NOT NULL,
  available_at TEXT NOT NULL,
  publish_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (publish_status IN ('PENDING','TEST_OBSERVED','DISCARDED_BY_POLICY')),
  publish_attempt_count INTEGER NOT NULL DEFAULT 0,
  authority_version INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY(aggregate_id) REFERENCES cmp_core_commands(command_id)
);

CREATE INDEX IF NOT EXISTS idx_cmp_outbox_pending ON cmp_transactional_outbox(publish_status, available_at);
CREATE INDEX IF NOT EXISTS idx_cmp_audit_record ON cmp_audit_events(record_type, record_id);
