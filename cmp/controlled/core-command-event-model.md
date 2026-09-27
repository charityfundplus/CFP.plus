# CMP 267 Core Command/Event Model — Controlled Scope

## Enabled command

`INTAKE_REGISTER` is the only accepted command. It registers a controlled intake after authenticated validation and immutable Notion Work Definition snapshot capture.

## Enabled states

`RECEIVED → VALIDATED → DEDUPED | REJECTED | QUARANTINED`

No transition to queued, leased, dispatched, acknowledged, running, retry, review, governance, or closed is available in this implementation.

## Required atomic write set

For an accepted non-duplicate intake, one transaction writes:

1. Idempotency registry row.
2. Work Definition Snapshot.
3. Core command.
4. Runtime intake state.
5. Append-only audit event(s).
6. Transactional outbox event.

Any failure rolls back the entire write set and must not return acceptance.

## Event names

- CMP_INTAKE_RECEIVED
- CMP_WORK_DEFINITION_SNAPSHOTTED
- CMP_INTAKE_VALIDATED
- CMP_INTAKE_DEDUPED
- CMP_INTAKE_REJECTED
- CMP_INTAKE_QUARANTINED
- CMP_OUTBOX_RECORDED
- CMP_INTAKE_TEST_EVIDENCE_CAPTURED

## Versioning and integrity

Every mutable authority row uses optimistic `authority_version` or `state_version`. Every event carries correlation and causation references plus payload hash. Projections are forbidden from writing runtime state. A duplicate with same idempotency scope/key/request hash replays the original result; same key with a different request hash is rejected and audited.

## Explicit exclusions

No queue publisher/consumer, assignment, lease, provider/MCP call, dispatch, retry executor, automated review, governance action, Stable ID action, Canonical Lock or Production Release is implemented or activated.
