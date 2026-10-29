# Synthetic one-way experiment — DRAFT

Continues existing sandbox/spacex-pilot and Draft PR #184. No Registry data or production files are changed. No real SpaceX API/account/affiliation. No REA installation or Clean Room independence claim: this is direct implementation of the supplied draft.

Node 24 with node:sqlite, standard library only. From this directory:

```sh
mkdir -p evidence
node demo.mjs evidence > evidence/demo.json
# Run from repository root, adapting absolute paths if checkout differs:
node --permission --allow-fs-read="$PWD/permission-probe.mjs" --allow-fs-read="$PWD/evidence/synthetic-input.json" permission-probe.mjs "$PWD/evidence/synthetic-input.json" > evidence/isolation.json
node --test-reporter=tap test.mjs > evidence/tests.tap 2>&1
node server.mjs
# On the same machine: http://127.0.0.1:4173 (NOT a deployed preview)
```

The permission command assumes current directory is this one, as does $PWD. Create an empty separate state directory, then run the stronger complete adapter probe:

```sh
mkdir -p /tmp/cfp-oneway-state
node --permission --allow-fs-read="$PWD" --allow-fs-read=/tmp/cfp-oneway-state --allow-fs-write=/tmp/cfp-oneway-state isolated-run.mjs "$PWD/evidence/synthetic-input.json" /tmp/cfp-oneway-state > evidence/isolated-run.json
```

Use a fresh state directory for a new run (otherwise accepted becomes IDEMPOTENT). isolated-run uses the input UTC as a simulated clock, explicitly to replay old fixtures. Normal demo uses current OS UTC. Synthetic fixture dates and IDs are not real event identities. Demo can safely be repeated: persistent duplicate conflicts are explicit, not silent overwrites. For a completely fresh demo choose a new evidence directory; tests currently inspect this directory's evidence.

Evidence is retained with source in this sandbox branch for review; no automated retention/deletion process. SQLite binary is generated, not included in source delivery; rerun demo to recreate it before tests. Tests read prior probe receipt, so run the probe command first; the standalone command really attempts a forbidden write. Child subprocess tests were replaced with explicit shell-run probes because this executor returned EPERM for nested spawnSync.

See SPEC.md for chosen semantics and E1–E5. REPORT.md records actual execution and missing evidence. ReviewSI/SecuritySI acceptance is PENDING; do not merge or deploy.
