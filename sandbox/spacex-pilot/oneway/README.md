# Synthetic one-way experiment — DRAFT

Continues existing sandbox/spacex-pilot and Draft PR #184. No Registry data or production files are changed. No real SpaceX API/account/affiliation. No REA installation or Clean Room independence claim: this is direct implementation of the supplied draft.

Node >= 22.13 with built-in `node:sqlite` (prints ExperimentalWarning on Node 22; executed on 22.23.4 and, originally, 24.19.0). Standard library only. From this directory:

```sh
# Self-contained tests: each test uses its own temp directory; committed evidence/ is never read as state or overwritten.
node --test-reporter=spec test.mjs

# Demo into a NEW output directory (kill switch: --enable is required, otherwise KILL_SWITCH_OFF before any file is created)
node demo.mjs /tmp/cfp-demo --enable

# Local read-only preview of that output (127.0.0.1 only, NOT a deployed preview; PORT defaults to 4173)
node server.mjs /tmp/cfp-demo

# Isolated adapter run under Node permissions with source snapshot pin (ported from PR #183)
PIN=$(sha256sum /tmp/cfp-demo/synthetic-input.json | cut -d' ' -f1); mkdir -p /tmp/cfp-oneway-state
node --permission --allow-fs-read="$PWD" --allow-fs-read=/tmp/cfp-demo/synthetic-input.json --allow-fs-read=/tmp/cfp-oneway-state --allow-fs-write=/tmp/cfp-oneway-state isolated-run.mjs /tmp/cfp-demo/synthetic-input.json /tmp/cfp-oneway-state "$PIN" --enable
```

Ported from PR #183 (that PR stays open until this transfer is reviewed): kill switch defaulting OFF and checked before the destination is created; reverse direction refused before any records transaction (only the refusal is audited); symlinked destination database rejected; source snapshot SHA-256 pin required before parsing. Files under `evidence/` (top level) are the 2026-10-29 historical receipts; `evidence/20261117-claude/` holds the 2026-11-17 rerun.

See SPEC.md for chosen semantics and E1–E5. REPORT.md records actual execution and missing evidence. ReviewSI/SecuritySI acceptance is PENDING; do not merge or deploy.
