# CFP+ • Independent Repository Survival Policy v0.1

Status: HUMAN DECISION RECORDED • RESEARCH DESIGN • NOT PRODUCTION VERIFIED

## Core rule
**If any source repository is unavailable or irrecoverably lost, every other repository must remain independently available for its locally supported, previously ingested data and functions.** A failure must not cascade via synchronous calls, shared write privileges, shared storage, or a single runtime dependency.

## One-way flow
Authoritative source → approved outbound immutable export → each independently operated archive/research repository. **No reverse sync, no automated write-back, no source repair from archives.** Any restoration of a source requires separate, explicit Human Governance approval and controlled recovery procedure; it is not normal synchronization.

## Engineering controls and evidence required
1. **Independent storage:** separate failure domains and recoverable snapshots; no remote mount that becomes unusable on source failure.
2. **Independent runtime:** local read-only mode when upstream APIs, identity provider, DNS, or network are unavailable; define what remains available and what is degraded.
3. **Independent authorization:** test emergency access and token expiration; no uncontrolled shared master credential.
4. **Independent metadata:** local copy of provenance, schema, checksums, version, relationships and authorization classification; no dependence on live parent lookup to read snapshots.
5. **Isolation:** bounded queues, circuit breakers, retry limits, immutable ingest; failed upstream never triggers write-back.
6. **Recovery:** test simulated outage of each source, restore from authorized copies into a *separate sandbox*, validate byte hashes, record counts, lineage, permissions, and elapsed RTO / data-loss RPO.
7. **Governance:** archive copies may contain older data. Preserve timestamp and `last_verified_source_version`; do not present stale data as current or grant archives canonical authority.
8. **Threat model:** common-mode risks remain (same cloud region, shared identity, compromised encryption keys, DNS, legal/provider outage); independently validate each.

## Acceptance criteria
- An isolated repository remains readable with its own stored snapshot after source outage.
- No source-write-capable credentials, reverse callbacks or network path from archive are available.
- Failure-injection evidence includes independent read, negative write tests, audit trail, recovery results and residual limitations.
- No claim of zero data loss, full five-way backup equivalence or production readiness without evidence.

HUB 69 remains the **single logical gateway**, but its implementation must be resilient rather than a single physical point of failure.

Tracking: https://github.com/charityfundplus/CFP.plus/issues/118
