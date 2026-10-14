# CoreEngine assessment retention — Issue #130 / group 6

Source inspected: PR #124 head `11bb42464afebcd2962ca0ab94df0822853445c3`.
Scope: synthetic sandbox only. No paid services, deployment or real SI adapters.

## Gap and repair
Assessment-bearing CoreEngine checkpoints previously used schema 1, which older code accepts while ignoring the optional `learning.assessments` collection. A downgrade could therefore overwrite retained evidence with an empty collection.

New writers emit schema 2 when assessment packets exist. Legacy readers reject schema 2 before state restoration. Current readers retain compatibility with schema 1 checkpoints that contain no assessments; assessment packets from schema 1 readers are preserved and the next checkpoint uses schema 2. Restore also rejects missing/duplicate assessment keys or missing packet keys referenced by assessment audit events. Existing audit events are not migrated or rehashed.

## Operator rule
Before replacing runtime code, inspect the latest CoreEngine checkpoint schema. A schema 2 checkpoint requires an assessment-aware reader. Restore the matching code and checkpoint together; do not relabel schema 2 as schema 1, delete packets, or rewrite an audit chain to make downgrade work. `VersionUpgrade.rollback` remains a sandbox metadata rollback, not installation of historical executable code. It preserves packet evidence.

## Fresh focused verification
Command: `node drafts/si-office/tests/assessment-retention.test.mjs`
Result: 3/3 passed. Tests cover evidence loss refusal; legacy checkpoint compatibility; upgrade/rollback with review and original audit prefix; SQLite backup/restore preservation and session revocation. Only these new affected-path regressions were run. Results: `ASSESSMENT_RETENTION_RESULTS.txt`.

Limit: encrypted recipient backup envelope was not changed or rerun. No production approval, assessor authority, certification or new privileges arise from this evidence. Existing backup manifest compatibility describes the storage wrapper; CoreEngine schema 2 independently gates checkpoint readers.
