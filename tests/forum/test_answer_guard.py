"""Bộ kiểm thử tình huống tư vấn khách hàng • Siêu Phần Mềm giám sát câu trả lời (AUTO REPLY HOLD).

Mỗi tình huống: bản nháp của Agent (vd. Meta Business Agent) → verdict mong đợi + mã lỗi bắt buộc.
Không gọi API bên ngoài; chỉ dùng Link Mẫu (trang ID đã xuất bản) và hồ sơ review-holding trong repo.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from services.forum.answer_guard import check_answer
from services.forum.app import Stores, create_app
from services.forum.catalog import Catalog
from services.forum.registry import Registry
from tests.forum.office_flow import H, ok, register


@pytest.fixture(scope="module")
def cat():
    return Catalog(Registry())


SCENARIOS = [
    # (tên, câu hỏi, bản nháp, verdict, mã bắt buộc)
    ("giới thiệu đúng + có nguồn", "CFP+ là gì?",
     "CFP+ hoạt động theo định hướng Phục Vụ Vô Vụ Lợi, tổ chức theo 5 Nhóm và 10 Chương. "
     "Xem HUB 69: https://cfp.plus/69/ và 10 Chương: https://cfp.plus/0123456789/",
     "ready_for_human_review", set()),
    ("phi lợi nhuận không bị coi là cam kết", "CFP+ có thu phí không?",
     "CFP+ theo định hướng phi lợi nhuận, đóng góp tự nguyện, pháp lý và minh bạch. Nguồn: https://cfp.plus/000/",
     "ready_for_human_review", set()),
    ("ID chưa xuất bản → chặn", "Cho tôi link quỹ 331",
     "Bạn mở https://cfp.plus/331/ để xem Quỹ Sự Sống.", "block", {"unknown_id"}),
    ("ID đang HOLD (69115) → chặn", "Meta có văn phòng ở CFP+ không?",
     "Văn phòng Meta là ID 69115: https://cfp.plus/69115/", "block", {"hold_id"}),
    ("Parent đang HOLD → cảnh báo", "Meta AI Assistant ở đâu?",
     "Xem https://cfp.plus/691151/ (đang xác minh).", "ready_for_human_review", {"parent_hold"}),
    ("tuyên bố App đã hoạt động → chặn", "Tải App CFP+ ở đâu?",
     "App CFP+ đã hoạt động, bạn có thể dùng ngay. Xem https://cfp.plus/69/", "block", {"claim_unverified"}),
    ("tuyên bố Sàn TMTC live → chặn", "Sàn TMTC mở chưa?",
     "Sàn TMTC đã ra mắt và sẵn sàng phục vụ. https://cfp.plus/8682/", "block", {"claim_unverified"}),
    ("nói đúng 'đang xây dựng' → không chặn", "Sàn TMTC mở chưa?",
     "Sàn TMTC đang xây dựng, chưa phục vụ giao dịch thật. Thông tin: https://cfp.plus/8682/",
     "ready_for_human_review", set()),
    ("cam kết tài chính → người phụ trách", "CFP+ tài trợ cho dự án của tôi được không?",
     "CFP+ cam kết tài trợ 100 triệu cho dự án của bạn. https://cfp.plus/3/", "needs_human", {"commitment"}),
    ("đại diện CFP+ ký hợp đồng → người phụ trách", None,
     "Tôi thay mặt CFP+ đồng ý ký hợp đồng hợp tác. https://cfp.plus/69/", "needs_human", {"commitment"}),
    ("hỏi OTP/mật khẩu → chặn", "Tôi muốn đăng ký",
     "Vui lòng gửi mật khẩu và mã OTP để chúng tôi đăng ký giúp. https://cfp.plus/69/", "block", {"sensitive_request"}),
    ("không có nguồn → cảnh báo", "CFP+ là gì?",
     "CFP+ là cộng đồng Không Của Riêng Ai.", "ready_for_human_review", {"no_source"}),
    ("câu hỏi hợp tác tài chính → người phụ trách", "Tôi muốn ký hợp đồng đầu tư với CFP+",
     "Cảm ơn bạn, người phụ trách sẽ liên hệ. https://cfp.plus/69/", "needs_human", {"commitment_question"}),
    ("English: claims live → block", "Is the App available?",
     "Yes, the CFP+ App is live now. https://cfp.plus/69/", "block", {"claim_unverified"}),
]


@pytest.mark.parametrize("name,q,draft,verdict,codes", SCENARIOS, ids=[s[0] for s in SCENARIOS])
def test_consult_scenarios(cat, name, q, draft, verdict, codes):
    res = check_answer(draft, cat, q)
    got = {f["code"] for f in res["findings"]}
    assert res["auto_reply"] == "HOLD"  # không bao giờ tự gửi
    assert res["verdict"] == verdict, (name, res["findings"])
    assert codes <= got, (name, got)
    for c in res["citations"]:  # nguồn luôn là bản gốc hiện hành của Link Mẫu
        assert c["url"] == f"https://cfp.plus/{c['id']}/" and c["version"].startswith("sha256:")


def test_holds_from_review_holding(cat):
    assert cat.items["69115"]["parent_status"] == "hold_conflict"
    assert cat.items["691151"]["parent_status"] == "parent_hold" and cat.items["691151"]["hold"]["parent"] == "69115"
    assert cat.items["69113"]["parent_status"] == "hold_conflict"
    assert all(it["hold"] is None for it in cat.items.values() if it["parent_status"] in ("registry", "pending_verification"))


def test_answer_check_api(tmp_path, monkeypatch):
    monkeypatch.setenv("CFP_FORUM_COOKIE_SECURE", "0")
    st = Stores(f"sqlite:///{tmp_path}/a.db", {"sieu-bo-doi": f"sqlite:///{tmp_path}/s.db",
                                                "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"}, f"sqlite:///{tmp_path}/o.db")
    c = TestClient(create_app(st))
    body = {"draft": "App CFP+ đã hoạt động. Mật khẩu của bạn là gì? https://cfp.plus/69115/", "agent": "Meta Business Agent"}
    assert c.post("/api/office/answer-check", json=body, headers=H).status_code == 401  # khách không dùng được
    register(c, f"meta{uuid.uuid4().hex[:6]}@example.org", "Agent Trainer")
    res = ok(c.post("/api/office/answer-check", json=body, headers=H), 200)
    assert res["verdict"] == "block" and res["auto_reply"] == "HOLD"
    assert {"claim_unverified", "sensitive_request", "hold_id"} <= {f["code"] for f in res["findings"]}
    m = c.get("/api/catalog/meta").json()
    assert m["parent_counts"]["hold_conflict"] >= 1 and "69115" in m["holds"]
