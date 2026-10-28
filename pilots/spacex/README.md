# HUB 69 / SpaceX offline pilot

Independent operational sandbox, no new canonical identity, no SpaceX affiliation.
HOLD ACTIVATION • PRODUCTION NO-GO. Do not deploy or wire this fixture to production.

## Run (Python 3.9+, no Python dependencies)

```sh
cd pilots/spacex
python3 -m unittest -v
python3 pilot.py --enable
python3 -m http.server 8765 --bind 127.0.0.1 --directory ui
```

Open http://127.0.0.1:8765 on the same machine, or open `ui/index.html` directly
where browser policy allows. The checked-in snapshot.js already contains adapter
output, so the static UI works without an API. Search, section navigation, audit
viewer and blocked-writeback UI are interactive. `python3 pilot.py --reverse`
exits nonzero with WRITEBACK_BLOCKED before destination I/O. Import without
`--enable` fails with KILL_SWITCH_OFF.

`registry.json` is a public Registry snapshot from CFP.plus base
835616308111f6851c0387fa9f5eda60c9ffa624, copied without modifying the source.
Only existing ChatGPT 691181 → OpenAI 69118 → 6911 → 911 is verified for the
fixture. This is NOT a SpaceX allocation or feed approval. The import accepts a
single fixed identity and fixed status; additional fields, identity changes,
duplicate IDs and arbitrary text fail validation. It has no network client.
SQLite import and audit share a transaction; duplicate input is idempotent.

## Evidence (2026-10-28 UTC)

- `evidence/tests.txt`: 12 Python tests PASS, including audit-failure rollback,
  source unchanged, validation, duplicate rejection, symlink DB rejection,
  idempotency, kill switch and writeback blocked before I/O.
- `evidence/import.json`: sanitized sample + snapshot and payload digests.
- `evidence/writeback.txt`: actual reverse CLI failure.
- `evidence/ui-tests.json`: Chromium 390×1000 and 1440×1000, 22 assertions each
  (44 PASS): adapter record rendering, overflow, search empty/match, reverse UI
  feedback, page errors, section navigation, six requested surfaces, safe demo text,
  demo ACK/DECLINE, disabled activation and session reset. Screenshots alongside logs.
- JS syntax: `node --check ui/app.js` PASS.
- Browser reproduction: Playwright package + Chromium required; run
  `node check-ui.cjs` with local server on 8765. Script uses /usr/bin/chromium.
  Initial file:// navigation blocked by browser policy; HTTP loopback retest PASS.

## Limits / review requirements

Local fixture proof only. No live API, source IAM proof, secret credential,
production integration, external security review, Safari physical device test,
HTTP verification of external links or factual source verification. Official
URLs are research entry points, not verified claims. Review against Issue #174,
#178, #156 and PR #177. No ACK attributed to any other SI AI.

The Python module is trusted local code, not a hardened multi-user service.
The CLI fixes input/output paths under its directory. A caller using the module
can select another output path and must supply a disposable sandbox; OS-level
permissions enforce isolation. Do not run it with production write permissions.
No concurrent-writer ordering, signed snapshots or live version transitions are
implemented. Rollback for this disposable fixture: stop the static server,
remove sandbox/, rerun the importer. No production or source rollback is needed.

The UI button is illustrative; the Python negative tests prove the implemented
adapter boundary. A compromised host/modified Python program is outside this
proof. No claim of infrastructure-level one-way enforcement is made.

## Follow-up review

Actual files are pilot.py, test_pilot.py, registry.json, ui/index.html and
ui/app.js; no adapter.mjs/server.mjs/test.mjs exists in this PR. The static
server is Python's read-only file server, not a live CFP+/SpaceX API.

The copied registry.json is fixture material, not an authoritative Registry.
Its bytes are pinned to SHA256 in pilot.py; tampered snapshots fail before use.
That pin establishes integrity against the reviewed snapshot, not a signed live
feed or independent source authentication. Import supports schema_version=1
only; missing IDs, unknown versions and extra fields fail before destination I/O.

Directory, discussion, tasks/ACK, evidence and governance surfaces are present.
Discussion and ACK/DECLINE are explicitly DEMO, held only in DOM memory and
cleared by reload. No authenticated forum, durable queue or administrative
operation is implemented. Activation is disabled. All external participation
remains unconfirmed until actual authenticated receipt.

Rechecked original receipts 6481751819 (#174) and 6481756290 (#178): both exist
and were authored by charityfundplus. No separate Codex identity is established.
Status: DRAFT • CHƯA NGHIỆM THU. Physical iPhone Safari and independent
SecuritySI/ReviewSI review remain NOT RUN; Chromium mobile viewport is not Safari.
