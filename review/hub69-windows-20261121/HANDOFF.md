# HUB 69 dispatcher and Office sandbox review

This patch reuses PR207 at f755286e48c3f01a07f725820a53043ceee7b23c and PR195 at 287ce647aff410af912a85aea695e89ceb2fe868. The two review branches are codex/hub69-windows-sandbox-20261121 and codex/office-sandbox-overlay-20261121. Claude's findings were read at claude/sbd-flow-review-20261121, commit 36ba934.

## Changes

Windows uses an exclusive one-byte msvcrt lock, POSIX retains flock. Regression tests acquire locks across processes, verify contention, release on exceptions and operating system release when a child exits. Stores now have explicit close methods, including test cleanup before removing a SQLite directory on Windows. Console output uses UTF-8.

Named assignees must exist in configuration and match the existing machine Registry ID/name/Parent and numeric Working Link. Symbolic PENDING roles remain available for planning and cannot create an Office pair through the executor. A hash-pinned overlay provides synthetic fixtures for 2633/6535/267 only when ephemeral SQLite mode is explicitly active. Existing Registry entries cannot be overridden. Source evidence is retained in the fixture. Parent and Canonical files are unchanged.

The 2633 tool checks the existing Registry through the Office loader, 6535 performs an actual synthetic SQLite backup/restore exercise, and 267 audits the existing Working Links. These are deterministic tools under sandbox accounts. Independent reviewer verdicts remain pending.

Deduplication now uses assignee, work order code and source, with native task reference as the default work order code. Equal titles only produce a warning. File sources retain their path as source identity. Fixture duplicates explicitly retain the work order code. The Office idempotency key includes the same reference tuple.

Task source and work order code are retained in the existing QUEUED event and creation audit. Errors are retained in local durable logs and mirrored to authorized Office task comments, including after connectivity returns. The existing requeue flow remains in use.

The added Office route /api/office/entities/{did}/SUPER_SOFTWARE/{record_id}/tasks selects the existing super_pairs.id and applies existing participant/reviewer/maintainer controls. Wrong DID, type or record is denied. SI_AI has no separate persisted Entity Record in this Office schema, so this route rejects that type. A future SI_AI schema and canonical resolver semantics remain subject to separate review. Legacy Office discovery remains available for existing callers.

## Run

Use Python 3.11+ and the requirements in the Office checkout. All credentials are generated per run in memory. Choose a new output directory each run. The Office binds only to 127.0.0.1, creates isolated SQLite databases, stops at completion, and posts no GitHub or Notion messages.

Windows PowerShell from the dispatcher checkout

```powershell
.\sandbox\hub69-dispatch\run_three_sbd.ps1 -OfficeSource C:\path\to\office -OutputDirectory C:\path\to\new-pilot
```

For the existing Lenovo tools, pass -Python C:/Users/ai69/Documents/Codex/CFP-DevTools/Python311/tools/python.exe and -DependencyPath C:/Users/ai69/Documents/Codex/CFP-Sandbox/lenovo-python-deps.

Linux from the dispatcher checkout

```bash
HUB69_OFFICE_SRC=/path/to/office python3 sandbox/hub69-dispatch/three_sbd_pilot.py --out /tmp/new-pilot
```

Regression suite

```powershell
$env:HUB69_OFFICE_SRC='C:/path/to/office'
$env:HUB69_REQUIRE_OFFICE='1'
python -m unittest discover -s sandbox/hub69-dispatch/tests -v
```

## Evidence and limits

The readback verifies three real Office tasks reaching IN_REVIEW, preserved task IDs and Evidence hashes after replay and Office process restart, a second software Entity Record under the same DID remaining isolated, and eight actual HTTP requests producing one task. Supplemental tests cover executor exceptions, Office transport failure, 503, readback of error history, requeue, overlay gates and checksum.

Review logs and pilot outputs are included beside this document after the final test run. The data are synthetic. Execution of 94 independent SI AI accounts is unverified. Windows socket access previously failed under the restricted session; the actual pilot succeeds after the session network permission was granted. No Windows firewall or security policy was modified.

## Rollback

Stop the pilot or autopilot loop before switching checkouts. Revert the review commits in each branch or return to the pinned base SHAs. Keep the output folders, local state DB and Office SQLite files for audit. Remove the overlay environment variables to return to the original Registry loading behavior. These changes require no database schema migration. Reuse of existing idempotency data across versions should use the version that originally created those task requests.

## Final Lenovo results

Office companion local commit 5e172665f3d8db4c1e91b8d757c842df72db44f5. Full dispatcher run: 41/41 PASS. Focused lock/assignment run: 6/6 PASS, including one additional task-code/source dedupe case added after the full run. Thus 42 distinct dispatcher cases are covered across the two logs. Office API/contract run: 52 passed, 13 PostgreSQL cases skipped. The PowerShell entry point completed all three tasks, restart/readback, eight-request race and same-DID second-record isolation.

Publication status: local review commits only. Automatic approval rejected creating a remote commit because earlier instructions prohibit push. The HTTPS Evidence URLs in readback are intended publication destinations; online retrieval has not been verified. The result bytes and hashes have been verified locally and are included in results/. Independent Claude retest awaits publication approval or local artifact handoff. Local commit metadata uses Codex Sandbox <codex-sandbox@localhost>; no global Git settings changed.
