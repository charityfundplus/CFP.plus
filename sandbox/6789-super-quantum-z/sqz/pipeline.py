"""Chuỗi tự động: Tiếp nhận → Phân công → Thực thi → Kiểm tra → Bàn giao.

Sau khi Job DONE, `auto_check_and_handover`:
1. 6788 kiểm chứng độc lập (`verify_job`), ghi review bằng danh tính máy `AUTO_6788`
   (khác danh tính đã gửi Job; nếu trùng thì bỏ qua, không tự review).
2. Tạo báo cáo Evidence theo schema 6776 v1, kiểm hợp lệ, ghi audit `HANDOVER`.
Không tự kích hoạt production; trạng thái bàn giao là DONE hoặc NOT_VERIFIED, không VERIFIED
khi chưa có reviewer con người hoặc 87783.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .ops6776 import validate_evidence
from .si6788 import verify_job

AUTO_REVIEWER = "AUTO_6788"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def auto_check_and_handover(store, job_id: str) -> dict:
    job = store.get(job_id)
    if job is None or job["status"] not in ("DONE", "FAILED"):
        return {"handover": False, "reason": "Job chưa kết thúc"}
    v = verify_job(job)
    reviewed = False
    if job["owner_id"] != "6788" and job.get("submitted_by") != AUTO_REVIEWER:
        store.review(job_id, "6788", v["verdict"], f"AUTOMATED • {v['method']} • {v['details']}",
                     reviewer_principal=AUTO_REVIEWER)
        reviewed = True
    status = "DONE" if v["verdict"] == "APPROVED" else ("BLOCKED" if job["status"] == "FAILED" else "NOT_VERIFIED")
    nature = (job.get("result") or {}).get("nature", "SOFTWARE")
    report = {
        "task": f"{job['kind']} • job {job_id}", "owner_id": job["owner_id"],
        "ack": {"by": job["owner_id"], "at": datetime.fromtimestamp(job["created_at"], timezone.utc)
                .isoformat(timespec="seconds")},
        "status": status, "nature": nature if nature != "QPU" else "SOFTWARE",
        "sources": ["https://github.com/charityfundplus/CFP.plus/tree/claude/87788-super-trio-upgrade/"
                    "sandbox/6789-super-quantum-z"],
        "result": f"verdict={v['verdict']} • method={v['method']}",
        "evidence": [{"kind": "job", "ref": job_id}, {"kind": "audit_head", "ref": store.verify_audit()["head"]}],
        "reviewer_id": "6788" if reviewed else None,
        "blockers": [] if status != "BLOCKED" else [job.get("error") or "Job FAILED"],
        "next_action": "87783 review độc lập" if status == "DONE" else "Chủ trì xem lại kết quả",
        "reported_at": _now(),
    }
    check = validate_evidence(report)
    store.audit("pipeline", "HANDOVER", {"job": job_id, "status": status, "evidence_valid": check["valid"]})
    return {"handover": True, "verdict": v["verdict"], "report": report, "evidence_check": check}
