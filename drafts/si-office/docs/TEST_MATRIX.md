# 12-module test matrix

Execution: `npm test` → 18 tests / 18 passed. Actual HTTP handler invoked in process; socket transport/current browser not verified.

| Module | Functional input/output evidence | Access / audit | Verdict |
|---|---|---|---|
| 01 • Identity & Lineage | Registry lineage, identity evidence, Country/Developer proposal, null identity, duplicates | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 02 • Introduction & Capabilities | Scoped draft record + evidence | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 03 • Products | Research maturity enum; rejects commercial maturity; office/HSTDN reference validation | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 04 • Services | Required service scope; draft only | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 05 • Marketing | Draft → reviewer; claims not auto-verified | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 06 • CRM | Synthetic-only record; real PII detection absent | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 07 • Commerce | Draft quote record; payment route 403 | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 08 • HSTDN & Partners | Member validation; typed relation; legal claim NOT VERIFIED | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 09 • Office & Tasks | Submit → review requires evidence and reviewer | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 10 • API/MCP | Ten read-synthetic adapters; connected=false/externalRequests=0 | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 11 • Governance/Security | Host/Origin/session/identity denial; audit-chain recomputation | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |
| 12 • Reports/Evidence/KPI | JSON export and synthetic counts; no real impact claim | Each module: viewer submit denied; editor review denied; reviewer review logged | VERIFIED handler / PARTIAL business depth |

Current browser: BLOCKED (sandbox EPERM). Runnable expanded test suite: tests/browser.mjs. Baseline browser evidence belongs to initial draft only. VI/EN dictionaries/contracts are implemented and syntactically checked; interactive localization coverage awaits current browser test.
No test result grants Governance approval, identity verification, quantum capability or legal partnership.
