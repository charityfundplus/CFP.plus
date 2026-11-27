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

## Shared queue • sandbox only

The legacy experiment endpoint remains available in standalone mode. Setting
`SUPER_QUANTUM_Z_QUEUE_CONFIG` switches HTTP execution to the fenced CMP queue.
The private JSON configuration contains `database` (an absolute path) and
`principals` (an object keyed by string ID). Each principal has a unique token
of at least 32 characters and a list of permitted `backends`. Provision the
file with restrictive host permissions and pass only each principal's own
token to that principal. Use synthetic IDs and inputs during sandbox exercises.

- Submit to `POST /sandbox/cmp/{id}/work-orders` with a Bearer token and
  `{"work_order_id":"CMP-001","experiment":{"backend":"ortools"}}`.
- Read the same ID's `GET /sandbox/cmp/{id}/evidence/{job}`. The record contains
  the job state, attempt count, result, SHA-256 of the compact sorted JSON
  result, and ordered audit events. Repeating a submit with the same order ID
  and experiment returns the original job, including after an API restart.
- Install `mcp-requirements.txt` for MCP stdio. Use
  `python -m super_quantum_z.mcp_server` with
  `SUPER_QUANTUM_Z_MCP_ID` and `SUPER_QUANTUM_Z_MCP_TOKEN`. Its two tools call
  the loopback CMP API on port 8000.
- Run `python -m super_quantum_z.worker /state/queue.db worker` on the same host.
  The worker runs the scheduler on each claim. A claim has a ten-second lease,
  refreshed while the isolated calculation runs. Work orders expire after two
  minutes. Each attempt can run for up to 30 seconds, with up to three attempts
  and retry delays of 2 and 4 seconds. Two valid leases may run concurrently.
- An operator with access to the database can use the worker CLI arguments
  `stop`, `resume`, and `status` in place of `worker`. Stop cancels pending and
  running jobs and persists across restart. An isolated worker checks the stop
  on its next heartbeat. Once resumed, cancelled work requires a fresh order
  ID. Result writes are fenced by the claim session.

`compose.sandbox.yml` is a Linux host candidate with a persistent local disk,
a loopback API, an offline worker, restart limits, and CPU, RAM, PID, and log
limits. The host administrator supplies `CFP_SANDBOX_STATE` owned by UID 65532
and `CFP_SANDBOX_CONFIG` readable by that UID. Set the configuration's database
path to `/state/queue.db`. Use a local filesystem supporting SQLite locking.
The built-in health check probes the queue and the worker CLI reports state
counts and Emergency Stop. Container process restart handles process exits.
Operational monitoring can alert on container health, failed/expired jobs,
disk free space and provider charges. The queue keeps up to 1,000 work orders
including terminal orders. Archive the stopped database using SQLite backup,
verify the backup, and start a new sandbox queue when that limit is reached.
Preserve the old queue when historical evidence and idempotency keys are needed.

Review a candidate upgrade in the Draft PR with the offline, CPU and MCP
recovery jobs. Back up the database under Emergency Stop before a sandbox
upgrade. Verify readback and resume deliberately. Retain the previous image
and backup for rollback. This profile covers a single SQLite host and requires
a provisioned cloud host to verify VM recovery, hours of sustained operation,
billing alerts, and backup restore. No cloud services are created by the profile.

## Read-only coverage

From this directory run
`python -m super_quantum_z.coverage <registry-commit> <pr-253-commit>`.
The output retains leading zeroes, maps the ten chapters to the four numeric
groups, and records V and D in the fifth group. It merges roles by string ID,
flags overlaps for review and reports source matches and unbound planning
slots. It creates no Registry entries or runtime grants. The CMP configuration
file determines which vetted IDs can access a sandbox deployment.
