# Integration receipt — 2026-11-17 UTC

PR #184 is the integration candidate; #183 remains open pending transfer acceptance. Supersedes the section-ownership instruction in CONTINUATION-20261117.md: HUB 69 introduction is now also carried in #184 for eventual integration. Neither branch is merged or publicly deployed.

Changes: self-contained one-way tests with unique temporary fixtures/SQLite and cleanup; reusable demo generation with injected clock; injectable read-only evidence handler; real loopback HTTP test; #183 snapshot SHA-256 pin reused for verified Registry importer construction and preview serving; existing no-writeback/whitelist/approval checks retained; HUB 69 introduction copied from #183 without allocating any ID. The Registry projection and synthetic persistent status adapter remain distinct experiments; no production feed integration is claimed.

## Actual validation
- Node v24.22.1: 20/20 tests PASS, 0 fail, 0 skipped (10 one-way + 10 Registry/preview). tests.tap is the actual run.
- Command from repository root: PILOT_SOCKET_TEST=1 node --test --test-isolation=none --test-reporter=tap sandbox/spacex-pilot/test.mjs sandbox/spacex-pilot/oneway/test.mjs
- Tests run without generating historical evidence first. E3 now proves fresh adapter no-writeback, not a previously saved permission receipt. A separate fresh Node filesystem permission probe returned ERR_ACCESS_DENIED / FileSystemWrite (isolation.json).
- Chromium /usr/bin/chromium: 33 assertions PASS across 375, 390, 1440 px, pilot and HUB 69. Search, reverse-demo labelling, safe text, session reset, introduction links, no horizontal overflow or JS errors. check-ui.cjs is reproducible; ui-results.json records results. Six screenshots were produced under /tmp/cfp-ui-T3JbmP locally; binaries are not included in this GitHub receipt.
- Initial default sandbox blocked HTTP listen (EPERM); repeat with permitted network capability passed. Standard child-process test runner initially failed; --test-isolation=none passed without bypassing tests. Earlier failed attempts do not count as PASS.
- Existing historical evidence directories and registry.json are not modified by this change. New receipts are in evidence-20261117 only. manifest.json pins reviewed source bytes, excluding this report and historical files.

## Remaining gates
Physical iPhone Safari NOT RUN. Claude / ReviewSI / SecuritySI independent acceptance PENDING; no ACK is attributed to them. Official external source fact/link verification and approved public sandbox hosting are still pending. No public URL or production deployment, DNS/IAM/Registry/ID/Parent/Canonical change. The snapshot hash proves reviewed fixture integrity, not signed live-source authentication. Node permissions are a local defense, not proof of infrastructure isolation. Keep Draft and production NO-GO.
