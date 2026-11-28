"""Validator ID Số Sống CFP+ • Work Order MCP-DDB8FF1A5BD9 (6776).

CHỈ áp dụng các quy tắc đã ghi trong Mẫu Chung 366 (mục "Kiến trúc ID Số Sống 0–9",
chỉ đạo 26–27/11/2026). Không tự suy diễn quy tắc chưa xác minh; phần chưa xác minh
được trả về dưới dạng `pending`, không thành lỗi hay đạt.

Quy tắc đã xác minh (trích nguồn):
  R1 Chỉ chữ số 0–9; mỗi chữ số là một nhánh 0–9 tại một cấp. "10" là tổ hợp hai chữ số
     1 và 0 (hai cấp), không phải nhánh thứ 10 hay Chương 10.
  R2 Lưu dạng chuỗi, bảo toàn số 0 đầu ("0", "00", "000" là ba ID khác nhau).
  R3 Chữ số đầu xác định Chương; 5 Nhóm: D • V | 000 | 135 | 246 | 789.
  R4 MMDD (tháng trước, ngày sau) là khóa quy hoạch 366 ngày, gồm 0229; DDMM cũ chỉ là
     lịch sử, không dùng để tạo mới. Năm không nhuận không có Daily Record 29/02.
  R5 Mười chức năng 0–9: 0 Đón Nhận … 9 Phục Vụ; không dùng nhãn 10.
  R6 Kiểm tra cú pháp không thay thế kiểm tra nghiệp vụ và Registry → `registry` luôn
     là PENDING khi chưa đối chiếu nguồn Registry.
"""

from __future__ import annotations

import calendar
import hashlib
import json
from datetime import date

from .ids import CHAPTER_GROUP

FUNCTIONS = {"0": "Đón Nhận", "1": "Xác Thực", "2": "Kiểm Chứng", "3": "Phân Loại", "4": "Nghiên Cứu",
             "5": "Tích Hợp", "6": "Tích Lũy", "7": "Chia Sẻ", "8": "Nâng Tầm", "9": "Phục Vụ"}
GATE_GROUPS = ("D", "V")  # Nhóm cổng quản trị/điều hướng, không phải ID Số
SOURCE = "https://app.notion.com/p/424caac9a557812aa0b4cc4f64e89008"
MONTH_DAYS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # tổng 366


def mmdd_keys() -> list[str]:
    return [f"{m:02d}{d:02d}" for m in range(1, 13) for d in range(1, MONTH_DAYS[m - 1] + 1)]


MMDD = frozenset(mmdd_keys())


def is_mmdd(key: str) -> bool:
    return isinstance(key, str) and key in MMDD


def daily_record_allowed(key: str, year: int) -> bool:
    """R4: Daily Record chỉ hợp lệ nếu ngày có thật trong năm đó (0229 chỉ năm nhuận)."""
    if not is_mmdd(key):
        return False
    return not (key == "0229" and not calendar.isleap(year))


def mmdd_for(d: date) -> str:
    return f"{d.month:02d}{d.day:02d}"


def validate(cfp_id, *, as_mmdd: bool = False) -> dict:
    errors, warnings, pending = [], [], []
    if not isinstance(cfp_id, str):
        errors.append("R2: ID phải là chuỗi (số nguyên làm mất số 0 đầu)")
        return {"id": cfp_id, "valid": False, "errors": errors, "warnings": warnings, "pending": pending}
    if cfp_id in GATE_GROUPS:
        return {"id": cfp_id, "valid": True, "kind": "GATE_GROUP", "errors": [], "warnings": [],
                "pending": ["registry: PENDING"], "source": SOURCE}
    if not cfp_id or not cfp_id.isascii() or not cfp_id.isdigit():
        errors.append("R1: chỉ gồm chữ số 0–9")
    if errors:
        return {"id": cfp_id, "valid": False, "errors": errors, "warnings": warnings, "pending": pending}
    levels = [{"level": i + 1, "branch": ch, "prefix": cfp_id[: i + 1]} for i, ch in enumerate(cfp_id)]
    out = {
        "id": cfp_id, "valid": True, "kind": "ID_SO", "depth": len(cfp_id),
        "chapter": cfp_id[0], "group": CHAPTER_GROUP[cfp_id[0]], "levels": levels,
        # Parent theo cấu trúc số là "dự kiến" (vd. 87728 → 8772) trong hồ sơ hiện hữu; chưa chốt.
        "structural_parent": cfp_id[:-1] or None,
        "leading_zeros": len(cfp_id) - len(cfp_id.lstrip("0")),
        "errors": errors, "warnings": warnings, "pending": pending, "source": SOURCE,
    }
    pending.append("structural_parent: DỰ KIẾN, chờ Registry chốt Parent")
    pending.append("registry: PENDING (R6, chưa đối chiếu)")
    if len(cfp_id) == 4:
        out["mmdd"] = is_mmdd(cfp_id)
        if as_mmdd and not out["mmdd"]:
            dd, mm = cfp_id[:2], cfp_id[2:]
            if f"{mm}{dd}" in MMDD:
                errors.append(f"R4: {cfp_id} giống định dạng DDMM cũ; MMDD đúng là {mm}{dd}")
            else:
                errors.append(f"R4: {cfp_id} không phải MMDD hợp lệ")
        elif out["mmdd"]:
            dd, mm = cfp_id[:2], cfp_id[2:]
            if f"{mm}{dd}" in MMDD and mm + dd != cfp_id:
                warnings.append(f"R4: {cfp_id} cũng đọc được theo DDMM cũ ({mm}{dd}); dùng nghĩa MMDD")
    elif as_mmdd:
        errors.append("R4: khóa MMDD phải đúng 4 chữ số")
    out["valid"] = not errors
    return out


# ---------------------------------------------------------------- kiêm nhiệm • chống trùng
def record_key(record: dict) -> str:
    """Khóa idempotency ổn định của một bản ghi gán vai (không phụ thuộc thứ tự trường)."""
    norm = {"id": record["id"], "role": record.get("role", "").strip().lower(),
            "context": str(record.get("context", "")).strip()}
    return hashlib.sha256(json.dumps(norm, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def check_assignments(records: list[dict]) -> dict:
    """Kiểm tra danh sách gán vai: ID hợp lệ, kiêm nhiệm được phép, phát hiện bản trùng và
    xung đột tên (cùng ID mà khác tên ở các nguồn → cần Registry quyết định)."""
    seen: dict[str, int] = {}
    names: dict[str, set] = {}
    roles: dict[str, set] = {}
    invalid, duplicates = [], []
    for i, r in enumerate(records):
        v = validate(r.get("id"))
        if not v["valid"]:
            invalid.append({"index": i, "id": r.get("id"), "errors": v["errors"]})
            continue
        k = record_key(r)
        if k in seen:
            duplicates.append({"index": i, "duplicate_of": seen[k], "id": r["id"], "role": r.get("role")})
            continue
        seen[k] = i
        roles.setdefault(r["id"], set()).add(r.get("role", ""))
        if r.get("name"):
            names.setdefault(r["id"], set()).add(r["name"].strip())
    conflicts = [{"id": i, "names": sorted(n)} for i, n in names.items() if len(n) > 1]
    concurrent = {i: sorted(rs) for i, rs in roles.items() if len(rs) > 1}
    return {"total": len(records), "unique": len(seen), "invalid": invalid, "duplicates": duplicates,
            "name_conflicts": conflicts, "concurrent_roles": concurrent,
            "ok": not invalid and not conflicts}
