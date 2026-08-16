# HUB 69 • Vận hành & Đồng bộ (Working)

## Cộng tác đa nền tảng (Working)

HUB 69 áp dụng nguyên tắc **Một Nội Dung Gốc • Ba Bản Gốc Đồng Bộ**. Notion, GitHub và Google Drive đều phải chứa **toàn văn cùng một phiên bản gốc** của mỗi tài liệu được công bố để Con Người và AI 🤖 có thể đọc, soi chiếu và review trực tiếp ở bất kỳ nền tảng nào.

- **Notion:** bản gốc làm việc và điều phối SoT.
- **GitHub:** bản gốc công khai/AI-readable, nội dung phải tương đương với Notion.
- **Google Drive:** bản gốc cộng tác, nội dung phải tương đương với Notion và GitHub.

### Chuẩn Canonical (Domain + Link)

- **Canonical Public Identity:** `cfp.plus`
- **Canonical Link format duy nhất:** `https://cfp.plus/{ID}`
- `www.cfp.plus`: technical host/redirect (nếu hạ tầng cần)
- `cfp.notion.site`: publishing/staging/fallback, **NON-CANONICAL**
- Notion workspace/pages: **Working Source of Truth (SoT)**

### Quy tắc đồng bộ chỉnh sửa

Nếu một nội dung hợp lệ được chỉnh sửa tại **bất kỳ một trong ba nơi**, CMP phải coi đó là một **Sync Event**: xác định tài liệu, version/thời điểm sửa, đối chiếu nội dung, rồi cập nhật cùng thay đổi sang **hai nền tảng còn lại**. Chỉ khi ba bản khớp nhau mới được đánh dấu **SYNCED / CURRENT**.

Nếu có hai chỉnh sửa đồng thời, khác nhau hoặc xung đột, CMP **không tự ghi đè**. Phải giữ nguyên cả hai bằng chứng, đánh dấu **SYNC CONFLICT / REVIEW REQUIRED**, chuyển cho reviewer và Human Governance khi cần.

Không nền tảng nào chỉ giữ bản tóm tắt thay cho nội dung gốc. Metadata kỹ thuật như Source Link, Version, Sync Timestamp, Commit SHA hoặc Revision ID có thể khác nhau nhưng **nội dung gốc phải thống nhất**. Các bản không tự tạo Governance Approval.

- [GitHub • HUB 69 Review & Collaboration Index](https://github.com/charityfundplus/CFP.plus/blob/main/docs/HUB69_COLLABORATION_INDEX.md)
- [Google Drive • CFP+ HUB 69 • Collaboration Workspace](https://drive.google.com/drive/folders/1JxTGabFVepUW22TwyyeUEV0ZBCpszr9Z)
- [Google Doc • HUB 69 • Review & Collaboration Index](https://docs.google.com/document/d/1FLleiyL76hZMi2V1-6pKxsw-JRhifsmGeNvitQuUn2U/edit)

**Review rule:** Finding → Evidence → Recommendation → Closure Criteria. Nội dung chưa đủ bằng chứng ghi **PENDING EVIDENCE**; không tự đổi, tái sử dụng hoặc khóa Canonical ID/Link.

## Publication Flow • AI Developer evidence-complete

- **Thailand → iApp Technology → Chinda LLM / ChindaMT / ChindaTTS** đã đạt minimal-profile evidence gate và được đẩy vào Chương 6 để review/publication. [Chương 6 • AI và Công Nghệ](https://app.notion.com/p/3b9caac9a557812b9d5dd58727edd9f7) • [Official evidence](https://open.iapp.co.th/) • [Chinda](https://chinda.iapp.co.th/). API capability có bằng chứng nhưng CFP+ E2E activation chưa thực hiện; giữ **Automation (Unverified) / CMP READY — TEST REQUIRED**. Không có Canonical ID/Link mutation hoặc Governance Approval.

- **South Korea → NAVER → HyperCLOVA X** đã đạt minimal-profile evidence gate và đã được đẩy vào Chương 6 để review/publication. [Chương 6 • AI và Công Nghệ](https://app.notion.com/p/3b9caac9a557812b9d5dd58727edd9f7) • [NAVER working profile](https://app.notion.com/p/638f43a5a4974dbfa67abc4aa0f315a7) • [Official evidence](https://www.navercorp.com/en/tech/hyperclovax). Không có Canonical ID/Link mutation hoặc Governance Approval.

- [HUB 69 Universal Master Template • v1.0 (Draft)](https://app.notion.com/p/19bc113a05654b19adb2a609506a8ace)
- [CFP SYNC 001 • Trung Tâm Đồng Bộ Đa Nền Tảng • Recovery Candidate](https://app.notion.com/p/3bdcaac9a55781bfbcf9e55124f33b2e)
- [CMP Automated Review Protocol • v1.0 • Official](https://app.notion.com/p/3bdcaac9a557811382a7d3539e09779c)

## Phát hành chính thức • CMP Automated Review v1.0

- [Website CMP Review](https://cfp.plus/cmp-review)
- [AI Manifest](https://cfp.plus/ai/manifest.json)
- [GitHub Protocol](https://github.com/charityfundplus/CFP.plus/blob/main/docs/CMP_AUTOMATED_REVIEW_PROTOCOL.md)
- [Google Docs Protocol](https://docs.google.com/document/d/15uSZwzz3-PaLbSUgIlQIckmCvhyDOKmX4blKx65JrNU)
- [CMP Automated Review Protocol • v1.0 • Official](https://app.notion.com/p/3bdcaac9a557811382a7d3539e09779c)

**Ranh giới:** Review tự động được phép. AI không tự Governance Approve, Canonical Lock, đổi Canonical ID hoặc xuất bản ngoài quy trình.
