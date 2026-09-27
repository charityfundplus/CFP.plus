-- CMP 267 controlled implementation only. No queue, dispatch, lease, provider/MCP or automation activation.
CREATE TABLE IF NOT EXISTS cmp_idempotency_registry (
  idempotency_record_id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL DEFAULT 'cmp.intake.register.v1',
  principal_id TEXT NOT NULL,
  command_type TEXT NOT NULL CHECK (command_type = 'INTAKE_REGISTER'),
  work_order_ref TEXT NOT NULL,
  idempotency_key TEXT NOT NULL,
  request_hash TEXT NOT NULL CHECK (request_hash GLOB 'sha256:[0-9a-f]*'),
  first_message_id TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  command_id TEXT,
  outcome_status TEXT NOT NULL CHECK (outcome_status IN ('IN_PROGRESS','ACCEPTED','REJECTED','QUARANTINED')),
  response_code INTEGER,
  response_hash TEXT,
  response_reference TEXT,
  created_at TEXT NOT NULL,
  completed_at TEXT,
  expires_at TEXT NOT NULL,
  authority_version INTEGER NOT NULL DEFAULT 1,
  UNIQUE(namespace, principal_id, command_type, work_order_ref, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_cmp_idempotency_correlation ON cmp_idempotency_registry(correlation_id);
