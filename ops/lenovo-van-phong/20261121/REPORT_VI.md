# CFP+ • HUB 69 • Khôi phục Văn Phòng Siêu Bộ Đôi trên Lenovo • 21/11/2026

**Đầu mối kỹ thuật:** Claude Code (phiên cloud sandbox) • **Điều phối:** ChatGPT Work
**Chế độ:** SANDBOX PRACTICE • HOLD ACTIVATION • PRODUCTION NO GO. Không merge, không deploy, không đổi Registry / Canonical ID / HUB 69.

## 0. Tóm tắt trạng thái

| # | Việc | Trạng thái | Bằng chứng |
|---|---|---|---|
| 1a | Văn Phòng (PR #124 `drafts/si-office`) chạy ở `127.0.0.1:4173`, mở trong Chromium | **VERIFIED (sandbox cloud)** | `evidence/chromium-open.json`, `evidence/office.png`, `evidence/core.png`, `evidence/office-mobile.png` |
| 1b | Mở trong Chrome **trên Lenovo** | **BLOCKED**: phiên này chưa kết nối được Lenovo (không có thư mục Remote Control nào được chia sẻ) | mục 4 |
| 1c | Nguyên nhân "manifest sai checksum" | **VERIFIED**: manifest lệch theo commit, không phải hỏng tệp | `evidence/manifest-drift.json` |
| 1d | PR #195 lấy đúng commit vào thư mục riêng | **VERIFIED** | worktree tách tại `287ce647aff410af912a85aea695e89ceb2fe868` |
| 2 | Một vòng Work Order P0 (Siêu Bộ Đôi 691121, dữ liệu giả lập) | **VERIFIED 29/30**; 1 FAIL là HTTPS (loopback không có TLS, đúng dự kiến) | `evidence/wo-loop-smoke.json` |
| 3 | Phối hợp SI AI qua Link Mẫu, kiểm tra mỗi giờ | **PENDING**: chưa có bằng chứng giao/nhận việc mới | mục 5 |

## 1. Văn Phòng tại cổng 4173 (PR #124)

- Mã: PR #124, head `e994ea884fdf7a06ca5efe20674b96a0d51e24f8`, thư mục `drafts/si-office`, Node v22.23.5.
- `npm test`: **40/40 pass, 0 fail** (phần mềm chạy).
- `npm start` → `CFP+ Sandbox: http://127.0.0.1:4173`. curl: `/` 200, `/core` 200; Host lạ → 403 `LOOPBACK_HOST_ONLY` (đúng thiết kế).
- Chromium 157 (Playwright, headless) mở 4 trang, **0 lỗi console**:
  - `http://127.0.0.1:4173/`: 200, "CFP+ • Văn Phòng SI AI"
  - `http://127.0.0.1:4173/core`: 200, "CFP+ • Bộ Code Lõi • Siêu Bộ Đôi"
  - bản điện thoại 390×844: 200
  - `http://localhost:4173/`: 200

Đây là bằng chứng trong **sandbox cloud**, chưa phải Chrome trên Lenovo.

## 2. Nguyên nhân manifest báo sai checksum

`node scripts/verify-evidence.mjs` (mặc định đọc `docs/ROUND1_CURRENT_MANIFEST.json`) tại head PR #124 báo `Evidence mismatch: configs/training-basic-v1.json`.

- Checksum của **chính manifest** khớp tệp `.sha256` → manifest không hỏng.
- Manifest được ghi lần cuối ở commit `d4d83ec` (13/10). Tại `d4d83ec`: **VERIFIED 88/88**.
- Sau đó các commit `8b53169`, `9d681d3`, `b381648`, `275c6b1`, `42e8bae`, `1958a3f`, `51e8a39`, `62e0e5f` sửa **13/88 tệp** mà không ghi lại manifest. Danh sách tệp và commit gây lệch: `evidence/manifest-drift.json`.
- Giả thuyết CRLF (git `autocrlf` trên Windows) đã kiểm: **không** giải thích 13 tệp này. Trên Lenovo Windows có thể có **thêm** lệch do CRLF; `lenovo-check.mjs` phân biệt hai loại.
- README của PR #124 cũng ghi: các manifest lịch sử "verify only at their pinned commits".

**Kết luận:** lỗi checksum không làm Văn Phòng hỏng và không phải nguyên nhân Chrome không mở. Có hai cách sửa (cần tác giả PR #124 / Human Governance chọn, vì đụng evidence đã nghiệm thu): (a) kiểm tại commit ghim `d4d83ec`; (b) tạo manifest mới cho head hiện tại, giữ manifest cũ làm lịch sử.

## 3. Vòng Work Order P0 (PR #195)

- Mã: PR #195, head `287ce647aff410af912a85aea695e89ceb2fe868`, thư mục riêng (git worktree, tách khỏi nhánh làm việc).
- Chạy: `CFP_SANDBOX_EPHEMERAL=1` (SQLite tạm, không Supabase, không secrets thật), uvicorn `127.0.0.1:8195`, worker `services.forum.worker run --interval 5`.
- Tài khoản giả lập `gov@` / `reviewer@sandbox.example.invalid`; mật khẩu sinh ngẫu nhiên tại chỗ, không ghi vào log hay báo cáo (đã quét: 0 lần xuất hiện).
- Kịch bản: `tests/forum/smoke_live.py` có sẵn trong PR #195, Siêu Bộ Đôi **691121 (Claude, 911 → 6911 → 69112 → 691121)**, ID có sẵn, không cấp ID mới.

| Bước | Kết quả | Ai thực hiện |
|---|---|---|
| Work Order: giao nhiệm vụ | PASS, task tạo, chuỗi Registry đúng | Phần mềm (smoke, vai governance) |
| ACK → Start | ACKED → IN_PROGRESS | Phần mềm (vai người thực thi) |
| Thảo luận Diễn Đàn Siêu Bộ Đôi + HSTDN | PASS, cách ly hai diễn đàn | Phần mềm |
| Evidence → Submit | 1 Evidence → IN_REVIEW | Phần mềm |
| Review độc lập | tự duyệt bị chặn 403; reviewer → ACCEPT | Phần mềm (vai reviewer) |
| Closure | người thực thi tự đóng → 403; governance → CLOSED | Phần mềm |
| Báo cáo / audit | 11 sự kiện audit; vòng khép kín 12/12 bước | Phần mềm |
| Worker + kill switch | heartbeat, dừng giữ 2 nhịp, chạy lại | Phần mềm (worker) |
| HTTPS | FAIL (loopback http), dự kiến | Hạ tầng: chờ Render (Human Governance) |

**Phần do SI AI (Claude Code) làm:** chọn commit, dựng môi trường tách biệt, cấu hình chế độ tạm, chạy và đọc kết quả, chẩn đoán manifest, viết báo cáo này và `lenovo-check.mjs`. **Phần do phần mềm làm:** mọi bước nghiệp vụ trong bảng trên (API PR #195 + script smoke có sẵn). Không có con người hay SI AI khác ký Review: "reviewer" là tài khoản giả lập, nên đây là **bằng chứng luồng chạy đúng**, không phải nghiệm thu năng lực.

## 4. Lenovo + Chrome: BLOCKED, bước khắc phục

Phiên Claude Code này chạy trên cloud. Lenovo **chưa chia sẻ thư mục nào qua Remote Control**, nên không kiểm được trực tiếp cổng 4173 và Chrome trên Lenovo.

**Bước người vận hành trên Lenovo (khoảng 5 phút):**
1. `git fetch origin codex/si-office-p0-draft-20261013 && git checkout e994ea8` (hoặc worktree riêng), vào `drafts/si-office`, `node -v` ≥ 22, `npm test` (mong đợi 40/40), `npm start`.
2. Ở cửa sổ khác: `node <repo>/ops/lenovo-van-phong/20261121/lenovo-check.mjs <repo>/drafts/si-office`. Gửi phần `verdict`, `probes` và `manifest.drift[].reason`; không cần gửi gì khác.
3. Chrome: mở đúng `http://127.0.0.1:4173/` (gõ `http://`; không dùng tên máy hay IP LAN, vì server trả 403).
4. Nếu bước 2 báo `SERVER OK` mà Chrome vẫn lỗi: thử cửa sổ ẩn danh (loại extension), `chrome://net-internals/#proxy` (proxy hệ thống/công ty chặn loopback?), đọc mã lỗi Chrome (`ERR_CONNECTION_REFUSED` = server không chạy hoặc chạy trong WSL/VM khác máy; `ERR_PROXY_*` = proxy).
5. Cách nhanh nhất để Claude Code tự kiểm: trong Claude desktop app trên Lenovo, **Settings → Claude Code → Remote Control**, chia sẻ thư mục repo. Phiên Claude Code sẽ xin kết nối, chạy các bước 1–4 và chụp màn hình.

## 5. Phối hợp SI AI

Chưa giao việc mới cho SI AI nào trong phiên này, vì chưa có bằng chứng chuyển giao. Đầu mối đề xuất (chờ ChatGPT Work xác nhận):

| Việc | Đầu mối | Trạng thái |
|---|---|---|
| Ghi lại manifest cho head PR #124 hoặc ghim `d4d83ec` | Codex (tác giả PR #124) | PENDING |
| Thẩm định SEC-01..06 trên head PR #195 | SecuritySI | PENDING (đã có trong checkpoint PR #195) |
| Render HTTPS sandbox (FAIL HTTPS còn lại) | Human Governance | HUMAN GOVERNANCE |
| Chạy `lenovo-check.mjs` và Chrome trên Lenovo | Người vận hành Lenovo | PENDING |

## 6. Bước kế tiếp

1. Người vận hành Lenovo làm mục 4 (hoặc bật Remote Control) → Claude Code cập nhật 1b thành VERIFIED hoặc ghi lỗi cụ thể.
2. ChatGPT Work chọn cách xử lý manifest (2a/2b) và giao Codex.
3. Claude Code kiểm tra tiến độ mỗi giờ trong phiên; chỉ báo khi có thay đổi có bằng chứng.
