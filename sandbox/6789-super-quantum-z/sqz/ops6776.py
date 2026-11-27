"""6776 • Siêu Phần Mềm: schema Evidence, giám sát cảnh báo sớm, sao lưu và khôi phục.

- `EVIDENCE_SCHEMA` (JSON Schema 2020-12) + `validate_evidence`: chuẩn báo cáo chung cho
  mọi Team (Nhiệm vụ • ACK • Nguồn • Kết quả • Evidence • Sai số • Reviewer • Blocker • Next).
- `watchdog`: kiểm tra trạng thái và sinh cảnh báo theo mức; audit hỏng → đề nghị dừng.
- `backup` / `restore`: xuất và nạp lại toàn bộ dữ liệu, xác minh chuỗi audit sau khôi phục.
"""

from __future__ import annotations

import hashlib
import json
import time

from jsonschema import Draft202012Validator
from datetime import datetime

from sqlalchemy import delete, func, insert, select, text

from .ids import classify
from .store import Store, audit_log, control, heartbeats, jobs, reviews

ID_PATTERN = "^[0-9]{1,12}$"
EVIDENCE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://cfp.plus/schemas/evidence-report-v1.json",
    "title": "CFP+ Evidence Report v1",
    "type": "object",
    "additionalProperties": False,
    "required": ["task", "owner_id", "ack", "status", "nature", "sources", "result", "evidence",
                 "reviewer_id", "blockers", "next_action", "reported_at"],
    "properties": {
        "task": {"type": "string", "minLength": 3, "maxLength": 300},
        "owner_id": {"type": "string", "pattern": ID_PATTERN},
        "ack": {"type": "object", "required": ["by", "at"], "additionalProperties": False,
                "properties": {"by": {"type": "string", "pattern": ID_PATTERN},
                               "at": {"type": "string", "format": "date-time"}}},
        "status": {"enum": ["DONE", "VERIFIED", "IN_PROGRESS", "BLOCKED", "WAITING_HUMAN_GOVERNANCE",
                            "NOT_VERIFIED"]},
        "nature": {"enum": ["CLASSICAL", "QUANTUM_SIMULATION", "HYBRID_SIMULATION", "QPU",
                            "DOCUMENT", "SOFTWARE"]},
        "sources": {"type": "array", "minItems": 1, "items": {"type": "string", "pattern": "^https?://"}},
        "result": {"type": "string", "minLength": 1},
        "evidence": {"type": "array", "minItems": 1,
                     "items": {"type": "object", "required": ["kind", "ref"], "additionalProperties": False,
                               "properties": {"kind": {"enum": ["commit", "ci_run", "url", "job", "audit_head",
                                                                "session"]},
                                              "ref": {"type": "string", "minLength": 4}}}},
        "error_margin": {"type": "string"},
        "reviewer_id": {"type": ["string", "null"], "pattern": ID_PATTERN},
        "blockers": {"type": "array", "items": {"type": "string"}},
        "next_action": {"type": "string"},
        "reported_at": {"type": "string", "format": "date-time"},
    },
    # VERIFIED bắt buộc có reviewer; các luật chéo còn lại kiểm ở validate_evidence.
    "if": {"properties": {"status": {"const": "VERIFIED"}}},
    "then": {"properties": {"reviewer_id": {"type": "string"}}},
}
_VALIDATOR = Draft202012Validator(EVIDENCE_SCHEMA, format_checker=Draft202012Validator.FORMAT_CHECKER)


def validate_evidence(report: dict) -> dict:
    errors = [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in _VALIDATOR.iter_errors(report)]
    if not errors:
        for key in ("owner_id", "reviewer_id"):
            if report.get(key):
                classify(report[key])
        if report.get("reviewer_id") and report["reviewer_id"] == report["owner_id"]:
            errors.append("reviewer_id: phải khác owner_id (kiểm chứng độc lập)")
        if report["status"] == "BLOCKED" and not report["blockers"]:
            errors.append("blockers: BLOCKED phải nêu ít nhất một điểm bị chặn")
        for path in ("reported_at", "ack.at"):
            val = report["ack"]["at"] if path == "ack.at" else report[path]
            try:
                if datetime.fromisoformat(val.replace("Z", "+00:00")).tzinfo is None:
                    errors.append(f"{path}: cần múi giờ (RFC 3339)")
            except ValueError:
                errors.append(f"{path}: không phải date-time RFC 3339")
        if report["nature"] == "QPU":
            errors.append("nature: QPU chưa được Human Governance cho phép trong lõi")
    return {"valid": not errors, "errors": errors, "schema": EVIDENCE_SCHEMA["$id"]}


# ---------------------------------------------------------------- giám sát
def watchdog(store: Store, *, max_queue: int = 100, stale_s: float = 30.0,
             selftest_window: int = 50) -> dict:
    alerts: list[dict] = []

    def alert(level: str, code: str, msg: str) -> None:
        alerts.append({"level": level, "code": code, "message": msg})

    try:
        store.ping()
    except Exception as exc:  # DB mất kết nối
        return {"status": "CRITICAL", "alerts": [{"level": "CRITICAL", "code": "DB_DOWN", "message": str(exc)}],
                "recommend_emergency_stop": False, "checked_at": time.time()}
    audit = store.verify_audit()
    if not audit["ok"]:
        alert("CRITICAL", "AUDIT_BROKEN", f"Chuỗi audit hỏng: {audit}")
    if store.stopped():
        alert("WARNING", "EMERGENCY_STOP_ON", "Emergency Stop đang bật")
    workers = store.workers(stale_s)
    if not any(w["alive"] for w in workers):
        alert("CRITICAL", "NO_LIVE_WORKER", "Không có worker gửi heartbeat trong thời hạn")
    queued = store.counts().get("QUEUED", 0)
    if queued > max_queue:
        alert("WARNING", "QUEUE_BACKLOG", f"{queued} Job đang chờ (> {max_queue})")
    tests = [j for j in store.recent("bell_selftest", selftest_window) if j["status"] in ("DONE", "FAILED")]
    failed = [j for j in tests if j["status"] == "FAILED" or not (j["result"] or {}).get("pass")]
    if failed:
        alert("CRITICAL", "SELFTEST_FAILING", f"{len(failed)}/{len(tests)} Bell self-test gần nhất không đạt")
    level = "CRITICAL" if any(a["level"] == "CRITICAL" for a in alerts) else (
        "WARNING" if alerts else "OK")
    return {"status": level, "alerts": alerts, "workers": len(workers),
            "recommend_emergency_stop": any(a["code"] == "AUDIT_BROKEN" for a in alerts),
            "checked_at": time.time()}


# ---------------------------------------------------------------- sao lưu / khôi phục
TABLES = (jobs, reviews, audit_log, control, heartbeats)


def backup(store: Store) -> dict:
    with store.engine.connect() as c:
        data = {t.name: [dict(r) for r in c.execute(select(t)).mappings()] for t in TABLES}
    body = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"format": "sqz-backup-v1", "created_at": time.time(), "sha256": hashlib.sha256(body.encode()).hexdigest(),
            "tables": data}


def restore(store: Store, snapshot: dict) -> dict:
    """Nạp bản sao lưu vào Store RỖNG (không ghi đè dữ liệu đang có), rồi xác minh."""
    if snapshot.get("format") != "sqz-backup-v1":
        raise ValueError("Định dạng sao lưu không hỗ trợ")
    body = json.dumps(snapshot["tables"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if hashlib.sha256(body.encode()).hexdigest() != snapshot["sha256"]:
        raise ValueError("sha256 không khớp: bản sao lưu bị thay đổi")
    with store.engine.begin() as c:
        if c.execute(select(jobs.c.id).limit(1)).first() or c.execute(select(audit_log.c.seq).limit(1)).first():
            raise PermissionError("Store đích không rỗng: từ chối ghi đè")
        c.execute(delete(control))
        for t in TABLES:
            rows = snapshot["tables"].get(t.name, [])
            if rows:
                c.execute(insert(t), rows)
        if store.backend == "postgresql":  # đồng bộ sequence sau khi chèn khóa tường minh
            for t, col in ((audit_log, "seq"), (reviews, "id")):
                if c.execute(select(func.count()).select_from(t)).scalar():
                    c.execute(text(f"SELECT setval(pg_get_serial_sequence('{t.name}', '{col}'), "
                                   f"(SELECT max({col}) FROM {t.name}))"))
    v = store.verify_audit()
    return {"restored": {t.name: len(snapshot["tables"].get(t.name, [])) for t in TABLES}, "audit": v}
