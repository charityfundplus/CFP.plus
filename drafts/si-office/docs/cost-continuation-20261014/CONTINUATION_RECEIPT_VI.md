# CFP+ • Kết quả thực tế / source phục hồi • 14/10/2026

**CONDITIONAL APPROVAL • HOLD ACTIVATION • PRODUCTION NO-GO.**
Baseline đánh giá b75b780eb64430355f0b51a4b58b9e5269e0db43 giữ nguyên.
Parent draft đọc được 4e6e11a1e7d8d4edcf361ac2f79b183d678cb20a.
Không checkout hoặc clone/chuyển branch local; fetch chọn file để dev độc lập.

## Ngoại lệ nguồn cost-bound trước đây

Issue130/PR124/Notion ghi hai artifact local phiên trước:
- scripts/cost-bound.mjs SHA256 6bf77ec5fabc8fe3ad21f0ba64db9bb172321e97116870e6c9162b99bc8c8509
- cost-bound.test.mjs SHA256 bf4115f6cab1f6769ec7cca0a72783ef26d9490d23c7ae730414aa3745b1e097

Workspace hiện tại không có thư mục cfp-cost-review hoặc source này. **Không
claim khôi phục byte-for-byte**. Source mới theo đặc tả F+U+D+R+S được phục hồi
và kiểm đúng5 case tại revision lượt này; hash mới trong MANIFEST.json.
Historical5/5 và hai hash cũ giữ nguyên là lịch sử, không dùng như evidence
cho bytes mới. Calculator offline không fetch evidence hoặc xác thực authority.

## New scoped validation

Node v24.19.0, local synthetic input only:

```sh
node tests/cost-bound.test.mjs
node tests/training-evidence-pack.test.mjs
```

Cost5/5 PASS, exit0; pack3/3 PASS, exit0, raw logs cùng thư mục.
Lần đầu `node --test` chỉ báo file-wrapper pass, không liệt kê ca; không tính
wrapper đó là5/3 PASS. Chạy file trực tiếp cho actual named cases. Pack được
kiểm lại sau thay đổi liên quan missing-output digest; cost không rerun sau PASS.
Các suite Core/training/browser/backup/kernel/cohort cũ không chạy lại.

Cost tests: unknownD/R không=0; grossUSD/nonoverlap/scope; exact1500 không
hardcap/authority; residual vượt target; negative/fractional/unsafe/ref missing
fail-closed. Các ref example.invalid là fixture, không evidence thật.
Pack tests: hợp nhất hai pair cùng subject, missing pair/output incomplete,
hash/foreign/duplicate/reused mapping denied. Không actual assessment/grants.

## Deliverables / giới hạn

Cost source+5 tests+log+manifest được đưa vào existing DraftPR124; bảng DO/Render
hoàn thiện khoản phí, nguồn và UNKNOWN; checklist host/accounts/rollback chuẩn
bị; local pack giúp Link Mẫu/Core training organization miễn phí. Chỉ additive
source/docs; không sửa runtime hoặc artifact lịch sử.

Còn thiếu: account gross/tax/FX/quota/pending/D/R và hardcap; host/lease/closure
authority/observer; named operator/deputy/custodian/reviewer và actual access
admin@cfp.plus; off-host custody/restore/RPO/RTO; downgrade data preservation;
advanced prerequisite/assessor/real learner evidence. Historical24 NOT ASSESSED.
Render compute pricing open trả shell; estimate7.00 cần quote xác nhận lại.

Bước tiếp: tiếp tục local artifact/code review khi có delta; HG bổ sung
account/role/authority receipt, chọn một provider/full runtime revision và
phê duyệt host rehearsal riêng trước khi thực thi. Hiện không yêu cầu mua host
để tiếp tục. Không gọi lại các hạng mục PASS không thay đổi.

Không checkout, paid resources, DNS, merge, deploy hoặc real adapters; không
mutate ID/Parent/DID/Canonical/AuditHistory/Driveowner/ACL. GitHub+Notion cập
nhật lượt này không chứng minh five-store runtime sync.
