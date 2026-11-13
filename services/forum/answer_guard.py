"""Siêu Phần Mềm • Giám sát câu trả lời tư vấn khách hàng (dùng cho mọi Agent: Meta Business Agent, SI AI…).

Nguyên tắc (TRAINING • REVIEW • AUTO REPLY HOLD • PRODUCTION NO-GO):
  • Chỉ KIỂM TRA bản nháp; không gửi. `auto_reply` luôn "HOLD" cho tới HUMAN APPROVAL production.
  • Sáu nhóm rủi ro (category): id • link • source • deployment_claim • authority • sensitive.
  • Trạng thái ID tách bạch (id_status):
      UNKNOWN    — không có trang ID số đã xuất bản (không tự cấp ID) ............ chặn
      HOLD       — có hồ sơ HOLD trong registry/review-holding (Registry xác nhận) .. chặn
      PARENT_HOLD— Parent có hồ sơ HOLD ........................................ cảnh báo, ghi "đang xác minh"
      UNVERIFIED — có trang nhưng Parent chưa xác minh / chỉ suy từ tiền tố ....... cảnh báo
      CANDIDATE  — Parent theo Registry (ứng viên review, chưa Canonical Lock) ..... không cảnh báo
  • Knowledge legacy: bảng mapping cũ (HUB69.md • CMP.md • GLOBAL_AI_ID_BASELINE_CANDIDATE.md) chỉ có giá trị
    audit (registry/AI_CANONICAL_ID_REGISTRY.md). Ghép ID với tên theo bảng cũ khác Registry hiện hành → chặn.
Không lưu nội dung bản nháp; chỉ trả kết quả + sha256.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

from services.forum.catalog import REPO_ROOT, fold

GUARD_SOURCE = Path(__file__)
GUARD_VERSION = "sha256:" + hashlib.sha256(GUARD_SOURCE.read_bytes()).hexdigest()[:16]

_LINK_ID = re.compile(r"cfp\.plus/([0-9]{1,32})(?![0-9])", re.I)
_WORD_ID = re.compile(r"\bID\s*(?:số\s*)?:?\s*([0-9]{2,32})\b", re.I)
_URL = re.compile(r"https?://[^\s)\]>\"']+", re.I)
_CANONICAL = re.compile(r"^https://cfp\.plus/[0-9]{1,32}/?$", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.-]?\d){8,10}(?!\d)")
_SENT = re.compile(r"(?<=[.!?\n])\s+")
ALLOWED_EMAILS = {"contact@cfp.plus"}
LEGACY_DOCS = ("HUB69.md", "CMP.md", "registry/GLOBAL_AI_ID_BASELINE_CANDIDATE.md")

# Thành phần CHƯA được kiểm chứng là đang phục vụ người dùng thật (bản đồ hệ sinh thái + lệnh NO-GO).
NOT_LIVE = ("app", "san tmtc", "tmtc", "3366", "quantum", "gen z", "giao trinh", "voice", "da ngon ngu",
            "sieu phan mem", "meta business agent", "production", "dien dan", "mang xa hoi")
CLAIM_LIVE = ("da hoat dong", "dang hoat dong", "da van hanh", "dang van hanh", "da ra mat", "da trien khai",
              "san sang phuc vu", "da hoan thanh", "co the su dung ngay", "is live", "now available", "is available",
              "fully operational", "launched")
# Hướng dẫn tải/cài App khi App chưa tồn tại (bản đồ: App = planned).
APP_STORE = ("app store", "google play", "ch play", "tai app", "tai ung dung", "cai dat app", "download the app",
             "apk")
NEGATION = ("chua", "not yet", "khong", "dang xay dung", "se ", "du kien")
COMMIT = ("cam ket", "bao dam", "dam bao loi nhuan", "lai suat", "hoan tien", "hop dong",
          "thay mat cfp", "dai dien cfp", "chung toi dong y tai tro", "se tai tro", "se chuyen tien",
          "guarantee", "refund", "we promise", "on behalf of cfp", "contract", "investment return")
# Câu hỏi của khách cần người phụ trách (chỉ áp cho câu hỏi; trong câu trả lời "đầu tư" có thể vô hại, vd. Quỹ Đầu Tư)
QUESTION_ESCALATE = COMMIT + ("dau tu", "tai tro", "hop tac chinh thuc", "dong gop tien", "chuyen khoan", "invest",
                              "sponsor", "partnership")
SENSITIVE = ("mat khau", "password", "otp", "so the", "ma pin", "cvv", "cccd", "cmnd", "ho chieu", "so tai khoan",
             "seed phrase", "private key")
ID_STATUS = {"hold_conflict": "HOLD", "parent_hold": "PARENT_HOLD", "pending_verification": "UNVERIFIED",
             "inferred_prefix": "UNVERIFIED", "registry": "CANDIDATE"}


def _legacy_map(root: Path = REPO_ROOT) -> dict[str, set[str]]:
    """ID → tên theo bảng mapping cũ (chỉ đọc, dùng để PHÁT HIỆN, không dùng làm nguồn)."""
    out: dict[str, set[str]] = {}
    pats = (re.compile(r"^\|\s*([0-9]{3,})\s*\|\s*([^|]+?)\s*\|"), re.compile(r"^-\s*([0-9]{3,})\s*—\s*([^/\n]+?)\s*(?:/|$)"))
    for rel in LEGACY_DOCS:
        f = root / rel
        for ln in (f.read_text("utf-8", "replace").splitlines() if f.is_file() else []):
            for p in pats:
                m = p.match(ln)
                if m:
                    out.setdefault(m.group(1), set()).add(m.group(2).strip())
    return out


LEGACY = _legacy_map()


def _sentences(text: str) -> list[str]:
    return [s for s in _SENT.split(text) if s.strip()]


def _f(level, category, code, message, **kw):
    return {"level": level, "category": category, "code": code, "message": message, **kw}


def _current_names(cid: str, it: dict, registry) -> str:
    e = registry.get(cid) if registry is not None else None
    return fold(f"{it['title']} {e.name if e else ''}")


def check_answer(draft: str, catalog, question: str | None = None, registry=None) -> dict:
    """verdict: block > needs_human > ready_for_human_review. Luôn auto_reply=HOLD."""
    findings: list[dict] = []
    ids = list(dict.fromkeys(_LINK_ID.findall(draft) + _WORD_ID.findall(draft)))
    citations, id_report = [], []
    for cid in ids:
        it = catalog.items.get(cid) if catalog is not None else None
        if not it:
            id_report.append({"id": cid, "status": "UNKNOWN"})
            findings.append(_f("block", "id", "unknown_id", f"ID {cid}: UNKNOWN — chưa có trang đã xuất bản, không đưa cho khách.", id=cid))
            continue
        st = ID_STATUS[it["parent_status"]]
        id_report.append({"id": cid, "status": st, "hold_source": (it["hold"] or {}).get("source")})
        citations.append({"id": cid, "url": it["canonical_url"], "title": it["title"], "version": it["version"], "id_status": st})
        if st == "HOLD":
            findings.append(_f("block", "id", "hold_id", f"ID {cid}: HOLD do Registry xác nhận ({it['hold']['source']}) — không giới thiệu như ID đã xác minh.",
                               id=cid, source=it["hold"]["source"]))
        elif st == "PARENT_HOLD":
            findings.append(_f("warn", "id", "parent_hold", f"ID {cid}: Parent {it['hold']['parent']} đang HOLD — ghi rõ 'đang xác minh'.", id=cid))
        elif st == "UNVERIFIED":
            findings.append(_f("warn", "id", "unverified_id", f"ID {cid}: UNVERIFIED — Parent chưa xác minh trong Registry (khác HOLD); ghi 'đang xác minh'.", id=cid))
    for url in dict.fromkeys(u.rstrip(".,;") for u in _URL.findall(draft)):
        low, host = url.lower(), (urlparse(url).hostname or "").lower()
        if any(d.lower() in low for d in LEGACY_DOCS):
            findings.append(_f("block", "source", "legacy_source", "Trích dẫn bảng mapping cũ — chỉ có giá trị audit, không phải nguồn chính thức.", url=url))
        elif host in ("cfp.plus", "www.cfp.plus"):
            if not _CANONICAL.match(url):
                findings.append(_f("block", "link", "noncanonical_link", "Link cfp.plus không theo chuẩn https://cfp.plus/{ID}/ (vd. /forum/, /hub/69/, /_internal/, sandbox).", url=url))
        elif host.endswith("onrender.com") or host.startswith(("localhost", "127.")):
            findings.append(_f("block", "link", "sandbox_link", "Link sandbox nội bộ — không đưa cho khách.", url=url))
        else:
            findings.append(_f("warn", "link", "external_link", "Link ngoài cfp.plus — người duyệt kiểm tra nguồn trước khi gửi.", url=url))
    legacy_hit: set[str] = set()
    for s in _sentences(draft):
        f, snip = fold(s), s.strip()[:200]
        hits = [t for t in NOT_LIVE if re.search(rf"\b{re.escape(t)}\b", f)]
        if hits and any(c in f for c in CLAIM_LIVE):
            findings.append(_f("block", "deployment_claim", "claim_unverified", "Tuyên bố chức năng đang xây dựng/kế hoạch là đã hoạt động — chưa có Evidence.",
                               terms=hits, sentence=snip))
        if any(a in f for a in APP_STORE) and not any(n in f for n in NEGATION):
            findings.append(_f("block", "deployment_claim", "app_store_claim", "Hướng dẫn tải/cài App CFP+ — App chưa phát hành (bản đồ: chờ hoàn thiện).", sentence=snip))
        if any(c in f for c in COMMIT):
            findings.append(_f("needs_human", "authority", "commitment", "Cam kết tài chính/pháp lý/đại diện CFP+ — chuyển người phụ trách.", sentence=snip))
        if any(re.search(rf"\b{re.escape(t)}\b", f) for t in SENSITIVE):
            findings.append(_f("block", "sensitive", "sensitive_request", "Không hỏi/nhận mật khẩu, OTP, số thẻ, giấy tờ tuỳ thân.", sentence=snip))
        for cid in ids:  # Knowledge legacy: ghép ID với tên theo bảng cũ, khác Registry hiện hành
            if cid in LEGACY and cid not in legacy_hit and cid in s and catalog is not None and cid in catalog.items:
                cur = _current_names(cid, catalog.items[cid], registry)
                for old in LEGACY[cid]:
                    tok = fold(old).split()[0] if old.strip() else ""
                    if tok and tok in f and tok not in cur:
                        findings.append(_f("block", "source", "legacy_mapping",
                                           f"ID {cid} được ghép với '{old}' theo bảng mapping cũ; nguồn hiện hành (Registry/trang) khác.",
                                           id=cid, legacy=old))
                        legacy_hit.add(cid)
                        break
    plain = _URL.sub(" ", draft)  # không quét số/email nằm trong URL (vd. cfp.plus/0123456789/)
    for em in {e.rstrip('.').lower() for e in _EMAIL.findall(plain)} - ALLOWED_EMAILS:
        findings.append(_f("needs_human", "sensitive", "personal_contact", "Có email cá nhân/khác kênh chính thức — kiểm tra quyền chia sẻ.", value_sha=hashlib.sha256(em.encode()).hexdigest()[:12]))
    if _PHONE.search(plain):
        findings.append(_f("needs_human", "sensitive", "personal_contact", "Có số điện thoại — kiểm tra quyền chia sẻ."))
    if question and any(c in fold(question) for c in QUESTION_ESCALATE):
        findings.append(_f("needs_human", "authority", "commitment_question", "Câu hỏi về tài chính/pháp lý/hợp tác chính thức — người phụ trách trả lời."))
    if not citations:
        findings.append(_f("warn", "source", "no_source", "Không có link nguồn https://cfp.plus/{ID}/ đã xuất bản."))
    levels = {x["level"] for x in findings}
    verdict = "block" if "block" in levels else "needs_human" if "needs_human" in levels else "ready_for_human_review"
    return {"verdict": verdict, "auto_reply": "HOLD", "findings": findings, "citations": citations, "ids": id_report,
            "categories": sorted({x["category"] for x in findings}), "guard_version": GUARD_VERSION,
            "draft_sha256": hashlib.sha256(draft.encode()).hexdigest()[:16]}
