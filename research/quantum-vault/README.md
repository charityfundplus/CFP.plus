# CFP+ Quantum Research Vault v0.1

Status: RESEARCH ONLY / HUMAN REVIEW / PRODUCTION NO-GO.

One gateway: https://cfp.plus/69. This is a sixth *logical research store* under HUB 69, not a second gateway, canonical registry, or physical quantum computer.

## Safe development
- This branch is isolated from `main`; no deployment or production integration is authorized.
- Five existing adapters (Notion, GitHub, Google Drive, Site, Cloud) are contracts only, with no credentials or network calls.
- No writes to external systems; no changes to numeric IDs, DID, Parent or Canonical.
- Experiments must label backend as `simulator`, `quantum_inspired`, or `physical_qpu` and provide evidence for any claimed performance.
- Future integration requires least privilege, read-back, audit trail, provenance, drift detection, rollback and human approval.

See `schema.json` for record validation and `test_contract.py` for offline smoke checks.

Notion: https://app.notion.com/p/3f7caac9a557813590d7dddfe68ac6ea
Tracking: https://github.com/charityfundplus/CFP.plus/issues/118
