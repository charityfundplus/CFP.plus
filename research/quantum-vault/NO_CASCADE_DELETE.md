# CFP+ • No Cascade Delete / No Reverse Sync v0.1

Status: Human design decision; enforcement NOT VERIFIED.

## Non-negotiable policy
- Authoritative source → approved immutable versioned snapshots → independently isolated archive(s).
- **No automatic bidirectional synchronization** and no reverse write path from archives to source.
- **No propagation of delete, overwrite, ransomware encryption, mass edits or tombstones** from any source to preserved snapshots. Treat deletion events as quarantined metadata, never as destructive archive operations.
- Archive ingestion must be append-only; content-addressed checksums and immutable retention windows enforced independently of source admin privileges.
- Archive compromise must not affect source or other archives. No shared write credential, writable shared volume or unrestricted replication token.
- Keep at least one logically offline / air-gapped or otherwise separately secured immutable recovery copy where feasible and authorized; test restore.
- Retention, privacy rights and legal deletion requirements still apply: authorized deletion must use a separate documented Human Governance procedure, not automatic sync.

## Tests required before production
1. Simulate source deletion, bulk deletion, corruption and ransomware-like overwrite on synthetic data; verify prior archive versions persist.
2. Simulate archive deletion/compromise; verify source and peers unaffected.
3. Verify source and archive credentials cannot write into each other's protected domains.
4. Test recovery from a known-good snapshot in an isolated environment, including hashes, counts, provenance, permissions, RPO and RTO.
5. Confirm the single HUB 69 logical gateway remains available or provides controlled degraded access when any one repository fails.

No production backup or resilience claims until failure-injection evidence and independent review exist.

Issue: https://github.com/charityfundplus/CFP.plus/issues/118
