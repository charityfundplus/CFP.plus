# Existing Link Mẫu → Training → Worksheet • VI / EN

Use the existing authenticated SI/AI–HSTDN Office and its export button.
No new Link Mẫu, Core, public route or learner account is created.
Giữ cùng Link Mẫu hiện hữu; không mở Preview trong lượt chuẩn bị này.

1. Export current server-filtered evidence from the existing UI when authorized.
   Save the original envelope unchanged; do not include credentials or recovery
   keys. / Giữ file nguồn; không điền lại taskKey đã mất.
2. Run the new read-only adapter on an export copy:
   `node scripts/training-export-worksheet.mjs EXPORT.json ACTUAL_DEVELOPMENT_SHA`.
   The SHA argument is a provenance claim, not authority verification; the output
   explicitly keeps sourceRevisionVerified=false pending manifest readback.
3. The adapter verifies the existing UTF-8 payloadJSON SHA256, exact subject/pair,
   real taskKey and task template, eighteen checks, feedback/output binding and
   separate draft reviewer. Historical missing fields remain null/findings.
4. Basic lessons retain study acknowledgement only. A complete basic draft
   worksheet can support an assessment request, not certify advanced competence.
   Six advanced tracks stay NOT ASSESSED pending assigned assessor/prerequisites.
5. Country/Developer/declared Parent evidence and HSTDN member/source references
   retain separate source/capability/legal statuses. Unknown country/developer or
   member not in exported declarations is a finding, never a guessed identity.
6. Follow up through existing Task Board #130 with finding→evidence→recommended
   repair→closure. No change to old records, Canonical IDs or Audit History.

The three new tests use a small synthetic export fixture; they do not replay the
accepted five lessons/twelve exercises/advanced cohort or former browser/backup
tests. No new advanced PASS, named reviewer ACK or operational access is implied.

Runtime review pin remains b75b780eb64430355f0b51a4b58b9e5269e0db43.
Development changes remain separate, Draft/unmerged and HOLD ACTIVATION.
