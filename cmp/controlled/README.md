# CMP 267 Controlled Implementation

This directory contains the authorized controlled-implementation artifacts for:

- T-WO-267-01 — Durable Intake and Idempotency Foundation
- T-WO-267-06 — Evidence, Independent Review and Tamper-Evident Audit

## Status

Implementation artifacts only. No acceptance test has been executed by this commit. No `VERIFIED_PASS` claim is permitted until executed output is retained, registered in an immutable Evidence Manifest, integrity verified, audit verified and independently reviewed.

## Explicitly disabled / absent

- Queue dispatch, scaling, consumers and scheduling
- Assignment and lease runtime
- Provider/MCP runtime calls and callbacks
- Production automation and production projections
- Stable ID actions
- Canonical Lock
- Production Release
- T-WO-267-02/03/04/05/07/08/09

## Run-safe utility commands

```bash
python3 tests/controlled_test_harness.py --list
python3 tests/controlled_test_harness.py --status-template
python3 tools/evidence_verifier.py --manifest <manifest.json> --object <retained-object>
python3 tools/audit_verifier.py --events <ordered-events.json>
```

Utilities are verifiers/harness scaffolds. Their presence or successful execution does not establish a CMP PASS result.
