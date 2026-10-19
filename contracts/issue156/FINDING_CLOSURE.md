# PR157 • finding remediation / closure ledger

Reviewed baseline SHA: `652dd252cf37a3a4991f8bc9abf52b99abce68d0`.
Correction SHA: the exact commit containing this file and manifest; the GitHub
PR157 remediation comment pins the full published SHA for every row below.
Evidence bytes are SHA-256 pinned in `manifest.json`. No self-referential commit
hash is embedded in its own contents.

| Finding | Severity | Owner | Candidate evidence | Closure criteria | Verdict |
|---|---|---|---|---|---|
| Public schema / approval | MEDIUM/P2 | Codex1 implementation; Codex2 review requested | openapi.json PublishedRecord/PublishedCapability; test_findings.py public schema/pending-page negatives | generated public response schema AND policy reject discovered/pending/active and empty top-level Evidence; external reviewer accepts exact corrected SHA | FIXED IN OFFLINE CANDIDATE / EXTERNAL ACCEPTANCE PENDING |
| Capability/binding Evidence | MEDIUM/P2 | Codex1; Codex2 review requested | Binding/Software/PublishedCapability minItems1; populated SI/AI/Robot/Software and capability negative tests; active even with Evidence denied | no populated unverified binding or approved claim with empty Evidence; active blocked under HOLD; external exact-SHA review | FIXED IN OFFLINE CANDIDATE / EXTERNAL ACCEPTANCE PENDING |
| Pagination approval pin | MEDIUM/P2 | Codex1; Codex2/Gemini consumer review requested | published_page(); required continuation source+approval pins; revocation/expiry/renewal conflict tests | filter before counts/offset; echo sourceRevision+approvalSetRevision; require both on continuation; changes fail409/restart; real atomic current authorization/audit separately tested | FIXED IN OFFLINE MODEL / HTTP NOT IMPLEMENTED |
| CFP+AI69110 / OpenAI69118 | HIGH/Governance | Registry custodian + Human Governance; Perplexity/GrokSI cross-check requested | GOV packet + five pinned raw artifacts; mapping addendum | authenticated decision/source precedence, requested reviewer receipts, separately authorized source diff/readback; preserve existing ID | OPEN/BLOCKED |
| Vietnam Parent / coverage | HIGH/Governance | Registry custodian + Human Governance; cross-check requested | GOV packet, 6984.md, HUB69.md, country index | authoritative explicit Parent/chapter relationship and source disposition; no guessed edge | OPEN/BLOCKED |
| Existing/proposed errors | LOW/P3 | Codex1; Codex2 review requested | operation-specific OpenAPI404/409/503 descriptions | existing Core source mismatch described503, ID conflict409; proposed approval pin mismatch409; consumer review | DOCUMENTATION CORRECTED / RUNTIME NOT RETESTED |

## Validation scope

Command:

```sh
python -m unittest -v test_findings \
  test_contract.ContractTests.test_schema_definitions \
  test_contract.ContractTests.test_references_resolve \
  test_contract.ContractTests.test_read_only_paths
```

19/19 targeted checks PASS (16 finding regressions + 3 affected schema/ref/GET
checks), `findings-test-results.txt`. The historical25 checks were NOT rerun.
`test-results.txt` remains the baseline log at652dd252; do not attribute it to new
runtime or new source acceptance.

Fresh-context agent in the SAME author session independently ran16 focused tests,
Draft2020-12 structural validation and53 reference resolutions; no new substantive
candidate defect reported. It also advanced the clock past approval expiry and
observed PUBLICATION_SNAPSHOT_CHANGED. This is not authenticated external Codex2,
Gemini, Claude, Perplexity or GrokSI acceptance; no ACK/verdict is recorded for them.

## Integration changes and remaining gates

Public clients must regenerate draft types for approved-only status and the new
approval pin. Empty SI/AI/Robot/Software/Capability lists remain valid when no
verified claim is supplied. Do not synthesize claims to satisfy minItems. Any
active operational status remains forbidden by this HOLD contract, even with
Evidence. Internal lifecycle schema remains separate; changing it later requires
review and authorization.

The helper is offline only: no listener, new service, Registry writer, live
adapter or approval issuer. Real signature verification/revocation, atomic
snapshot acquisition, field/link disclosure, audit fail-closed, HTTP error mapping,
CORS/rate limits, staging and device tests remain NOT VERIFIED. Semantic OpenAPI
validation remains NOT VERIFIED; JSON Schema structural checks are not a substitute.
All five adapter slots remain disabled and byte-identical to the baseline.

PR stays Draft. Runtime, Canonical ID/Parent/DID/Registry, IAM, DNS and production
remain untouched. Rollback removes this contract delta on the review branch.
HOLD ACTIVATION • PRODUCTION NO-GO.
