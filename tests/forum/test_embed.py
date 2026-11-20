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


# ---------------- hồi quy theo phản biện độc lập ReviewSI (20/11, F1–F10)
def test_f8_strict_origin_parsing(app_factory):
    c = app_factory("https://*.canva.site,https://www.canva.com,null,http://127.0.0.1:8123")
    for o in ["https://.canva.site", "https://evil.com@x.canva.site", "https://x.canva.site?.canva.site",
              "https://x.canva.site#.canva.site", " null ", "null/", "https://a.canva.site:444", "https://a.canva.site.",
              "javascript://a.canva.site"]:
        r = c.options("/api/auth/me", headers={"Origin": o, "Access-Control-Request-Method": "GET"})
        assert "access-control-allow-origin" not in {k.lower() for k in r.headers}, o
    r = c.options("/api/auth/me", headers={"Origin": "HTTPS://A.Canva.Site", "Access-Control-Request-Method": "GET"})
    assert r.headers["access-control-allow-origin"] == "https://a.canva.site"  # phản chiếu bản chuẩn hóa
    r = c.options("/api/auth/me", headers={"Origin": "http://127.0.0.1:8123", "Access-Control-Request-Method": "GET"})
    assert r.headers["access-control-allow-origin"] == "http://127.0.0.1:8123"  # khớp chính xác có cổng


def test_f2_f9_cors_on_early_errors_and_preflight_headers(app_factory):
    c = app_factory("https://*.canva.site")
    r = c.post("/api/forums/sieu-bo-doi/join", headers={"Origin": CANVA})  # thiếu header CSRF → 403 sớm
    assert r.status_code == 403 and r.headers["access-control-allow-origin"] == CANVA
    pre = c.options("/api/auth/me", headers={"Origin": CANVA, "Access-Control-Request-Method": "GET"})
    assert pre.headers["x-content-type-options"] == "nosniff"


def test_f3_vary_and_no_store(app_factory):
    c = app_factory("https://*.canva.site")
    assert "origin" in c.get("/api/health").headers.get("vary", "").lower()  # cả khi không nhúng
    a = reg(c).json()
    r = c.get("/api/auth/me", headers={"Origin": CANVA, "Authorization": f"Bearer {a['token']}"})
    assert r.headers["cache-control"] == "no-store"


def test_f5_embed_session_short_and_cookieless_logout_revokes_both(app_factory):
    c = app_factory("https://*.canva.site")
    r = reg(c)
    assert "set-cookie" not in {k.lower() for k in r.headers}  # phiên nhúng không đặt cookie
    from sqlalchemy import select
    from services.forum.app import sessions_t
    st = c.app.state.stores
    with st.auth.connect() as conn:
        exp = conn.execute(select(sessions_t.c.expires_at)).scalars().all()[-1]
    from datetime import datetime, timezone
    exp = exp if exp.tzinfo else exp.replace(tzinfo=timezone.utc)
    assert (exp - datetime.now(timezone.utc)).total_seconds() < 13 * 3600
    bearer_tok = r.json()["token"]
    ck = c.post("/api/auth/register", json={"email": "both@example.org", "password": "matkhau-embed", "name": "Ab"},
                headers=H)
    assert ck.status_code == 201
    out = c.post("/api/auth/logout", headers={**H, "Authorization": f"Bearer {bearer_tok}"})  # cookie + bearer
    assert out.status_code == 200
    c.cookies.clear()
    assert c.get("/api/auth/me", headers={"Authorization": f"Bearer {bearer_tok}"}).json()["user"] is None


def test_f6_frame_ancestors_injection_rejected(app_factory, monkeypatch):
    monkeypatch.setenv("CFP_EMBED_FRAME_ANCESTORS", "*; script-src * 'unsafe-inline'")
    c = app_factory("https://*.canva.site")
    r = c.get("/canva/")
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"] and r.headers["x-frame-options"] == "DENY"
    monkeypatch.setenv("CFP_EMBED_FRAME_ANCESTORS", "https://www.canva.com https://*.canva.site")
    r = app_factory("https://*.canva.site").get("/canva/")
    assert "frame-ancestors https://www.canva.com https://*.canva.site;" in r.headers["content-security-policy"]


def test_f7_same_host_page_in_iframe_can_get_token(app_factory):
    c = app_factory("https://*.canva.site")
    r = c.post("/api/auth/register", json={"email": "same@example.org", "password": "matkhau-embed", "name": "Ab"},
               headers={**H, "Origin": "http://testserver", "X-CFP-Token": "1"})
    assert r.status_code == 201 and r.json().get("token")


def test_f1_per_account_login_throttle(app_factory, monkeypatch):
    monkeypatch.setenv("CFP_FORUM_RL_LOGIN_PER_ACCOUNT", "3")
    c = app_factory("https://*.canva.site")
    h = {**H, "Origin": CANVA, "X-CFP-Token": "1"}
    codes = [c.post("/api/auth/login", json={"email": "victim@example.org", "password": f"sai-{i}-xxxx"},
                    headers={**h, "X-Forwarded-For": f"10.0.0.{i}"}).status_code for i in range(5)]
    assert codes[:3] == [401, 401, 401] and codes[3:] == [429, 429]
    assert c.post("/api/auth/login", json={"email": "victim@example.org", "password": "x"},
                  headers=h).headers["access-control-allow-origin"] == CANVA  # 429 đọc được (Retry-After)


def test_f10_validation_error_does_not_echo_password(app_factory):
    c = app_factory(None)
    r = c.post("/api/auth/register", json={"email": "x@example.org", "password": "ngan", "name": "Ab"}, headers=H)
    assert r.status_code == 422 and "ngan" not in r.text
