# CFP+ Issue #156 • Review handoff

**HOLD ACTIVATION • PRODUCTION NO-GO**

- `openapi.json`: OpenAPI 3.1, existing Core list/detail and disabled public design.
- `API_CONTRACT.md`: integration, security review, adapters, rollback and blockers.
- `REGISTRY_MAPPING.md`: original Registry comparison and conflicts.
- `adapters.json`: five disabled read-only connection designs.
- `publication_policy.py`: offline policy reference; no signature verifier or endpoint.
- `test-results.txt`, `manifest.json`: reproducible offline results/source hashes.
- `source-observations.json`: pinned read-only evidence, not a runtime Registry.

Run from this directory with Python 3 and requirements-test.txt installed:

```sh
python -m unittest -v test_contract test_sources
```

25 offline checks PASS. No runtime HTTP, live adapter, device test, formal OpenAPI
semantic lint or independent Gemini/Codex 2 acceptance claimed. All sample approval
receipts use example.invalid and are synthetic, never Governance authority.
