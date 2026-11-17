# Rerun and changes — Claude Code — 2026-11-17 UTC

Scope: PR #184 continuation per Issue #174 decision (PR #184 = main integration; PR #183 kept open until transfer verified). No Registry/ID/DID/Parent/Canonical change. No merge, deploy, DNS/IAM or production change. SpaceX is a research subject, not an official CFP+ partner.

Environment: Node v22.23.4, Playwright 1.63.0 with bundled Chromium, Linux container, 127.0.0.1 only.

## Changes
1. Tests self-contained: every test uses mkdtemp; `demo.mjs` exports `build(dir)`; `server.mjs` exports `makeHandler(dir)`. Final test asserts committed `evidence/` digests unchanged. Previously a clean checkout failed test 8 and created an empty `evidence/sandbox.sqlite`; running `demo.mjs` overwrote committed evidence and broke E3.
2. Ported from PR #183: kill switch (default OFF, before destination creation), reverse refused before any records transaction, symlink destination rejection, source snapshot SHA-256 pin.
3. E3 permission probe now runs as a fresh subprocess on a temp source (skips as BLOCKED only if spawn returns EPERM). New HTTP end-to-end test on an ephemeral 127.0.0.1 port.
4. HUB 69 (`69/index.html`): "Nghiên Cứu SpaceX" section — states not an official partner and no official ID; links spacex.com, Issue #174, PR #184 only. No numeric ID link.

## Results (this directory)
- `tests.tap`: 15 PASS / 0 FAIL / 0 SKIPPED (E1–E5, E3a/E3b, #183 ports, UI export equality, handler, HTTP E2E, evidence unchanged).
- `isolated-run.json`: IMPORTED; reverse WRITEBACK_BLOCKED; direct source write ERR_ACCESS_DENIED; pinned = before = after source SHA-256. Negative runs: wrong pin → SOURCE_SNAPSHOT_UNVERIFIED; missing `--enable` → KILL_SWITCH_OFF with state directory left empty.
- `ui-check.json` + PNGs: Chromium, iPhone 13 emulation (390 px) and 1440 px: HUB 69 section and sandbox preview HTTP 200, no horizontal overflow, no page errors, disclaimers present.
- Repository regression: `run_ctttc_v066_tests.py` 204 PASS / 0 FAIL.

## Still BLOCKED / PENDING
Real iPhone Safari (only Chromium device emulation here); public preview URL; independent ReviewSI/SecuritySI review; official sources for ownership figures; Node permission model is not OS/IAM isolation; audit triggers are not a tamper-proof ledger.

SANDBOX PRACTICE GO • PRODUCTION NO-GO.
