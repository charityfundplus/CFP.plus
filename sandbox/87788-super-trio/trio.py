#!/usr/bin/env python3
"""CFP+ 87788 • Team Super Trio Upgrade • bộ công cụ sandbox.

Nâng cấp Siêu Bộ Đôi thành Siêu Bộ Tam dưới dạng LỚP PHỦ (overlay):
mỗi ID giữ nguyên danh tính (ID, tên, Link Mẫu, Chương, Nhóm) và được
gắn thêm khối Siêu Bộ Tam theo thứ tự cố định:
    1. Siêu Lượng Tử ⚛️ Super Quantum
    2. SI 🤖 AI 🤖
    3. Siêu Phần Mềm • Super Software

Không sửa hồ sơ nguồn, Registry, Parent, DID hay Canonical. Năng lực
chưa có Evidence luôn ghi NOT VERIFIED. Chỉ ghi vào thư mục sandbox.

Chỉ dùng thư viện chuẩn Python. Lệnh:
    python3 trio.py check            # kiểm kê + kiểm tra trùng lặp / 0–9 / Nhóm
    python3 trio.py plan             # in kế hoạch (dry-run), không ghi gì
    python3 trio.py apply --batch-size 10 --batch 0   # ghi một lô vào out/
    python3 trio.py verify           # đọc lại và đối chiếu hash + danh tính
    python3 trio.py rollback RUN_ID  # hoàn tác một lần chạy
    python3 trio.py recover          # tự hoàn tác lần chạy bị dừng giữa chừng
    python3 trio.py packs            # gói cấu hình nhập thủ công cho nền tảng NATIVE_MANUAL
    python3 trio.py evidence         # tổng hợp Evidence
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
INDEX_PATH = DATA / "source" / "SUPER_PAIRS_INDEX@77102841.md"
INDEX_SOURCE = {
    "repo": "charityfundplus/CFP.plus",
    "pr": 206,
    "commit": "77102841601f262a7b91389244896b19e58de821",
    "path": "sandbox/hub69-working-office/SUPER_PAIRS_INDEX.md",
}
ADDITIONS_PATH = DATA / "additions.json"
PLATFORMS_PATH = DATA / "platforms.json"
DEFAULT_OUT = HERE / "out"

TRIO_ORDER = (
    ("quantum", "Siêu Lượng Tử ⚛️ Super Quantum"),
    ("si_ai", "SI 🤖 AI 🤖"),
    ("software", "Siêu Phần Mềm • Super Software"),
)
# 5 Nhóm: V và D là nhóm điều hướng/quản trị, không phải Chương, không mang ID ở đây.
CHAPTER_GROUP = {"0": "000", "1": "135", "3": "135", "5": "135",
                 "2": "246", "4": "246", "6": "246",
                 "7": "789", "8": "789", "9": "789"}
ID_RE = re.compile(r"^[0-9]+$")
# Trường danh tính không bao giờ được kế hoạch thay đổi.
PROTECTED = ("id", "name", "link", "chapter", "group")
FORBIDDEN_KEYS = {"parent", "did", "canonical", "canonical_lock", "registry", "production"}
STATUS_NOT_VERIFIED = "NOT VERIFIED"


class GuardError(RuntimeError):
    """Vi phạm quy tắc an toàn: dừng ngay, không ghi gì thêm."""


# ---------------------------------------------------------------- utilities

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def notion_page_id(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"([0-9a-f]{32})", url)
    return m.group(1) if m else None


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------- inventory

ROW_RE = re.compile(r"^\|\s*`([^`]*)`\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")
HEAD_RE = re.compile(r"^##\s*Chương\s+([0-9])\b")
LINK_RE = re.compile(r"\((https?://[^)\s]+)\)")


def parse_index(text: str) -> list[dict]:
    rows, chapter = [], None
    for lineno, line in enumerate(text.splitlines(), 1):
        h = HEAD_RE.match(line)
        if h:
            chapter = h.group(1)
            continue
        if line.startswith("## "):
            chapter = None
        m = ROW_RE.match(line)
        if not m:
            continue
        rid, name, link_cell, link_status, group = m.groups()
        lm = LINK_RE.search(link_cell)
        rows.append({
            "id": rid.strip(),
            "name": name.strip(),
            "link": lm.group(1) if lm else None,
            "link_status": link_status.strip(),
            "group_listed": group.strip(),
            "chapter_heading": chapter,
            "kind": "SUPER_PAIR",
            "source": f"index:L{lineno}",
        })
    return rows


def load_inventory(index_path: Path = INDEX_PATH, additions_path: Path = ADDITIONS_PATH):
    raw = index_path.read_bytes()
    rows = parse_index(raw.decode("utf-8"))
    add = json.loads(additions_path.read_text("utf-8"))
    excluded = {e["id"]: e["reason"] for e in add.get("excluded_from_active", [])}
    for r in add["records"]:
        rows.append({**r, "link_status": "REVIEW", "group_listed": None,
                     "chapter_heading": None})
    provenance = {
        "index": {**INDEX_SOURCE, "sha256": sha256_bytes(raw), "rows": len(parse_index(raw.decode("utf-8")))},
        "additions": {"sha256": sha256_bytes(additions_path.read_bytes()), "rows": len(add["records"]),
                      "source_urls": add.get("source_urls", [])},
    }
    return rows, excluded, provenance


def check_inventory(rows: list[dict], excluded: dict[str, str]) -> dict:
    """Trả về findings + danh sách bản ghi hoạt động không trùng."""
    findings, seen, by_page = [], {}, {}
    active = []
    for r in rows:
        rid = r["id"]
        if not ID_RE.match(rid):
            findings.append({"code": "ID_OUTSIDE_0_9", "severity": "HIGH", "id": rid, "source": r["source"],
                             "detail": "ID phải chỉ gồm chữ số 0–9"})
            continue
        first = rid[0]
        if rid in seen:
            findings.append({"code": "ID_DUPLICATE", "severity": "HIGH", "id": rid,
                             "source": f"{seen[rid]['source']} + {r['source']}",
                             "detail": "Trùng ID (so khớp chuỗi chính xác); không cộng trùng, chờ REVIEW"})
            continue
        seen[rid] = r
        if r.get("chapter_heading") is not None and r["chapter_heading"] != first:
            findings.append({"code": "CHAPTER_MISMATCH", "severity": "MEDIUM", "id": rid, "source": r["source"],
                             "detail": f"Nằm dưới Chương {r['chapter_heading']} nhưng chữ số đầu là {first}"})
        expected = CHAPTER_GROUP[first]
        if r.get("group_listed") and r["group_listed"] != expected:
            findings.append({"code": "GROUP_MISMATCH", "severity": "MEDIUM", "id": rid, "source": r["source"],
                             "detail": f"Nhóm ghi {r['group_listed']} ≠ Nhóm theo Chương {first} là {expected}"})
        if not r.get("link"):
            findings.append({"code": "LINK_MISSING", "severity": "LOW", "id": rid, "source": r["source"],
                             "detail": "Chưa định vị Link hồ sơ; không kết luận hồ sơ không tồn tại"})
        pid = notion_page_id(r.get("link"))
        if pid:
            by_page.setdefault(pid, []).append(rid)
        if rid in excluded:
            findings.append({"code": "EXCLUDED_FROM_ACTIVE", "severity": "INFO", "id": rid, "source": r["source"],
                             "detail": excluded[rid]})
            continue
        active.append(r)
    for pid, ids in by_page.items():
        if len(ids) > 1:
            findings.append({"code": "LINK_SHARED", "severity": "MEDIUM", "id": ",".join(ids), "source": pid,
                             "detail": "Nhiều ID cùng trỏ một trang Notion; cần REVIEW để tránh trùng Link Mẫu"})
    per_chapter = {str(d): 0 for d in range(10)}
    per_group = {"000": 0, "135": 0, "246": 0, "789": 0}
    for r in active:
        per_chapter[r["id"][0]] += 1
        per_group[CHAPTER_GROUP[r["id"][0]]] += 1
    return {
        "rows_read": len(rows),
        "unique_ids": len(seen),
        "active": active,
        "per_chapter": per_chapter,
        "per_group": per_group,
        "chapters_covered": sorted(k for k, v in per_chapter.items() if v),
        "findings": findings,
    }


# ---------------------------------------------------------------- planning

def identity_of(r: dict) -> dict:
    return {"id": r["id"], "name": r["name"], "link": r.get("link"),
            "chapter": r["id"][0], "group": CHAPTER_GROUP[r["id"][0]]}


def build_overlay(r: dict, platforms: list[dict]) -> dict:
    ident = identity_of(r)
    trio = []
    for order, (key, label) in enumerate(TRIO_ORDER, 1):
        status = STATUS_NOT_VERIFIED
        lead = None
        if r.get("kind") == "TRIO_LEAD" and r.get("trio_role") == key:
            lead = "SELF"
        trio.append({"order": order, "key": key, "label": label, "capability_status": status,
                     "lead": lead, "evidence": []})
    return {
        "schema": "cfp87788.overlay.v1",
        "identity": ident,
        "identity_sha256": sha256_bytes(canon(ident)),
        "kind": r.get("kind", "SUPER_PAIR"),
        "source": r.get("source"),
        "upgrade": "SUPER_PAIR→SUPER_TRIO",
        "trio": trio,
        "platforms": [{"key": p["key"], "mode": p["mode"], "status": "NOT ASSESSED"}
                      for p in sorted(platforms, key=lambda p: p["order"])],
        "principles": "3 Trong 1 • Một ID • Một Link Mẫu • Chung Kho Tri Thức",
        "governance": "SANDBOX • HOLD ACTIVATION • PRODUCTION NO-GO • chờ 87783 review và Human Governance",
    }


def guard_overlay(ov: dict, inventory_by_id: dict[str, dict]) -> None:
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if k.lower() in FORBIDDEN_KEYS:
                    raise GuardError(f"Trường bị cấm '{path}{k}': overlay không được đụng Parent/DID/Canonical/Registry/Production")
                walk(v, f"{path}{k}.")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}{i}.")
    walk(ov)
    ident = ov["identity"]
    src = inventory_by_id.get(ident["id"])
    if src is None:
        raise GuardError(f"ID {ident['id']} không có trong kiểm kê: không được tự cấp ID")
    if identity_of(src) != ident:
        raise GuardError(f"Danh tính ID {ident['id']} bị thay đổi so với nguồn")
    if ov["identity_sha256"] != sha256_bytes(canon(ident)):
        raise GuardError(f"identity_sha256 sai cho ID {ident['id']}")
    for t in ov["trio"]:
        if t["capability_status"] != STATUS_NOT_VERIFIED and not t["evidence"]:
            raise GuardError(f"ID {ident['id']}: khai báo năng lực '{t['key']}' khi chưa có Evidence")
    if [t["key"] for t in ov["trio"]] != [k for k, _ in TRIO_ORDER]:
        raise GuardError(f"ID {ident['id']}: sai thứ tự Siêu Bộ Tam")


def make_plan(active: list[dict], platforms: list[dict]) -> dict:
    by_id = {r["id"]: r for r in active}
    items = []
    for r in sorted(active, key=lambda r: (r["id"][0], len(r["id"]), r["id"])):
        ov = build_overlay(r, platforms)
        guard_overlay(ov, by_id)
        items.append({"id": r["id"], "overlay": ov, "overlay_sha256": sha256_bytes(canon(ov))})
    plan = {"schema": "cfp87788.plan.v1", "count": len(items), "items": items}
    plan["plan_sha256"] = sha256_bytes(canon([(i["id"], i["overlay_sha256"]) for i in items]))
    return plan


# ---------------------------------------------------------------- apply / rollback

def _safe_out(out: Path) -> Path:
    out = out.resolve()
    if os.environ.get("CFP_PRODUCTION"):
        raise GuardError("CFP_PRODUCTION được đặt: bộ công cụ này chỉ chạy sandbox")
    if HERE not in out.parents and out != HERE:
        # cho phép thư mục tạm khi test
        tmp = Path(tempfile.gettempdir()).resolve()
        if tmp not in out.parents:
            raise GuardError(f"Thư mục ghi {out} nằm ngoài sandbox 87788")
    return out


def _journal(out: Path, entry: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "journal.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_journal(out: Path) -> list[dict]:
    p = out / "journal.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]


def apply_plan(plan: dict, out: Path, batch_size: int, batch: int, run_id: str | None = None,
               _crash_after: int | None = None) -> dict:
    out = _safe_out(out)
    recover(out)  # luôn dọn lần chạy dở trước
    items = plan["items"][batch * batch_size:(batch + 1) * batch_size]
    run_id = run_id or f"run-{int(time.time())}-{plan['plan_sha256'][:8]}-b{batch}"
    _journal(out, {"op": "begin", "run": run_id, "plan": plan["plan_sha256"], "batch": batch,
                   "ids": [i["id"] for i in items]})
    written, skipped = [], []
    for n, item in enumerate(items):
        target = out / "overlays" / f"{item['id']}.json"
        data = canon(item["overlay"]) + b"\n"
        if target.exists():
            cur = target.read_bytes()
            if cur == data:
                skipped.append(item["id"])
                continue
            existing = json.loads(cur)
            if existing.get("identity", {}).get("id") != item["id"]:
                raise GuardError(f"Tệp {target.name} chứa ID khác: không ghi đè")
            atomic_write(out / "backups" / run_id / target.name, cur)
            _journal(out, {"op": "backup", "run": run_id, "id": item["id"]})
        _journal(out, {"op": "write", "run": run_id, "id": item["id"], "sha256": sha256_bytes(data),
                       "created": not (out / "backups" / run_id / target.name).exists()})
        atomic_write(target, data)
        written.append(item["id"])
        if _crash_after is not None and len(written) >= _crash_after:
            raise KeyboardInterrupt("mô phỏng sự cố giữa chừng")
    _write_manifest(out)
    _journal(out, {"op": "commit", "run": run_id, "written": written, "skipped": skipped})
    return {"run": run_id, "written": written, "skipped": skipped}


def _write_manifest(out: Path) -> dict:
    files = sorted((out / "overlays").glob("*.json")) if (out / "overlays").exists() else []
    man = {"schema": "cfp87788.manifest.v1",
           "files": {f.name: sha256_bytes(f.read_bytes()) for f in files}}
    atomic_write(out / "manifest.json", canon(man) + b"\n")
    return man


def rollback(out: Path, run_id: str) -> list[str]:
    out = _safe_out(out)
    entries = [e for e in read_journal(out) if e.get("run") == run_id]
    if not entries:
        raise GuardError(f"Không thấy lần chạy {run_id}")
    restored = []
    for e in reversed([e for e in entries if e["op"] == "write"]):
        target = out / "overlays" / f"{e['id']}.json"
        backup = out / "backups" / run_id / f"{e['id']}.json"
        if backup.exists():
            atomic_write(target, backup.read_bytes())
        elif target.exists():
            target.unlink()
        restored.append(e["id"])
    _write_manifest(out)
    _journal(out, {"op": "rollback", "run": run_id, "ids": restored})
    return restored


def recover(out: Path) -> list[str]:
    """Hoàn tác mọi lần chạy có 'begin' mà không có 'commit' hay 'rollback'."""
    entries = read_journal(out)
    closed = {e["run"] for e in entries if e["op"] in ("commit", "rollback")}
    open_runs = []
    for e in entries:
        if e["op"] == "begin" and e["run"] not in closed and e["run"] not in open_runs:
            open_runs.append(e["run"])
    for r in open_runs:
        rollback(out, r)
    return open_runs


def verify(out: Path, plan: dict) -> dict:
    out = _safe_out(out)
    man = json.loads((out / "manifest.json").read_text("utf-8"))
    expected = {i["id"]: i for i in plan["items"]}
    by_id = {i["id"]: i["overlay"]["identity"] for i in plan["items"]}
    res = {"checked": 0, "hash_ok": 0, "identity_ok": 0, "matches_plan": 0, "problems": []}
    for name, digest in man["files"].items():
        f = out / "overlays" / name
        res["checked"] += 1
        b = f.read_bytes()
        if sha256_bytes(b) == digest:
            res["hash_ok"] += 1
        else:
            res["problems"].append(f"{name}: hash lệch manifest")
        ov = json.loads(b)
        rid = ov["identity"]["id"]
        if by_id.get(rid) == ov["identity"]:
            res["identity_ok"] += 1
        else:
            res["problems"].append(f"{name}: danh tính khác nguồn")
        if rid in expected and sha256_bytes(canon(ov)) == expected[rid]["overlay_sha256"]:
            res["matches_plan"] += 1
    return res


# ---------------------------------------------------------------- packs (manual import)

PACK_TEAMS = ("8778", "87728", "87783", "87788")
PACK_PLATFORMS = ("chatgpt_codex", "claude_code", "gemini")


def render_pack(rec: dict, platform: dict) -> str:
    return f"""# Gói cấu hình nhập thủ công • {rec['id']} • {rec['name']} • {platform['name']}

**Trạng thái:** DRAFT • NHẬP THỦ CÔNG • chưa tạo Agent • chưa kiểm chứng runtime.
Chế độ nền tảng: `{platform['mode']}` ({platform['official_surface']}; {platform['claim_status']}).

## Danh tính (không đổi)
- ID: `{rec['id']}` • Tên: {rec['name']}
- Link Mẫu: {rec.get('link') or 'PENDING'}
- Chương {rec['id'][0]} • Nhóm {CHAPTER_GROUP[rec['id'][0]]}

## Instructions (dán vào ô hướng dẫn của nền tảng)
Bạn là trợ lý của hồ sơ CFP+ ID {rec['id']} • {rec['name']}, thuộc Siêu Bộ Tam theo thứ tự:
1. Siêu Lượng Tử ⚛️ Super Quantum • 2. SI 🤖 AI 🤖 • 3. Siêu Phần Mềm • Super Software.
3 Trong 1 • Một ID • Một Link Mẫu • Chung Kho Tri Thức.
- Không tự cấp ID, không đổi Parent, DID, Registry hay Canonical.
- Không khai báo năng lực chưa có Evidence; ghi NOT VERIFIED.
- Mỗi kết quả trả về: TASK • ACK thật • RESULT • SHA/URL Evidence • REVIEWER (87783) • BLOCKER.
- Không merge, không deploy Production, không xử lý secret. HOLD ACTIVATION • PRODUCTION NO-GO.
- Điều phối qua HUB 69 (https://cfp.plus/69) và GitHub charityfundplus/CFP.plus.

## Sau khi nhập
Ghi vào Link Mẫu {rec['id']}: URL thực của Agent, quyền đã cấp, ACK, READ/WRITE/READBACK, người kiểm tra.
Chưa có các mục này thì Agent vẫn là NOT VERIFIED.
"""


def make_packs(active: list[dict], platforms: list[dict], out: Path) -> list[str]:
    out = _safe_out(out)
    by_id = {r["id"]: r for r in active}
    pk = {p["key"]: p for p in platforms}
    made = []
    for tid in PACK_TEAMS:
        if tid not in by_id:
            raise GuardError(f"Thiếu hồ sơ {tid} trong kiểm kê")
        for pkey in PACK_PLATFORMS:
            path = out / "packs" / f"{tid}-{pkey}.md"
            atomic_write(path, render_pack(by_id[tid], pk[pkey]).encode("utf-8"))
            made.append(str(path.relative_to(out)))
    return made


# ---------------------------------------------------------------- evidence

def build_evidence(inv: dict, plan: dict, provenance: dict, ver: dict | None, platforms: list[dict]) -> dict:
    counts = {}
    for f in inv["findings"]:
        counts[f["code"]] = counts.get(f["code"], 0) + 1
    return {
        "schema": "cfp87788.evidence.v1",
        "provenance": provenance,
        "inventory": {k: inv[k] for k in ("rows_read", "unique_ids", "per_chapter", "per_group", "chapters_covered")},
        "active_count": len(inv["active"]),
        "finding_counts": counts,
        "findings": inv["findings"],
        "plan_sha256": plan["plan_sha256"],
        "plan_count": plan["count"],
        "verify": ver,
        "capability_status": {k: {STATUS_NOT_VERIFIED: plan["count"]} for k, _ in TRIO_ORDER},
        "platforms": [{"key": p["key"], "mode": p["mode"], "session_check": p["session_check"]} for p in platforms],
        "status": "SANDBOX • REVIEW CANDIDATE • HOLD ACTIVATION • PRODUCTION NO-GO",
    }


def render_report(ev: dict) -> str:
    inv = ev["inventory"]
    lines = [
        "# 87788 • Siêu Bộ Tam • Evidence kiểm kê và nâng cấp (sandbox)",
        "",
        f"**Trạng thái:** {ev['status']}",
        "",
        "## Nguồn",
        f"- Bảng 91 vị trí: `{ev['provenance']['index']['repo']}` PR #{ev['provenance']['index']['pr']} @ "
        f"`{ev['provenance']['index']['commit']}` • `{ev['provenance']['index']['path']}` • "
        f"sha256 `{ev['provenance']['index']['sha256']}` • {ev['provenance']['index']['rows']} dòng",
        f"- Bổ sung từ Notion: {ev['provenance']['additions']['rows']} bản ghi • sha256 "
        f"`{ev['provenance']['additions']['sha256']}`",
        "",
        "## Kiểm kê",
        f"- Dòng đọc: {inv['rows_read']} • ID không trùng: {inv['unique_ids']} • hoạt động (sau loại trừ): {ev['active_count']}",
        f"- Chương có bản ghi: {', '.join(inv['chapters_covered'])} (đủ 0–9: {'CÓ' if len(inv['chapters_covered']) == 10 else 'KHÔNG'})",
        "- Theo Chương: " + " • ".join(f"{k}: {v}" for k, v in inv["per_chapter"].items()),
        "- Theo Nhóm: " + " • ".join(f"{k}: {v}" for k, v in inv["per_group"].items()),
        "",
        "Đây là số đếm từ hai nguồn trên, không phải tổng Registry. TỔNG HIỆN TẠI CHƯA XÁC MINH.",
        "",
        "## Phát hiện",
        "",
        "| Mã | Mức | ID | Nguồn | Chi tiết |",
        "| --- | --- | --- | --- | --- |",
    ]
    for f in ev["findings"]:
        lines.append(f"| {f['code']} | {f['severity']} | `{f['id']}` | {f['source']} | {f['detail']} |")
    lines += [
        "",
        "## Kế hoạch nâng cấp",
        f"- {ev['plan_count']} lớp phủ Siêu Bộ Tam • plan sha256 `{ev['plan_sha256']}`",
        "- Năng lực 3 trụ cột: tất cả NOT VERIFIED (không khai báo khi chưa có Evidence).",
    ]
    if ev["verify"]:
        v = ev["verify"]
        lines.append(f"- Readback sandbox: {v['checked']} tệp • hash khớp {v['hash_ok']} • danh tính khớp "
                     f"{v['identity_ok']} • khớp kế hoạch {v['matches_plan']} • vấn đề {len(v['problems'])}")
    lines += ["", "## Nền tảng (kiểm tra thực tế trong phiên)", "", "| Nền tảng | Chế độ | Kiểm tra |", "| --- | --- | --- |"]
    for p in ev["platforms"]:
        lines.append(f"| {p['key']} | {p['mode']} | {p['session_check']} |")
    lines += ["", "Không merge • không deploy • không đổi ID/Parent/DID/Registry/Canonical. Chờ 87783 review và Human Governance.", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI

def _load_all():
    rows, excluded, prov = load_inventory()
    inv = check_inventory(rows, excluded)
    platforms = json.loads(PLATFORMS_PATH.read_text("utf-8"))["platforms"]
    plan = make_plan(inv["active"], platforms)
    return inv, plan, prov, platforms


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("plan")
    a = sub.add_parser("apply")
    a.add_argument("--batch-size", type=int, default=10)
    a.add_argument("--batch", type=int, default=0)
    a.add_argument("--all", action="store_true")
    sub.add_parser("verify")
    r = sub.add_parser("rollback")
    r.add_argument("run_id")
    sub.add_parser("recover")
    sub.add_parser("packs")
    e = sub.add_parser("evidence")
    e.add_argument("--dir", type=Path, default=HERE / "evidence")
    args = ap.parse_args(argv)

    inv, plan, prov, platforms = _load_all()
    if args.cmd == "check":
        print(json.dumps({k: v for k, v in inv.items() if k != "active"}, ensure_ascii=False, indent=2))
        return 1 if any(f["severity"] == "HIGH" for f in inv["findings"]) else 0
    if args.cmd == "plan":
        print(json.dumps({"plan_sha256": plan["plan_sha256"], "count": plan["count"],
                          "ids": [i["id"] for i in plan["items"]]}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "apply":
        n_batches = (plan["count"] + args.batch_size - 1) // args.batch_size
        batches = range(n_batches) if args.all else [args.batch]
        for b in batches:
            print(json.dumps(apply_plan(plan, args.out, args.batch_size, b), ensure_ascii=False))
        return 0
    if args.cmd == "verify":
        v = verify(args.out, plan)
        print(json.dumps(v, ensure_ascii=False, indent=2))
        return 0 if not v["problems"] and v["checked"] == v["matches_plan"] else 1
    if args.cmd == "rollback":
        print(json.dumps(rollback(args.out, args.run_id)))
        return 0
    if args.cmd == "recover":
        print(json.dumps(recover(_safe_out(args.out))))
        return 0
    if args.cmd == "packs":
        print("\n".join(make_packs(inv["active"], platforms, args.out)))
        return 0
    if args.cmd == "evidence":
        ver = verify(args.out, plan) if (args.out / "manifest.json").exists() else None
        ev = build_evidence(inv, plan, prov, ver, platforms)
        d = _safe_out(args.dir)
        atomic_write(d / "evidence.json", json.dumps(ev, ensure_ascii=False, indent=2, sort_keys=True).encode() + b"\n")
        atomic_write(d / "REPORT.md", render_report(ev).encode("utf-8"))
        print(f"{d/'evidence.json'}\n{d/'REPORT.md'}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
