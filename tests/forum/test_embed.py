"""Chế độ NHÚNG (Canva Code / Canva App / trang Canva đã xuất bản): token Bearer + CORS theo danh sách.

Bảo đảm:
  • tắt mặc định: không CORS, không trả token;
  • chỉ nguồn trong CFP_EMBED_ORIGINS nhận CORS (khớp chính xác hoặc *.domain; không khớp đuôi giả);
  • token chỉ trả khi trang nhúng hợp lệ xin rõ (X-CFP-Token: 1);
  • nguồn nhúng KHÔNG dùng được cookie (cookie + Origin nhúng → 403), không có Allow-Credentials;
  • token Bearer mang đúng danh tính; quyền máy chủ giữ nguyên (người khác không thấy nhiệm vụ);
  • đăng xuất hủy token; token sai → 401.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from services.forum.app import Stores, create_app

H = {"X-CFP-Forum": "1"}
CANVA = "https://cfp-forum.my.canva.site"


@pytest.fixture()
def app_factory(tmp_path, monkeypatch):
    monkeypatch.setenv("CFP_FORUM_RL_AUTH_PER_MIN", "1000")
    monkeypatch.setenv("CFP_FORUM_RL_WRITE_PER_MIN", "1000")
    monkeypatch.setenv("CFP_FORUM_COOKIE_SECURE", "0")

    def make(origins: str | None):
        if origins is None:
            monkeypatch.delenv("CFP_EMBED_ORIGINS", raising=False)
        else:
            monkeypatch.setenv("CFP_EMBED_ORIGINS", origins)
        u = lambda n: f"sqlite:///{tmp_path / n}.db"  # noqa: E731
        st = Stores(u("auth"), {"sieu-bo-doi": u("sbd"), "si-ai-hstdn": u("hstdn")}, u("office"))
        return TestClient(create_app(st))
    return make


def reg(c, origin=CANVA, token=True):
    h = {**H, "Origin": origin} if origin else dict(H)
    if token:
        h["X-CFP-Token"] = "1"
    r = c.post("/api/auth/register", json={"email": f"e{uuid.uuid4().hex[:8]}@example.org",
                                           "password": "matkhau-embed", "name": "Thành viên Canva"}, headers=h)
    c.cookies.clear()  # trình duyệt không lưu cookie từ phản hồi khác nguồn không credentials
    return r


def test_disabled_by_default(app_factory):
    c = app_factory(None)
    r = reg(c)
    assert r.status_code == 403  # Origin lạ, không có chế độ nhúng
    pre = c.options("/api/forums/sieu-bo-doi/posts", headers={"Origin": CANVA, "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in {k.lower() for k in pre.headers}
    r = c.post("/api/auth/register", json={"email": "x1@example.org", "password": "matkhau-embed", "name": "Ab"},
               headers={**H, "X-CFP-Token": "1"})
    assert r.status_code == 201 and "token" not in r.json()


def test_origin_matching(app_factory):
    c = app_factory("https://*.canva.site,https://www.canva.com,null")
    ok = ["https://a.canva.site", "https://x.my.canva.site", "https://www.canva.com", "null"]
    bad = ["https://canva.site.evil.com", "https://evilcanva.site", "http://a.canva.site", "https://www.canva.com.evil.io",
           "https://a.canva.site:444"]
    for o in ok:
        r = c.options("/api/auth/me", headers={"Origin": o, "Access-Control-Request-Method": "GET"})
        assert r.status_code == 204 and r.headers["access-control-allow-origin"] == o, o
        assert "access-control-allow-credentials" not in {k.lower() for k in r.headers}
    for o in bad:
        r = c.options("/api/auth/me", headers={"Origin": o, "Access-Control-Request-Method": "GET"})
        assert "access-control-allow-origin" not in {k.lower() for k in r.headers}, o


def test_bearer_flow_post_read_reply_two_accounts(app_factory):
    c = app_factory("https://*.canva.site")
    a, b = reg(c).json(), reg(c).json()
    assert a["token"] and b["token"] and a["token"] != b["token"]
    ha = {**H, "Origin": CANVA, "Authorization": f"Bearer {a['token']}"}
    hb = {**H, "Origin": CANVA, "Authorization": f"Bearer {b['token']}"}
    assert c.get("/api/auth/me", headers=ha).json()["user"]["id"] == a["id"]
    for h in (ha, hb):
        assert c.post("/api/forums/sieu-bo-doi/join", headers=h).status_code == 200
    p = c.post("/api/forums/sieu-bo-doi/posts", json={"title": "Từ Canva", "body": "Bài của A"}, headers=ha)
    assert p.status_code == 201 and p.headers["access-control-allow-origin"] == CANVA
    pid = p.json()["id"]
    posts = c.get("/api/forums/sieu-bo-doi/posts", headers=hb).json()["posts"]
    assert any(x["id"] == pid and x["author"]["id"] == a["id"] for x in posts)
    r = c.post(f"/api/forums/sieu-bo-doi/posts/{pid}/comments", json={"body": "B phản hồi"}, headers=hb)
    assert r.status_code == 201 and r.json()["author"]["id"] == b["id"]


def test_cookie_with_embed_origin_is_refused(app_factory):
    c = app_factory("https://*.canva.site")
    r = c.post("/api/auth/register", json={"email": "ck@example.org", "password": "matkhau-embed", "name": "Ab"},
               headers=H)  # cùng nguồn → có cookie
    assert r.status_code == 201
    r = c.post("/api/forums/sieu-bo-doi/join", headers={**H, "Origin": CANVA})  # cookie tự gửi + Origin nhúng
    assert r.status_code == 403


def test_token_not_returned_to_foreign_origin_or_without_ask(app_factory):
    c = app_factory("https://*.canva.site")
    assert "token" not in reg(c, token=False).json()
    assert reg(c, origin="https://evil.example").status_code == 403


def test_bad_token_and_logout(app_factory):
    c = app_factory("https://*.canva.site")
    a = reg(c).json()
    h = {**H, "Origin": CANVA, "Authorization": f"Bearer {a['token']}"}
    assert c.get("/api/auth/me", headers={**h, "Authorization": "Bearer sai"}).json()["user"] is None
    assert c.post("/api/forums/sieu-bo-doi/join", headers={**h, "Authorization": "Bearer sai"}).status_code == 401
    assert c.post("/api/auth/logout", headers=h).status_code == 200
    assert c.get("/api/auth/me", headers=h).json()["user"] is None


def test_server_side_permissions_unchanged_for_bearer(app_factory):
    c = app_factory("https://*.canva.site")
    a = reg(c).json()
    h = {**H, "Origin": CANVA, "Authorization": f"Bearer {a['token']}"}
    assert c.get("/api/office/board", headers=h).json()["tasks"] == []
    r = c.post("/api/office/tasks", json={"pair_id": 1, "title": "abc", "acceptance": "abc", "reviewer_id": 1,
                                          "idempotency_key": "embed-test-1"}, headers=h)
    assert r.status_code in (403, 404)
    assert c.post("/api/worker/control", json={"paused": True}, headers=h).status_code in (401, 403, 404, 422)


def test_canva_page_served_and_single_file_is_fresh(app_factory, monkeypatch):
    from services.forum.web import build_canva
    assert build_canva.OUT.read_text(encoding="utf-8") == build_canva.build(), "chạy python -m services.forum.web.build_canva"
    html = build_canva.OUT.read_text(encoding="utf-8")
    assert "innerHTML" not in html and "eval(" not in html  # không chèn HTML thô, không eval
    c = app_factory(None)
    r = c.get("/canva/")
    assert r.status_code == 200 and "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-frame-options"] == "DENY"
    assert c.get("/canva/canva.js").status_code == 200
    monkeypatch.setenv("CFP_EMBED_FRAME_ANCESTORS", "https://www.canva.com")
    c = app_factory("https://*.canva.site")
    r = c.get("/canva/")
    assert "frame-ancestors https://www.canva.com" in r.headers["content-security-policy"]
    assert "x-frame-options" not in {k.lower() for k in r.headers}
    assert c.get("/api/health").headers["x-frame-options"] == "DENY"  # API vẫn chặn khung
