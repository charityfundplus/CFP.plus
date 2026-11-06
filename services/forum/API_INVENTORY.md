# CFP+ Backend API • Kiểm kê theo module

Sinh tự động bởi `python -m services.forum.inventory --write` • CI kiểm tra khớp code.
**SANDBOX • NOT DEPLOYED.** Hợp đồng đầy đủ: `services/forum/openapi.json` (OpenAPI 3).

## Module (đã có / còn thiếu)

| Module | Trạng thái | Phạm vi | Ghi chú |
|---|---|---|---|
| Tài khoản • phiên đăng nhập | **implemented** | `/api/auth` |  |
| Diễn Đàn Siêu Bộ Đôi | **implemented** | `/api/forums/sieu-bo-doi` |  |
| Diễn Đàn SI AI • HSTDN | **implemented** | `/api/forums/si-ai-hstdn` |  |
| Văn Phòng SI AI • Siêu Bộ Đôi • CMP 267 (task/evidence/review) | **implemented** | `/api/office` |  |
| HSTDN • hồ sơ doanh nghiệp | **implemented** | `/api/office/enterprises` |  |
| Nghiên cứu • kho dữ liệu • giáo trình | **implemented** | `/api/office/topics, /api/office/datasets` |  |
| HUB 69 • tổng hợp chỉ đọc | **implemented** | `/api/hub` |  |
| AI Directory • Registry chỉ đọc | **implemented** | `/api/directory` |  |
| Link Mẫu • danh mục công trình (trang ID đã xuất bản + Registry, chỉ đọc) | **implemented** | `/api/catalog` |  |
| Worker P0 • hàng đợi + lịch chạy (heartbeat, retry, dead-letter, kill switch) | **partial** | `/api/worker/status` | SANDBOX: 1 việc chỉ đọc (registry_integrity). Chưa có runtime cố định → không phải 24/24. |
| Website • nội dung động và form | **missing** | `—` | Website hiện là nginx tĩnh; chưa có API nội dung/form. |
| App • API dùng chung | **partial** | `—` | App dùng được các API trên; chưa có client/App riêng trong repo. |
| Sàn TMTC 8682 • danh mục sản phẩm (sandbox, không thanh toán) | **missing** | `—` | Chưa có API danh mục; thanh toán không thuộc phạm vi. |
| CTTTC 28882 • đọc/tìm kiếm/nguồn chứng cứ | **missing** | `—` | Có schema + validator v0.6.6 trong repo; chưa có API. |

## Endpoint

| Module | Method | Path | Xác thực | Quyền thêm | CSRF | Kho dữ liệu |
|---|---|---|---|---|---|---|
| auth | POST | `/api/auth/login` | công khai |  | header X-CFP-Forum + Origin | auth (cfp_forum_auth) |
| auth | POST | `/api/auth/logout` | công khai |  | header X-CFP-Forum + Origin | auth (cfp_forum_auth) |
| auth | GET | `/api/auth/me` | công khai (+phiên nếu có) |  |  | auth (cfp_forum_auth) |
| auth | POST | `/api/auth/register` | công khai |  | header X-CFP-Forum + Origin | auth (cfp_forum_auth) |
| catalog | GET | `/api/catalog` | công khai |  |  | repo: trang <ID>/index.html đã xuất bản (chỉ đọc) + Registry |
| catalog | GET | `/api/catalog/meta` | công khai |  |  | repo: trang <ID>/index.html đã xuất bản (chỉ đọc) + Registry |
| catalog | GET | `/api/catalog/{cid}` | công khai |  |  | repo: trang <ID>/index.html đã xuất bản (chỉ đọc) + Registry |
| directory | GET | `/api/directory/countries` | công khai |  |  | Registry (tệp, chỉ đọc) + cfp_office (đọc) |
| directory | GET | `/api/directory/{eid}` | công khai |  |  | Registry (tệp, chỉ đọc) + cfp_office (đọc) |
| forums | GET | `/api/forums/{key}` | công khai (+phiên nếu có) |  |  | diễn đàn tương ứng (cfp_forum_sbd | cfp_forum_hstdn) |
| forums | POST | `/api/forums/{key}/join` | đăng nhập |  | header X-CFP-Forum + Origin | diễn đàn tương ứng (cfp_forum_sbd | cfp_forum_hstdn) |
| forums | GET | `/api/forums/{key}/members` | đăng nhập | admin của đúng diễn đàn |  | diễn đàn tương ứng (cfp_forum_sbd | cfp_forum_hstdn) |
| forums | POST | `/api/forums/{key}/members/{member_id}/approve` | đăng nhập | admin của đúng diễn đàn | header X-CFP-Forum + Origin | diễn đàn tương ứng (cfp_forum_sbd | cfp_forum_hstdn) |
| forums | GET | `/api/forums/{key}/posts` | công khai (+phiên nếu có) | Siêu Bộ Đôi: công khai • SI AI • HSTDN: thành viên đã duyệt |  | diễn đàn tương ứng (cfp_forum_sbd | cfp_forum_hstdn) |
| forums | POST | `/api/forums/{key}/posts` | đăng nhập | thành viên active của đúng diễn đàn | header X-CFP-Forum + Origin | diễn đàn tương ứng (cfp_forum_sbd | cfp_forum_hstdn) |
| forums | POST | `/api/forums/{key}/posts/{post_id}/comments` | đăng nhập | thành viên active của đúng diễn đàn | header X-CFP-Forum + Origin | diễn đàn tương ứng (cfp_forum_sbd | cfp_forum_hstdn) |
| health | GET | `/api/health` | công khai |  |  | tất cả (chỉ đọc trạng thái) |
| hub69 | GET | `/api/hub/69` | công khai |  |  | Registry (tệp, chỉ đọc) + cfp_office (đọc) |
| hub69 | GET | `/api/modules` | công khai |  |  | Registry (tệp, chỉ đọc) + cfp_office (đọc) |
| office | GET | `/api/office/agents` | công khai | công khai (sandbox) • Agent đang đào tạo, không phải danh sách đã nghiệm thu |  | cfp_office |
| office | GET | `/api/office/agents/{slug}` | công khai | công khai (sandbox) • cấu hình + Knowledge + kết quả kiểm thử hiện hành |  | cfp_office |
| office | POST | `/api/office/agents/{slug}/test-runs` | đăng nhập | người đã đăng nhập • chạy bộ tình huống, ghi audit | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/agents/{slug}/test-runs/{sha}` | công khai | công khai • Evidence tính lại; sha cũ → 409 |  | cfp_office |
| office | POST | `/api/office/answer-check` | đăng nhập | người đã đăng nhập • chỉ kiểm tra bản nháp, auto_reply=HOLD • audit không lưu nội dung | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/audit` | đăng nhập | governance • hoặc người tham gia/maintainer của đúng nhiệm vụ |  | cfp_office |
| office | GET | `/api/office/board` | công khai (+phiên nếu có) | theo quyền người xem (khách: rỗng) • REVIEWED cần Evidence + Review độc lập |  | cfp_office |
| office | POST | `/api/office/datasets` | đăng nhập |  | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/datasets/{did}` | công khai (+phiên nếu có) | access=members → người tạo / governance / người xem được nhiệm vụ dùng tài liệu |  | cfp_office |
| office | POST | `/api/office/enterprises` | đăng nhập |  | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/enterprises/{eid}` | công khai (+phiên nếu có) |  |  | cfp_office |
| office | GET | `/api/office/forum-links` | công khai (+phiên nếu có) | chỉ nhiệm vụ người xem được phép thấy • diễn đàn người xem đọc được |  | cfp_office (liên kết) + diễn đàn tương ứng (bài, qua đúng quy tắc diễn đàn) |
| office | GET | `/api/office/links` | công khai (+phiên nếu có) | ẩn liên kết tới nhiệm vụ/tài liệu không được xem |  | cfp_office |
| office | POST | `/api/office/links` | đăng nhập | chủ sở hữu mục nguồn / maintainer / governance • đích phải được xem | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/offices` | đăng nhập | governance • ID phải có trong Registry (type ai) | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/offices/{cid}` | công khai (+phiên nếu có) | khách: hồ sơ công khai • nhiệm vụ/evidence/review: người tham gia (assignee/reviewer/người tạo), maintainer, governance |  | cfp_office |
| office | POST | `/api/office/offices/{cid}/brand` | đăng nhập | maintainer/governance • nhãn xác nhận/ủy quyền: chỉ governance | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/offices/{cid}/maintainers/{uid}` | đăng nhập | governance | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/pairs` | đăng nhập | maintainer/governance | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/registry/{eid}` | công khai |  |  | cfp_office |
| office | GET | `/api/office/search` | công khai (+phiên nếu có) | tài liệu nội bộ chỉ hiện với người được xem |  | cfp_office |
| office | POST | `/api/office/tasks` | đăng nhập | maintainer/governance • reviewer độc lập có vai trò | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/tasks/{tid}/ack` | đăng nhập | người thực thi | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/tasks/{tid}/close` | đăng nhập | governance hoặc người giao việc • không phải người thực thi • cần ACCEPTED | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/tasks/{tid}/comments` | đăng nhập | người tham gia / maintainer / governance của đúng nhiệm vụ | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/tasks/{tid}/discussions` | đăng nhập | người xem được nhiệm vụ • thành viên active của ĐÚNG diễn đàn (diễn đàn tự kiểm) | header X-CFP-Forum + Origin | cfp_office (liên kết) + diễn đàn tương ứng (bài, qua đúng quy tắc diễn đàn) |
| office | POST | `/api/office/tasks/{tid}/evidence` | đăng nhập | người thực thi | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/tasks/{tid}/lessons` | đăng nhập | người xem được nhiệm vụ • chỉ sau Closure • ghi chủ đề theo Chương + liên kết | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/tasks/{tid}/loop` | đăng nhập | người xem được nhiệm vụ (khác → 404) • vòng khép kín từ dữ liệu thật |  | cfp_office |
| office | POST | `/api/office/tasks/{tid}/review` | đăng nhập | reviewer được chỉ định | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/tasks/{tid}/start` | đăng nhập | người thực thi • tối đa 5 việc song song | header X-CFP-Forum + Origin | cfp_office |
| office | POST | `/api/office/tasks/{tid}/submit` | đăng nhập | người thực thi • cần ≥1 Evidence | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/taxonomy` | công khai |  |  | cfp_office |
| office | POST | `/api/office/topics` | đăng nhập |  | header X-CFP-Forum + Origin | cfp_office |
| office | GET | `/api/office/topics/{tid}` | công khai (+phiên nếu có) |  |  | cfp_office |
| worker | POST | `/api/worker/control` | đăng nhập | governance Văn Phòng • kill switch (dừng/chạy lại) • ghi log kill_switch | header X-CFP-Forum + Origin | cfp_worker.control (qua worker_governance) + logs |
| worker | GET | `/api/worker/status` | công khai | công khai, chỉ số tổng hợp (không có nội dung lỗi/kết quả chi tiết) |  | cfp_worker (chỉ đọc) |

Ranh giới dữ liệu: mỗi kho là một schema + role riêng (#193 + 002_office.sql); role của kho này không có USAGE trên schema kho khác; `anon`/`authenticated` không có quyền.

RLS theo người dùng (003_office_rls.sql, **chưa áp Supabase**): backend đặt `cfp.user_id` mỗi giao dịch; Postgres tự tính governance/maintainer/người tham gia và ẩn hoặc chặn ghi dữ liệu của người khác (nhiệm vụ, evidence, review, lịch sử, tài liệu nội bộ, liên kết, audit). Thiếu danh tính → fail-closed.
