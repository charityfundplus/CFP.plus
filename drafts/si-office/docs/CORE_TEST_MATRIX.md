# Standard Core automated evidence • 13/10/2026

40/40 combined tests passed: 18 retained office/adapter regression tests + 22 Standard Core tests. In-process HTTP handler + actual core/adapter/checker methods, no socket/real model/network calls. Output: standard-core-test-results.txt; sample: core-demo-results.json.

| Scope | Evidence / result |
|---|---|
| 12 shared modules / config replication | 3 templates, one initial instance, new instances share one CoreEngine; unique key/config validation |
| Identity / Registry | Null identity, no self-issued fields/live mode, numeric-string preservation, read-only inventory NOT VERIFIED, conflict surfaced |
| Provider independence / protocol | mock-local/mock-alternate share contract; changed provider/protocol rejected |
| Mission / tools / resources | Unknown mission/resource/fields denied; roles enforced; source-only registry audit supported |
| Supervision / Cross-check | 16 axis checks + input/proposal controls; forged hash, changed title and false verification blocked |
| Tool-omission regression | Mandatory draft.write checked by trusted Core before adapter call, repeated by checker; malicious tools=[] cannot bypass policy |
| Human demo review | Separate session/role required, productionApproved=false; no real identity claim |
| Errors / timeout | Fault → FAILED, pair STOPPED, null output, retained audit, reviewer recovery and explicit new retry |
| Safe stop / concurrency | Stop during await prevents late commit; recovery waits quiescence; second active execution and completed-task replay denied |
| Learning | Safe-denial evaluation passes as exercise, privilegeChange=false and autoPromotion=false |
| Upgrade / rollback | Cohort synchronized; bad compatibility/health/active work cannot partly upgrade; identity/audit preserved |
| Website / US HSTDN drafts | Display-only 5 groups/10 chapters/scaffold, canonical=null; fictional products/services and legal relations NOT VERIFIED |
| HUB 69 / vault mock | Sole HUB, 10 reused read-synthetic adapters, externalRequests=0, connected=false |
| HTTP / GUI resources | Reuses role sessions; unauthorized/credential injection denied; /core and /core.js serve through actual handler |
| Browser / mobile | BLOCKED current environment; runnable suite prepared. Historical screenshots are office baseline only, not new Core evidence |

Independent Codex reviewer found a draft-write permission omission bypass, then verified its repair and reran final 40/40. This is not OpenSI/Grok acceptance or evidence of 8 independent reviewers. See CORE_INDEPENDENT_REVIEW.md.
