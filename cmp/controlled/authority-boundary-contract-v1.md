# CMP 267 Authority Boundary Contract v1

Status: approved for controlled implementation only.

## Single-authority rule

One record class has one writable authority. Projections, replicas, references, and controlled command interfaces are not authorities.

| Record class | Authority | Controlled implementation boundary |
|---|---|---|
| Work Identity / Stable ID | Existing controlled authority, unchanged | Operational identifiers never replace or mutate Stable ID. |
| Work Definition | Notion Control Plane | Core reads approved revision and stores immutable snapshot only. |
| Human Governance Decision | Notion Governance Decision Record | Core may validate a reference only; no protected action is enabled. |
| Execution State | Durable CMP Core | Only intake states RECEIVED, VALIDATED, DEDUPED, REJECTED, QUARANTINED are enabled. |
| Assignment / Lease | Durable CMP Core | Not implemented or activated in this branch. |
| Evidence Manifest / retained object | Evidence Store | Manifest and retained object controls support controlled test evidence only. |
| Audit Ledger | Durable CMP Core | Append-only audit schema and verifier support controlled test evidence only. |
| GitHub-native Technical Artifacts | GitHub | GitHub files, commits, PRs and native reviews remain GitHub authority. |

## Prohibitions

- No dual authority or uncontrolled dual write.
- No Stable ID create, issue, modify, bind, reuse, renumber, delete, replace, or inference.
- No Canonical Lock, Production Release, protected action, queue dispatch, assignment, lease, provider/MCP runtime, or production automation.
- Notion and GitHub are not authorities for CMP runtime state.

## Data flow

1. Authenticated controlled caller submits INTAKE_REGISTER.
2. Core reads an approved Notion Work Definition revision and creates an immutable snapshot.
3. One database transaction persists idempotency record, command, intake state, audit event and outbox event.
4. No publisher or consumer is activated. Outbox records are test-observable only.
5. Evidence and audit verification use retained controlled-test artifacts; PASS is prohibited without executed evidence, integrity verification, audit verification and independent review.

## Version and conflict rule

Authority rows carry monotonic versions. Projections may apply only expected authority versions and may never write back. Hash mismatch, source mismatch, unknown version or attempted authority override is rejected or quarantined and audited.
