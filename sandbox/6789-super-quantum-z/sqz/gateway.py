"""Kết nối CFP+ Gateway (cfp-gateway): tra ID Số Sống và DID, định dạng CMP Work Order.

- Tra ID qua `GET {SQZ_GATEWAY_URL}/api/id/{id}` (API có sẵn của cfp-gateway).
- Không bịa DID: chỉ trả DID khi Gateway/Registry cung cấp; nếu không ghi `NOT_ASSIGNED`.
- Gateway lỗi hoặc chưa cấu hình → kết quả `LOCAL_FORMAT_ONLY` (chỉ kiểm định dạng),
  không coi là đã xác minh.
"""

from __future__ import annotations

import os

import httpx

from .ids import classify

TIMEOUT_S = 5.0
# Trường CMP Work Order của cfp-gateway (main.WorkOrder).
GATEWAY_WORK_ORDER_FIELDS = {"work_order_id", "source", "target", "task", "payload", "required_capability"}


def resolve_id(cfp_id: str, base_url: str | None = None, client: httpx.Client | None = None) -> dict:
    info = classify(cfp_id)
    base = (base_url or os.getenv("SQZ_GATEWAY_URL") or "").rstrip("/")
    out = {**info, "did": None, "did_status": "NOT_ASSIGNED", "registry": None}
    if not base:
        return {**out, "verification": "LOCAL_FORMAT_ONLY", "reason": "SQZ_GATEWAY_URL chưa cấu hình"}
    http = client or httpx.Client(timeout=TIMEOUT_S)
    try:
        r = http.get(f"{base}/api/id/{cfp_id}")
    except httpx.HTTPError as exc:
        return {**out, "verification": "LOCAL_FORMAT_ONLY", "reason": f"Gateway lỗi: {type(exc).__name__}"}
    finally:
        if client is None:
            http.close()
    if r.status_code == 404:
        return {**out, "verification": "GATEWAY_NOT_FOUND"}
    if r.status_code != 200:
        return {**out, "verification": "LOCAL_FORMAT_ONLY", "reason": f"Gateway HTTP {r.status_code}"}
    try:
        rec = r.json()
    except ValueError:
        return {**out, "verification": "LOCAL_FORMAT_ONLY", "reason": "Gateway trả JSON không hợp lệ"}
    if not isinstance(rec, dict) or rec.get("id") != cfp_id:
        return {**out, "verification": "LOCAL_FORMAT_ONLY", "reason": "Gateway trả ID không khớp"}
    did = rec.get("did")
    if did is not None and not isinstance(did, str):
        return {**out, "verification": "LOCAL_FORMAT_ONLY", "reason": "Gateway trả DID sai kiểu"}
    return {**out, "registry": rec, "verification": "GATEWAY_VERIFIED",
            "did": did, "did_status": "ASSIGNED" if did else "NOT_ASSIGNED"}


def to_gateway_work_order(job: dict) -> dict:
    """Chuyển Job sang Work Order đúng trường của cfp-gateway để chuyển tiếp qua CMP."""
    return {"work_order_id": f"sqz-{job['id']}", "source": "6789-SQZ", "target": job["owner_id"],
            "task": job["kind"], "payload": {"job_id": job["id"], "status": job["status"],
                                             "result": job.get("result")},
            "required_capability": None}
