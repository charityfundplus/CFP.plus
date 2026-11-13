"""Link Mẫu • Danh mục công trình CFP+ (chỉ đọc, chỉ dữ liệu đã xác minh).

Nguồn sự thật (không bịa, không cấp ID):
  • Mỗi trang ID số đã xuất bản trong repo (`<ID>/index.html`, là nội dung cfp.plus phục vụ) = một bản ghi.
  • Parent chỉ lấy từ Registry (`services.forum.registry`); không có → `parent_status = pending_verification`.
  • Công trình được nêu tên nhưng chưa có trang/ID trong repo → danh sách `pending` (không có canonical_id).

Ba lớp tách biệt cho mỗi bản ghi:
  identity  (bất biến)   : canonical_id, canonical_url
  source    (có version) : title, description, version = sha256(nội dung tệp nguồn), source path
  operation (vận hành)   : liên kết sandbox, trạng thái chức năng — tính tại chỗ, không ghi đè nguồn.
Chỉ mục dựng lại mỗi lần khởi động (mỗi deploy); version đổi khi và chỉ khi nội dung nguồn đổi.
"""
from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_BASE = "https://cfp.plus"

# Công trình được Người sáng lập nêu tên (lệnh 6667318954) mà repo CHƯA có trang ID số đã xuất bản.
# Không gán ID/URL: chờ Registry/Human Governance xác minh.
PENDING = (
    {"name": "App CFP+", "note": "Chưa có trang ID số trong repo; thiết kế Canva DAHZzR3gzHM (không phải backend)."},
    {"name": "3366 • đa ngôn ngữ", "note": "Chưa có thư mục 3366/ trong repo."},
    {"name": "Quantum", "note": "Chưa có trang/ID trong repo."},
    {"name": "Gen Z", "note": "Chưa có trang/ID trong repo."},
    {"name": "Giáo trình 10 học phần miễn phí", "note": "Tuyến song song; chưa có trang/ID trong repo."},
)

# Thành phần sandbox (INTERNAL • không phải route công khai, không có Canonical ID mới).
SANDBOX = (
    {"name": "Diễn Đàn Siêu Bộ Đôi", "path": "/_internal/forum/sieu-bo-doi/", "module": 3},
    {"name": "Diễn Đàn SI AI • HSTDN", "path": "/_internal/forum/si-ai-hstdn/", "module": 3},
    {"name": "HUB 69 • Văn Phòng SI AI (danh bạ)", "path": "/_internal/office/", "module": 2},
    {"name": "Bảng điều phối (task/ACK/Evidence/Review, worker)", "path": "/_internal/ops/", "module": 4},
    {"name": "Văn Phòng Siêu Bộ Đôi (danh sách + nút điều hướng thật, tích hợp Canva)",
     "path": "/_internal/van-phong-sieu-bo-doi/", "module": 2},
    {"name": "Bản đồ hệ sinh thái (10 phân hệ • trạng thái thật)", "path": "/_internal/map/", "module": 0},
    {"name": "Link Mẫu phổ thông (hồ sơ theo ID, theo quyền)", "path": "/_internal/linkmau/69/", "module": 1},
    {"name": "Văn Phòng Agent • Meta Business Agent (TRAINING • AUTO REPLY HOLD • chưa nghiệm thu)",
     "path": "/_internal/agent/meta-business-agent/", "module": 5},
)

# 10 module chức năng của Link Mẫu (không phải cấp ID số). Trạng thái = thực tế trong sandbox.
MODULES = (
    (0, "Mở rộng", "planned"), (1, "Hồ sơ • ID", "implemented"), (2, "Văn Phòng • Siêu Bộ Đôi", "implemented"),
    (3, "Diễn Đàn", "implemented"), (4, "Task • ACK • Evidence • Review", "implemented"),
    (5, "Công cụ • Siêu Phần Mềm (worker)", "partial"), (6, "Kho công trình • tài liệu • nghiên cứu", "implemented"),
    (7, "Đa ngôn ngữ • voice", "planned"), (8, "Test • an toàn • giám sát", "partial"), (9, "Kết quả • lịch sử", "partial"),
)

HOLDING_DIR = "registry/review-holding"
_HOLD_ROW = re.compile(r"^\|\s*([0-9]{1,32})\s*\|.*\|\s*([^|]*?)\s*\|\s*$")
_H1_IDS = re.compile(r"\b[0-9]{2,32}\b")


def load_holds(root: Path) -> dict[str, dict]:
    """ID đang bị giữ (HOLD) theo hồ sơ review-holding: chỉ ĐỌC; không sửa Registry, không tự gỡ HOLD."""
    holds: dict[str, dict] = {}
    d = root / HOLDING_DIR
    for f in sorted(d.glob("*.md")) if d.is_dir() else []:
        lines = f.read_text("utf-8", "replace").splitlines()
        src = f"repo:{HOLDING_DIR}/{f.name}"
        h1 = next((ln for ln in lines if ln.startswith("# ")), "")
        for cid in _H1_IDS.findall(h1.split("•", 1)[-1] if "•" in h1 else ""):
            holds.setdefault(cid, {"source": src, "finding": "ID error under review"})
        for ln in lines:
            m = _HOLD_ROW.match(ln)
            if m:
                holds[m.group(1)] = {"source": src, "finding": m.group(2)}
    return holds


_TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
_DESC = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"', re.I)


def fold(s: str) -> str:
    """So khớp không dấu, không phân biệt hoa thường (đ → d)."""
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()


class Catalog:
    def __init__(self, registry, root: Path = REPO_ROOT):
        self.registry = registry
        self.reload(root)

    def resolve(self, ref: str) -> dict | None:
        """Link con chỉ lưu `catalog:<ID>`; nội dung luôn đọc từ bản gốc HIỆN HÀNH (không sao chép)."""
        kind, _, cid = ref.partition(":")
        it = self.items.get(cid) if kind == "catalog" else None
        return {k: it[k] for k in ("canonical_id", "canonical_url", "title", "version")} if it else None

    def reload(self, root: Path = REPO_ROOT) -> None:
        """Dựng lại chỉ mục từ nguồn (mỗi deploy). Cập nhật nội dung gốc một lần → mọi link con thấy version mới."""
        registry = self.registry
        self.holds = load_holds(root)
        self.items: dict[str, dict] = {}
        for d in sorted(p for p in root.iterdir() if p.is_dir() and re.fullmatch(r"[0-9]{1,32}", p.name)):
            f = d / "index.html"
            if not f.is_file():
                continue
            raw = f.read_bytes()
            text = raw.decode("utf-8", "replace")
            title = html.unescape((_TITLE.search(text) or [None, ""])[1]).strip()
            desc = html.unescape((_DESC.search(text) or [None, ""])[1]).strip()
            ent = registry.get(d.name)
            parent = ent.parent_id if ent else None
            self.items[d.name] = {
                "canonical_id": d.name,
                "canonical_url": f"{PUBLIC_BASE}/{d.name}/",
                "title": title or d.name,
                "description": desc[:300],
                "parent_id": parent,
                # registry: Parent khai báo trong Registry • inferred_prefix: Registry tự suy từ tiền tố (CHƯA xác minh)
                # hold_conflict: chính ID đang HOLD • parent_hold: Parent đang HOLD → KHÔNG coi là đã xác minh
                "parent_status": ("hold_conflict" if d.name in self.holds else
                                  "pending_verification" if not parent else
                                  "parent_hold" if parent in self.holds else
                                  "registry" if ent.parent_source == "explicit" else "inferred_prefix"),
                "hold": self.holds.get(d.name) or (dict(self.holds[parent], parent=parent)
                                                   if parent in self.holds else None),
                "registry_type": ent.type if ent else None,
                "version": "sha256:" + hashlib.sha256(raw).hexdigest()[:16],
                "source": f"repo:{d.name}/index.html",
                "classification": "PUBLIC",
                "access_scope": "public",
                "sandbox_url": f"/{d.name}/",
            }

    def search(self, q: str | None, limit: int = 50) -> list[dict]:
        rows = list(self.items.values())
        if q:
            k = fold(q.strip())
            rows = [r for r in rows if k in fold(f"{r['canonical_id']} {r['title']} {r['description']}")]
            rows.sort(key=lambda r: (not r["canonical_id"].startswith(q.strip()), len(r["canonical_id"]), r["canonical_id"]))
        return rows[:limit]
