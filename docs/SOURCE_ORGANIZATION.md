# CFP+ source organization / Tổ chức mã nguồn

2026-10-13. GitHub is the authoritative executable source and Git history. Google Drive holds immutable, versioned handover snapshots. Notion holds indexes, tasks and status. The website consumes reviewed source only after approval. No automatic two-way synchronization is enabled. This execution follows the user's current instruction; older Working-page language about three editable originals does not apply to executable source.

## Existing paths / Đường dẫn hiện hành

The functional names below are an index over existing paths, not new independent copies. All 656 current original paths remain intact; numeric website routes, ID/Parent/DID/Canonical, five groups, ten chapters, HUB69 and historical evidence are preserved. Duplicate checks do not authorize deletion.

| Function | Authoritative path | Usage / dependencies | Version and observed status |
| --- | --- | --- | --- |
| apps | numeric routes including `69/`, root `index.html`, `styles.css`; draft UI `drafts/si-office/public/` | Static website; P2 served by existing HTTP server. VI/EN mobile browser flow 8/8. Legacy website EN remains partial. | Baseline `3a883614c174`; draft synthetic PASS, production not deployed |
| core | `drafts/si-office/core/` | 12 modules plus common helpers; import `core-engine.mjs`; Node24 used, no external runtime packages | Shared Core; regression40/40 PASS |
| si-ai | `registry/`, `ai/`, `drafts/si-office/configs/pairs.json` | Existing Registry remains authority; draft snapshots do not allocate identity. Instantiate pair configuration on shared Core. | Versioned Git/configs; synthetic/unbound; real roster acceptance pending |
| software | `drafts/si-office/sandbox/`, `scripts/`; `cmp/executor/` | Existing P2 service, release tools and CLI; Node24 built-in SQLite; executor Python dependencies in its requirements.txt | P2/HTTP/rollback tested; executor not run this turn |
| integrations | `drafts/si-office/adapters.mjs`, `core/si-adapter.mjs`, existing CMP/API branches | Provider-neutral synthetic contracts; actual runtime descriptors disabled | Mock/read-synthetic only; five operational vaults disconnected |
| training | `drafts/si-office/configs/training-basic-v1.json`, `scripts/training-exercises.mjs`, `scripts/training-teams.mjs`, existing training docs | Five VI/EN lessons,12 exercises,six advanced curricula; use existing package scripts | Tests2/2; three separate DB/services × three pair templates PASS; real assessment NOT ASSESSED |
| tests | `drafts/si-office/tests/`, `tests/ctttc/`, `run_ctttc_v066_tests.py` | Node24; Python3.12/jsonschema; optional Python Playwright/Chromium for loopback browser | Current reruns recorded separately under evidence; CTTTC204/204 |
| docs | `docs/`, `drafts/si-office/docs/`, `hub69/`, `governance/`, `website/` | VI/EN design,runbooks,registry/source references; do not silently replace approved text | Mixed historical/design/draft; inspect pinned revision |
| evidence | existing `drafts/si-office/docs/*MANIFEST*`, `drafts/handover-v1/`; new `evidence/source-organization/` | Historical hashes apply to their original commits. SOURCE_MANIFEST is the 649-file pre-organization baseline. CURRENT_SOURCE_MANIFEST validates all656 files at the newer pinned HEAD. The existing verifier now validates WORKING_PREVIEW_MANIFEST (77 hashes). | SHA-256 and exact Git blob comparison; integrity is not governance approval |
| operations | existing `ops/`, P2_RUNBOOK; `operations/SOURCE_RESTORE.md` | Controlled snapshot,SQLite backup,isolated restore,release rollback | Restore source143/143 hashes and P2/teams rehearsal PASS |

Each module inherits its version from the pinned repository commit; no competing version number or canonical identity is invented. Individual Core module contracts and use are documented in `drafts/si-office/docs/CORE_ARCHITECTURE.md` and `CORE_RUNBOOK.md`; the 12 UI contracts remain in `public/office-contracts.js`. Pair instances use separate controlled state, not copied Core implementations. Do not follow older README copy instructions to create independently evolving operational cores.

## Synchronization / Đồng bộ

1. Pin source commit, scope and classification; inspect conflicts and private data before publishing new bytes.
2. Keep GitHub source/history; commit reviewable changes to Draft PR124 only. Never force-push, merge or deploy automatically.
3. Create a scoped archive only when recovery/handover needs one. Record date, source revision, byte count, SHA-256 and test status. Preserve old Drive artifacts.
4. Upload into the existing parent without sharing changes; download again and compare bytes and every scoped file digest.
5. Update existing Notion catalog/board with exact GitHub/Drive evidence links and statuses. Read back before marking that write verified.
6. Use SYNC VERIFIED only for the named resources actually compared. This does not certify five-vault operational synchronization, reviewer ACK, real competency or production.

## Branches and duplicates / Nhánh và trùng lặp

61 branch trees were inventoried (not truncated):14,909 branch file occurrences,1,312 unique path/blob variants;663 variants absent from current HEAD. `BRANCH_INDEX.json` pins branch revisions; `BRANCH_VARIANTS.json` lists retained alternatives for review. Full branch variant bytes were not all downloaded/tested; no unreviewed branch was merged. Concurrent commits4ad2375/b75b780 added7 files and changed3 while this inventory ran; latest pinned HEAD has656 byte-verified files. Preserve both dated snapshots.

Initial HEAD byte/checksum inventory:649 files;7 identical-content groups covering88 paths (81 copies beyond one per group),including21 empty files. Repeated numeric route skeletons and Python package markers are legitimate possible reasons; no deletion is recommended without dependency/reference/authority review. See `DUPLICATE_REVIEW.json`.

Git clone/history bundling could not connect in this session; source files were downloaded through authenticated GitHub connector and checked against Git blob SHA. GitHub retains all history; the Drive ZIP is explicitly a scoped source snapshot, not a complete Git history or private-state backup.
