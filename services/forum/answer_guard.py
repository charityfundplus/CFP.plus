"""Siêu Phần Mềm • Giám sát câu trả lời tư vấn khách hàng (dùng cho mọi Agent: Meta Business Agent, SI AI…).

Nguyên tắc (lệnh "META BUSINESS AGENT" • TRAINING • REVIEW • AUTO REPLY HOLD • PRODUCTION NO-GO):
  • Chỉ KIỂM TRA bản nháp; không gửi trả lời cho khách. `auto_reply` luôn là "HOLD": một người phụ trách phải
    duyệt trước khi gửi, cho đến khi có HUMAN APPROVAL cho production.
  • Mọi ID/link cfp.plus phải là trang ID số ĐÃ XUẤT BẢN (Link Mẫu); ID lạ → chặn (không tự cấp ID).
  • ID đang HOLD (review-holding) → chặn; Parent đang HOLD → cảnh báo.
  • Không tuyên bố chức năng đang xây dựng/kế hoạch là đã hoạt động.
  • Cam kết tài chính, pháp lý hoặc đại diện CFP+ → chuyển cho con người.
  • Hỏi mật khẩu/OTP/số thẻ/giấy tờ tuỳ thân → chặn.
Chỉ trả về kết quả kiểm tra; không lưu nội dung câu hỏi/câu trả lời (có thể chứa dữ liệu của khách hàng).
"""
from __future__ import annotations

import hashlib
import re

from services.forum.catalog import fold

# ID trong link chuẩn https://cfp.plus/{ID} hoặc dạng "ID 12345".
_LINK_ID = re.compile(r"cfp\.plus/([0-9]{1,32})(?![0-9])", re.I)
_WORD_ID = re.compile(r"\bID\s*(?:số\s*)?:?\s*([0-9]{2,32})\b", re.I)
_SENT = re.compile(r"(?<=[.!?\n])\s+")

# Thành phần CHƯA được kiểm chứng là đang phục vụ người dùng thật (theo MODULES/PENDING của Link Mẫu + lệnh NO-GO).
NOT_LIVE = ("app", "san tmtc", "tmtc", "3366", "quantum", "gen z", "giao trinh", "voice", "da ngon ngu",
            "sieu phan mem", "meta business agent", "production", "dien dan")
CLAIM_LIVE = ("da hoat dong", "dang hoat dong", "da van hanh", "dang van hanh", "da ra mat", "da trien khai",
              "san sang phuc vu", "da hoan thanh", "co the su dung ngay", "is live", "now available", "is available",
              "fully operational", "launched")
# Cam kết tài chính / pháp lý / đại diện → con người quyết định.
# (không dùng "lợi nhuận"/"pháp lý" đơn lẻ: CFP+ thường viết "phi lợi nhuận", "pháp lý và minh bạch")
COMMIT = ("cam ket", "bao dam", "dam bao loi nhuan", "lai suat", "hoan tien", "hop dong",
          "thay mat cfp", "dai dien cfp", "chung toi dong y tai tro", "se tai tro", "se chuyen tien",
          "guarantee", "refund", "we promise", "on behalf of cfp", "contract", "investment return")
# Dữ liệu nhạy cảm không được hỏi khách.
SENSITIVE = ("mat khau", "password", "otp", "so the", "ma pin", "cvv", "cccd", "cmnd", "ho chieu", "so tai khoan",
             "seed phrase", "private key")


def _sentences(text: str) -> list[str]:
    return [s for s in _SENT.split(text) if s.strip()]


def check_answer(draft: str, catalog, question: str | None = None) -> dict:
    """Trả về verdict + findings + citations. verdict: block > needs_human > ready_for_human_review."""
    findings: list[dict] = []
    ids = list(dict.fromkeys(_LINK_ID.findall(draft) + _WORD_ID.findall(draft)))
    citations = []
    for cid in ids:
        it = catalog.items.get(cid) if catalog is not None else None
        if not it:
            findings.append({"level": "block", "code": "unknown_id", "id": cid,
                             "message": f"ID {cid} chưa có trang đã xuất bản — không được đưa cho khách (không tự cấp ID)."})
            continue
        citations.append({"id": cid, "url": it["canonical_url"], "title": it["title"], "version": it["version"],
                          "parent_status": it["parent_status"]})
        if it["parent_status"] == "hold_conflict":
            findings.append({"level": "block", "code": "hold_id", "id": cid, "source": it["hold"]["source"],
                             "message": f"ID {cid} đang HOLD (xung đột Registry) — không giới thiệu như ID đã xác minh."})
        elif it["parent_status"] == "parent_hold":
            findings.append({"level": "warn", "code": "parent_hold", "id": cid,
                             "message": f"Parent {it['hold']['parent']} của ID {cid} đang HOLD — ghi rõ 'đang xác minh'."})
    for s in _sentences(draft):
        f = fold(s)
        hits = [t for t in NOT_LIVE if re.search(rf"\b{re.escape(t)}\b", f)]
        if hits and any(c in f for c in CLAIM_LIVE):
            findings.append({"level": "block", "code": "claim_unverified", "terms": hits, "sentence": s.strip()[:200],
                             "message": "Tuyên bố chức năng đang xây dựng/kế hoạch là đã hoạt động — chưa có Evidence."})
        if any(c in f for c in COMMIT):
            findings.append({"level": "needs_human", "code": "commitment", "sentence": s.strip()[:200],
                             "message": "Cam kết tài chính/pháp lý/đại diện CFP+ — chuyển người phụ trách."})
        if any(re.search(rf"\b{re.escape(t)}\b", f) for t in SENSITIVE):
            findings.append({"level": "block", "code": "sensitive_request", "sentence": s.strip()[:200],
                             "message": "Không hỏi/nhận mật khẩu, OTP, số thẻ, giấy tờ tuỳ thân qua tư vấn."})
    if question and any(c in fold(question) for c in COMMIT):
        findings.append({"level": "needs_human", "code": "commitment_question",
                         "message": "Câu hỏi liên quan tài chính/pháp lý/hợp tác chính thức — người phụ trách trả lời."})
    if not citations:
        findings.append({"level": "warn", "code": "no_source",
                         "message": "Không có link nguồn cfp.plus/{ID} đã xuất bản — thêm nguồn để khách kiểm chứng."})
    levels = {x["level"] for x in findings}
    verdict = "block" if "block" in levels else "needs_human" if "needs_human" in levels else "ready_for_human_review"
    return {"verdict": verdict, "auto_reply": "HOLD", "findings": findings, "citations": citations,
            "draft_sha256": hashlib.sha256(draft.encode()).hexdigest()[:16]}
