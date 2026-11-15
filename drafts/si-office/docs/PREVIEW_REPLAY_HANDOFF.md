# HUB 69 • Exact replay package and guided intake

13/10/2026. HUMAN REVIEW • PRODUCTION NO-GO.

## Accepted revision package

[Download replay package for accepted revision 2814b357d8b31385aff530ca37eb8606674b608e](https://drive.google.com/file/d/1i3wmDKK4140PWYiKoUHW-iL7pZsS-mtq/view).

ZIP: 139077 bytes. SHA-256: `b6d0294970e4962bf45a58cd9b296d2fed3c8c5ff6ed9b6daf1886aa8c014f69`.

Manifest SHA-256: `2f9f59cd4d698cba6f362fc20e1215643858e73548280d9ee8e856a66feefcf1`.

All 64 scoped runtime files were compared with exact Git blob hashes and sizes. Google download matched archive bytes and all runtime entries. `release/` contains only that accepted revision. `tools/` contains package verification/launch helpers; README_PREVIEW_VI.md includes local instructions and a proposal for an approved HTTPS forwarder. No account, token, certificate/key or SQLite state is bundled. Existing personal/audit state was not changed.

The launcher verifies manifest/hash/size/path boundaries, rejects tampered or unexpected source and derives the revision from the verified manifest. New packaging checks PASS: 64 sources verified; tamper rejected; actual HTTPS GET/p2 returned 200 with the exact accepted revision header. Local replay used https://localhost:4214/p2 and was stopped. Default4190 returned a generic start failure; no root cause was inferred. Replay test trusted only its temporary local certificate; it is not an iPhone certificate or public URL.

Current environment status has no host identity, hostname, secret binding or supported inbound HTTPS forwarding capability. TCP destinations are empty. No tunnel, DNS, Cloudflare, Sites or production deployment was created. A URL that an iPhone outside the executor can open is still unavailable. Do not ask for the same host information again before new configuration exists. Historical public ephemeral receipts on the branch remain distinct; they do not prove current availability or the new candidate.

## Current intake and new navigation

Concurrent revision `8b53169e3353ebc8e798cd8a658aebd5afbd037d` extended existing Core intake with declarations, explicit source/relationship records, append-only amendments, enrollment, marketing and work requests. It retains NOT VERIFIED / NOT ASSESSED / NOT AUTHORIZED distinctions, server scope and synthetic-only behavior. Its OFFICE_INTAKE_HANDOVER.md and test files are source-reported evidence; this continuation did not repeat those underlying suites or supply independent reviewer acceptance.

The initial local prototype overlapped that concurrent work and was not applied over it. This final delta preserves the newer Core/UI/permission/export implementation and adds only seven contextual navigation links in existing `public/office-intake.js`:

1. Link Mẫu → existing universal office.
2. Đăng ký → existing application, or issued-account login when signed out.
3. Xác minh → existing declaration/source review display, explicitly pending review; it does not verify real identity.
4. Học tập → existing public basic curriculum.
5. Thực hành → existing course/exercise flow after login.
6. Nhận việc → existing work-request form; request does not authorize execution.
7. Evidence → existing scoped export after login.

The accepted2814 package contains its original four-link UI and is immutable. The seven-step candidate has a separate new draft revision; never label its source as2814. ID, Parent, DID, Canonical, Registry and existing Audit History are unchanged by this navigation delta. No new Core or registry is introduced.

## Validation and review gate

PREVIEW_STEPS_BROWSER.json records three new focused groups PASS on actual local TLS/Chromium: anonymous links resolve and protected actions lead to login; authenticated links resolve against existing intake with viewer permissions retained; VI/EN320/390, logout resets links, no page errors. Only synthetic temporary accounts/state; services stopped. The test fixture omits a revision header for uncommitted QA rather than falsely identifying a build. Full intake, Core, course, Routing and other unaffected suites were not rerun.

Actual CFP+ direct review and Safari on a real iPhone remain PENDING. Record exact reviewed revision, device/browser, path, expected/actual result and Evidence. After real feedback, apply one focused repair and retest only affected behavior. No feedback, reviewer ACK or competence certification is invented.

MCP/CMP retain separate connection exceptions; no new call or mock success is reported. Notion/GitHub/Google coordination is not five-store live sync. Website https://cfp.plus/69 unchanged. Routing evidence remains closed/retained; Cloud Run and343/8882/HTTP-nginx exceptions do not block this replay/local work. No merge/deploy or production access changes.
