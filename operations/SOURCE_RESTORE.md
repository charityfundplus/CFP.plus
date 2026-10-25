# Source snapshot and isolated state recovery / Khôi phục nguồn và dữ liệu riêng

Do not overwrite working source, production databases, identity records or audit history. GitHub is the primary source/history. Drive snapshots are immutable handover artifacts.

## Source snapshot

Baseline revision: `3a883614c17443e1dd3bb94219139eb299f0e7ab` (parents include requested `40af3c85b01b4efdd6bfe7babbb6a4b4ab3a4222`).

Archive: [143-file Core/training/HUB69 snapshot](https://drive.google.com/file/d/1bT5fZNvm-TmHFqeaWB5U5dnYFrAOQAQ4/view?usp=drivesdk).

ZIP SHA-256: `72cbd147cf8385a307591036aa96c6736cd20bb8f40356251abd8ff04006256f`.

SOURCE_MANIFEST SHA-256: `05bb159cdae1558efb2d1fee356fb437bf9f7b7a736701f17764d2790d28f7e2`.

1. Download ZIP to a controlled machine; compare ZIP SHA-256 with receipt.
2. Extract into a new empty directory. The archive contains `drafts/si-office/`, `69/`, baseline SOURCE_MANIFEST and its digest; it is not the full repository. Verify every extracted source entry using the baseline manifest. Do not expect every manifest entry to exist in this scoped ZIP.
3. Use Node24+ with built-in SQLite. In restored `drafts/si-office/` run `npm test`, `npm run test:p2` and `node scripts/training-teams.mjs` as appropriate. This turn restored143 source entries and reran P2 10/10 plus3×3 isolated teams successfully.
4. For full source/history restoration, obtain the repository from GitHub and check out the exact pinned commit in a new checkout. No local full Git history bundle is claimed. Preserve branches rather than reconstructing ancestry from ZIP.
5. The old default evidence verifier in the baseline ZIP uses a historical pre-merge manifest; use SOURCE_MANIFEST for baseline source integrity. At concurrent HEAD b75b780 the existing verifier defaults to WORKING_PREVIEW_MANIFEST and passes77 hashes. Explicit historical selectors require their original source revision.

## Private training, subjects and audit

No retained real user/pair database was available in this workspace, and no private state was copied to public GitHub or source ZIP. Existing remote state was not inspected or modified. Preservation of unseen state is not certified.

Use the existing P2_RUNBOOK backup/restore flow for controlled state: authenticated maintainer `backup(token,newPath)` captures SQLite committed/WAL state and digest/checkpoint metadata; trusted local administration `P2Sandbox.restore(backup,newDestination)` verifies integrity/version and restores to a new database, revokes sessions and appends a restore generation. Keep original audit/history and reauthenticate. Independent external custodian/retention and process-kill/shared-DB multi-process assurance remain pending.

The new P2 tests verify successful restore,session revocation,corrupt-backup rejection and preserved task history. HTTP/release tests execute verified bundles and rollback to a separate DB while retaining the current audit backup. This is bounded synthetic rollback, not general production migration.

## Governance

Draft PR124 remains open/unmerged. No merge,deploy,sharing changes,real adapters,payment or identity mutation. Production requires Human Governance,verified identity/roster/assessors,actual five-vault owner/URL/scope/readback,independent audit and approved hosting/access policy.

## Current snapshot after concurrent preview update

Revision: `b75b780eb64430355f0b51a4b58b9e5269e0db43`. [Current150-file archive](https://drive.google.com/file/d/1rhjwMu4OB9kxdtJ07gNiycFDCXFvpk81/view?usp=drivesdk). ZIP SHA-256 `cf0b9a40d6f215c7d058a988e9f84c0fc5632bacd290a692e9f54f25e7eb5d45`; CURRENT_SOURCE_MANIFEST SHA-256 `a22cebc88de1acdf36a6fca89b7786591c4b71608fec2644850f01ee65df3ff5`. Downloaded bytes/150 entries match. Keep earlier snapshot immutable.

Run `python operations/verify-source-snapshot.py evidence/source-organization/CURRENT_SOURCE_MANIFEST.json a22cebc88de1acdf36a6fca89b7786591c4b71608fec2644850f01ee65df3ff5 --root /path/to/pinned/checkout` to verify656 original source files. For archive recovery replace `--root` with `--archive /path/to/snapshot.zip --archive-sha256 cf0b9a40d6f215c7d058a988e9f84c0fc5632bacd290a692e9f54f25e7eb5d45 --extract /new/empty-path`. Extraction refuses existing targets and unexpected/unsafe paths.
