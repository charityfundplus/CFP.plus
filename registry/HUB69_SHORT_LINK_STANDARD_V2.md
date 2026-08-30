# HUB 69 • SHORT LINK ID STANDARD • V2.1

## Quy tắc bắt buộc
Mọi ký tự chữ nhận diện KHO phải nằm trước tên miền `cfp.plus` dưới dạng subdomain.
Sau dấu `/` chỉ được phép là Canonical ID bằng số.

## Phạm vi áp dụng
Chuẩn link rút gọn này chỉ áp dụng cho 3 kho nền tảng:
- Website gốc: `https://cfp.plus/<ID>`
- GitHub: `https://gh.cfp.plus/<ID>`
- Google: `https://gg.cfp.plus/<ID>`
- Notion: `https://nt.cfp.plus/<ID>`

## Không áp dụng cho MCP và CMP
MCP và CMP thuộc nội dung trong hệ 10 Chương CFP+, không phải mã kho trong công thức link rút gọn 3 kho.
Không dùng:
- `https://mcp.cfp.plus/<ID>`
- `https://cmp.cfp.plus/<ID>`

MCP và CMP phải sử dụng Canonical ID số của chính nội dung tương ứng trong cấu trúc 10 Chương và được truy cập theo Canonical Link `https://cfp.plus/<ID>` hoặc projection của 3 kho khi cần.

## Ví dụ HUB 69
- `https://cfp.plus/69`
- `https://gh.cfp.plus/69`
- `https://gg.cfp.plus/69`
- `https://nt.cfp.plus/69`

## Ví dụ AI ID 691181
- `https://cfp.plus/691181`
- `https://gh.cfp.plus/691181`
- `https://gg.cfp.plus/691181`
- `https://nt.cfp.plus/691181`

## Guardrail
Không dùng dạng `cfp.plus/gh/<ID>`, `cfp.plus/gg/<ID>`, `cfp.plus/nt/<ID>` hoặc bất kỳ ký tự nào sau tên miền. Sau `/` chỉ có số. Canonical ID không thay đổi giữa các kho.

Status: V2.1 corrected by Human Governance • MCP/CMP subdomain proposal withdrawn • resolver deployment still requires verification.
