# CMP Direct Write Gateway

Status: IMPLEMENTATION IN PROGRESS
Blocker: CMP-EXECUTOR-WRITE-GATEWAY
Pilot: WO-CH7 • Doanh Nghiệp • Gemini

## Locked pilot

Target Notion page: `3bfcaac9a557819e82b0e3ae2b07943e`
Allowed anchor: `Integration Test Log`
Challenge token: `2026-08-18-1218`

## Runtime contract

The executor must perform, in order:

`READ → AI CALL → WRITE → READ BACK → VERIFY → EVIDENCE → RETURN`

Every stage uses one Execution ID.

## Environment

Runtime secrets must be supplied by the deployment environment and must never be committed to this repository.

Required runtime credentials:

- Notion integration credential with access to the locked pilot page.
- Gemini API credential.

## Fail closed rules

- Reject a target other than the locked pilot page during P0.
- Reject a write outside the allowed anchor.
- Append only. No delete or full page replacement.
- Stop if the challenge token cannot be read.
- Do not claim PASS unless the exact write is found during read back.
- Never store credentials in logs or evidence.

## Evidence receipt

A successful run must return:

- execution_id
- target_page_id
- anchor_block_id
- appended_block_ids
- read status
- write status
- read_back status
- exact-match result
- timestamps
- evidence hash if generated

## Closure rule

Until a real runtime produces physical Notion write and read-back evidence, status remains:

`HUMAN MEDIATED • EVIDENCE REQUIRED`

Only after a real end-to-end run may the pilot be considered for:

`GEMINI ↔ CMP ↔ NOTION • READ/WRITE VERIFIED`

Only Plus+ For Life
