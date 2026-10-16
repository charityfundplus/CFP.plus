# Bộ Đào Tạo Cơ Bản v1 / Basic Training v1

Core configuration: configs/training-basic-v1.json. One shared CoreEngine. SYNTHETIC / HUMAN REVIEW / PRODUCTION NO-GO.

## Step by Step / Từng bước

1. Read the task, allowed workspace/pair/resource and evidence requirements. / Đọc nhiệm vụ và phạm vi được cấp.
2. Sign into /p2 with a locally provisioned synthetic editor. / Đăng nhập editor giả lập do quản trị cấp.
3. Study five VI/EN lessons: identity/lineage, ethics/governance, tool use, security, evidence/assessment. / Học năm bài và ghi nhận học; không tự nâng quyền.
4. Select a permitted pair and a training-drill. Use one of twelve configured exercises. / Chọn cặp được cấp và bài tập phân hệ.
5. Run a supervised synthetic task. Inspect input, proposal and cross-check evidence. / Chạy có giám sát, đọc checks và output.
6. Reflect in task-scoped feedback; record observed result and evidence gap. / Lưu phản hồi gắn task/outputHash.
7. A different authenticated reviewer reviews the draft. / Reviewer khác chủ thể xem bằng chứng và kết luận.
8. If denied/faulted, preserve evidence; recover/retry only through authorized workflow. / Giữ lỗi và lịch sử, không tự tăng quyền.
9. Export/pin revision, task/checks/feedback/reviewer and digest. / Gắn revision và manifest vào kết quả.
10. Report only material exceptions; learning success never grants identity or real-operation permission. / Chỉ báo ngoại lệ trọng yếu.

Run all twelve supervised draft exercises: node scripts/training-exercises.mjs. This creates no real accounts, customer data, payments, network adapters or canonical identity. Each exercise uses the same engine; it is not proof that all Office production functions are complete.

## Advanced program / Chương trình nâng cao

Six draft tracks: durability/restart/idempotency; access isolation/revocation; recovery/backup/executable sandbox rollback; research provenance/conflicts; protocol interoperability; VI/EN website/navigation/approved sync. Prerequisites: basic content studied, authorized scope, demonstrated task evidence and separate review. Each advanced assessment must use exact revision and observed behavior; no automatic promotion or named ACK.

## Evidence-based assessment

Required: revision, taskKey, expected/observed result, checks, feedback, reviewer subject and digest. Assess scope compliance, bounded outputs, correct safe denial/recovery, traceable evidence and independent subject review. Current automated exercise results certify synthetic workflow behavior only. Verified real member identities, competence and reviewer authority remain separate evidence requirements.


## Integration supplement / Bổ sung tích hợp (Issue #130, 2026-10-14)

Source directive: issuecomment-6161167283. Existing keys, twelve exercise payloads and six advanced tracks stay unchanged. The new lesson steps use existing `steps.vi/en`; evidence labels in `assessment.requiredEvidence` describe the worksheet, not extra supported API fields. Reuse TRAINING_HSTDN_WORKBOOK_VI_EN.md for advanced deliverables.

Prerequisites / Đầu vào: authorized disposable synthetic fixtures, existing server workspace/pair/resource grants, distinct editor/reviewer subjects. Record full execution SHA separately from evidence commit SHA. Missing authority or fixture is BLOCKED; behavior not exercised is NOT TESTED, never FAIL. Preserve immutable identity and old audit history.

| Lesson | PASS requires / Điều kiện PASS | FAIL observed / FAIL thực tế | Limit / Giới hạn |
|---|---|---|---|
| identity-lineage | Injection denied, unbound profile and locked fields unchanged, before/after receipt | Unauthorized identity accepted or locked fields mutated | Synthetic fixture does not verify real identity |
| ethics-governance | Separate source/capability/legal statuses; legal claim NOT VERIFIED; independent review | Unsupported VERIFIED or inferred operational approval | Source provenance does not establish legal authority |
| tool-use | Scoped task/checks/outputHash/feedback/review retained; separate overreach fixture denied with null output | Out-of-scope accepted output or self-review accepted | Mock workflow does not certify live adapters |
| security | Authorized HTTP/UI cross-workspace denial without leak; retained old task/audit; explicit authorized recovery and new retry | Data leak, erased history or unauthorized replay | Direct demo actors do not establish server session isolation |
| evidence | Actual task/output/source lineage, verified export digest/readback and distinct reviewer | Unsupported PASS, invented ACK or automatic capability promotion | Synthetic reviewer separation does not authenticate real assessor authority |

STUDY ACKNOWLEDGEMENT records reading only. ASSESSMENT needs actual task/output/revision, rubric and authenticated assessor authority; otherwise NOT ASSESSED or NEEDS EVIDENCE. VERIFIED CAPABILITY needs explicit authorized verification of defined scope and limits. None grants privileges automatically.

Historical PASS keeps its original execution revision. Applying it to a later SHA requires unchanged relevant source/dependencies and a recorded applicability decision; changed runtime requires only focused affected checks.
