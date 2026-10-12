# CFP+ • ONE-WAY DATA FLOW POLICY v0.1

Status: HUMAN DECISION RECORDED • DESIGN ONLY • PRODUCTION NO-GO

## Mandatory direction
**Authoritative CFP+ source repositories → approved outbound export → isolated Quantum Research Vault.**

The Quantum Vault is a **read-only consumer of approved snapshots**, not a system of record. **No reverse data path**, write-back, callback that mutates source, bidirectional sync, reverse replication, automatic merge, or automatic conflict resolution against source systems.

## Enforce by architecture, not documentation alone
1. Source owners select datasets, classifications, scope, and export cadence. Outbound exports are allowlisted, versioned, integrity-checked, and privacy-screened.
2. Export gateway has read-only access to authorized source data. Quantum Vault credentials must not grant source-system writes or admin access.
3. Prefer push of signed/checksummed immutable snapshots from an approved export zone to a separate ingest zone; avoid a persistent network path from Quantum Vault back to source.
4. Ingestion is append-only or isolated; quarantine invalid schemas, hashes, missing provenance and duplicated snapshots. No mutation of canonical IDs, DID, Parent, routes or source records.
5. Derived analyses and suggestions remain inside the research zone. Human Governance may manually evaluate findings through a separate, explicit proposal process; no automated return channel.
6. Source failure must not cause quantum research to write to or repair source systems. Quantum failure must not block source operations.
7. Test egress/network rules, credentials, IAM, webhook configurations, API tokens, CI secrets, shared mounts, service accounts, and callback paths to establish absence of reverse-write capabilities.
8. Verify rollback, kill switch, logs, export completeness, restore drills and source read-back before any production connection.

## Explicit caveat
One-way **logical policy** is not proof of physically unidirectional connectivity or a data diode. Real enforcement requires infrastructure evidence and independent tests. Existing five repositories are not assumed to be synchronized or interchangeable backups.

Tracking: https://github.com/charityfundplus/CFP.plus/issues/118
