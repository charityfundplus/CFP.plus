# HUB 69 • SHORT LINK / ID STANDARD • V1

## Nguyên tắc
Một Entity = Một Canonical ID. Ba kho GitHub, Google và Notion dùng cùng một ID số; không tạo ID riêng theo nền tảng.

## Công thức chung
Canonical Public: `https://cfp.plus/<ID>`
GitHub Short Alias: `https://cfp.plus/gh/<ID>`
Google Short Alias: `https://cfp.plus/gg/<ID>`
Notion Short Alias: `https://cfp.plus/nt/<ID>`

Chỉ `<ID>` thay đổi. Prefix nền tảng cố định: `gh`, `gg`, `nt`.

## Mapping 3 kho
| Kho | Alias rút gọn | Đích lưu trữ chuẩn |
| --- | --- | --- |
| GitHub | `cfp.plus/gh/<ID>` | `registry/<ID>.md` hoặc workspace/path đã đăng ký |
| Google | `cfp.plus/gg/<ID>` | Google Drive/Workspace/Site target URL đã đăng ký |
| Notion | `cfp.plus/nt/<ID>` | Notion Work Lane/Site target URL đã đăng ký |

## Ví dụ
HUB 69: `cfp.plus/69`
GitHub HUB 69: `cfp.plus/gh/69`
Google HUB 69: `cfp.plus/gg/69`
Notion HUB 69: `cfp.plus/nt/69`

Một AI có ID `691181`:
Canonical: `cfp.plus/691181`
GitHub: `cfp.plus/gh/691181`
Google: `cfp.plus/gg/691181`
Notion: `cfp.plus/nt/691181`

## Resolver Record bắt buộc
Mỗi ID có một hàng mapping:
`ID | Entity | Parent | Canonical | GitHub Target | Google Target | Notion Target | MCP | CMP | Evidence | Status`

## Trạng thái
`PENDING` → `LINK REGISTERED` → `TARGET VERIFIED` → `SYNC VERIFIED` → `WORKSPACE READY`.

## Guardrail
Alias rút gọn không tự tạo Canonical ID. Không renumber, không reuse conflict slot, không đổi Parent, không Canonical Lock nếu chưa có Human Governance decision. Nếu target chưa tồn tại thì giữ PENDING, không tạo link giả.

## Triển khai
Ba alias `gh`, `gg`, `nt` là lớp resolver/redirect của CFP+. URL gốc của GitHub, Google và Notion vẫn được lưu trong registry để audit và recovery.