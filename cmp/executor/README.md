# CMP Direct Write Gateway

Status: IMPLEMENTATION IN PROGRESS
Blocker: CMP-EXECUTOR-WRITE-GATEWAY
Pilot: WO-CH7 • Doanh Nghiệp • Gemini

## Locked pilot

Target Notion page: `3bfcaac9a557819e82b0e3ae2b07943e`
Allowed anchor: `Integration Test Log`
Challenge token: `2026-08-18-1218`

## Runtime

The first executable runtime is a GitHub Actions workflow:

`.github/workflows/cmp-gemini-notion-pilot.yml`

It performs:

`READ → GEMINI API CALL → WRITE → READ BACK → VERIFY → EVIDENCE`

Every stage uses one Execution ID supplied at workflow dispatch.

## Required GitHub Actions secrets

Configure these once in the repository's Actions secrets:

- `GEMINI_API_KEY`
- `NOTION_TOKEN`

Never place either credential in source files, issues, pull requests, logs, or Notion evidence records.

## Fail closed rules

- Target is locked to the WO-CH7 pilot page during P0.
- Write is restricted to the `Integration Test Log` anchor.
- Append only. No delete or full page replacement.
- Stop if the challenge token cannot be read.
- Do not claim PASS unless the exact execution receipt is found during read back.
- Never store credentials in evidence artifacts.

## Evidence receipt

A successful run returns an uploaded artifact containing a redacted receipt with:

- execution_id
- target_page_id
- appended_block_ids
- read status
- Gemini call status
- write status
- read_back status
- exact-match result
- timestamp
- evidence hash

## Closure rule

Until a real workflow run produces physical Notion write and read-back evidence, status remains:

`HUMAN MEDIATED • EVIDENCE REQUIRED`

After the real end-to-end run passes, the pilot may be considered for:

`GEMINI ↔ CMP ↔ NOTION • READ/WRITE VERIFIED`

Only Plus+ For Life
