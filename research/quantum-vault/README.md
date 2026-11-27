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

## Super Quantum Z sandbox

The fixed Bell experiment runs with Cirq, Qiskit and PennyLane on CPU. It
reports exact probabilities and the XX and ZZ expectations. OR-Tools CP-SAT
solves a separate classical integer model. The existing Vault schema validates
the simulator evidence; each evidence digest covers compact UTF-8 JSON for
`result` with sorted keys. The result payload travels with its digest.

From this directory, build and run the offline test image:

```sh
docker build -t super-quantum-z-test .
docker run --rm --network none super-quantum-z-test
```

For local development with Python 3.12, install `sandbox-requirements.txt`
into a virtual environment and run `python -m pytest -q`. For an optional API
test, supply a temporary `SUPER_QUANTUM_Z_SANDBOX_TOKEN` through the local
environment and run `python -m uvicorn super_quantum_z.api:app --host 127.0.0.1`.
Send a Bearer-authenticated POST to `/sandbox/experiment` with
`{"backend":"cirq"}`. The endpoint is disabled when the token is absent.

Related review: [CFP+ 678 Bell experiment](https://github.com/charityfundplus/CFP.plus/issues/233).
The sandbox runs use fixed synthetic experiments and generate new evidence.
