# CFP+ • Local Link Mẫu / CoreEngine / SI 🤖 AI evidence pack

**HOLD ACTIVATION • PRODUCTION NO-GO.** Evaluation baseline remains
`b75b780eb64430355f0b51a4b58b9e5269e0db43`; local draft additions do not replace it.

VI: Luồng hiện hữu Link Mẫu/Core tạo export theo selected pair. Chương trình
12 bài có nhiều pair, nên một export riêng không thể là evidence toàn bộ12.
Thêm `scripts/training-evidence-pack.mjs` dùng adapter hiện hữu để tổng hợp các
export **cùng learner**, mỗi pair một envelope. Không tạo Link Mẫu/Core/cohort
mới. Không đổi UI, curriculum, state/grants/audit hoặc baseline runtime.

EN: The existing selected-pair export covers only that pair's exercises. The
new offline pack combines envelopes for one learner across the configured
exercise pairs, preserves each input digest and actual task binding, and leaves
missing pairs/tasks/output digests incomplete. It rejects duplicate pair or
exercise mappings, foreign subjects/pairs and tampered envelope bytes. This is
an evidence organization tool, not an identity verifier or assessor.

## Local usage / sử dụng local

1. Dùng môi trường local hiện hữu và selected-pair download đã có; không kích hoạt host hoặc adapter thật. Chỉ export task mới thực sự cần phát triển; không chạy lại cohort đã PASS.
2. Giữ nguyên từng envelope `{payloadJSON, sha256, digestOf}` trong array JSON. Giữ actual taskKey và digest, không dựng key hồi tố hoặc đổi sourceRevision placeholder.
3. Chạy trong `drafts/si-office`:

```sh
node scripts/training-evidence-pack.mjs local-envelopes.json LEARNER_SUBJECT FULL_DEVELOPMENT_SHA > local-pack.json
```

4. Pack ghi lessons theo required pair, rows theo12 exercise của curriculum,
   missingPairs và input/output digests, declaration/HSTDN findings theo pair.
   Missing output digest không thành ready. Bằng chứng đủ chỉ có nghĩa
   basicDraftEvidenceReady, không competency PASS. Dữ liệu learner không tự
   chứng minh source revision/Build Manifest readback.
5. Reviewer thật cần identity/lineage/grants/prerequisite và receipt độc lập
   trước đánh giá; không dùng synthetic reviewer làm Human Governance.

All advanced tracks remain NOT ASSESSED; sourceRevisionVerified=false,
coreStateChanged=false, privilegeChange=false, activationAllowed=false,
providerCalls=0. Configured allowedPairs are a local scope check, not proof of
server grants or real membership. Workspace provenance remains dependent on
the authenticated original export and environment receipt; this tool does not
invent a workspace identifier absent from an export. No host/HTTPS/iPhone or
advanced competency claim.

Validation: 3 new pack tests, small two-pair synthetic fixtures only; no live
learner assignment, old12-exercise cohort or full Core/UI suites rerun.
