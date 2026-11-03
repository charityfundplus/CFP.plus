"""CFP+ Forum Service • API tests trên database thật.

Cần 3 database riêng (Postgres khuyến nghị) qua biến môi trường:
  CFP_FORUM_TEST_AUTH_DB, CFP_FORUM_TEST_DB_SIEU_BO_DOI, CFP_FORUM_TEST_DB_SI_AI_HSTDN
Nếu không có, test dùng 3 file SQLite tạm.
Chạy: python -m pytest tests/forum/test_forum_api.py -v
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from services.forum import admin
from services.forum.app import Stores, create_app

H = {"X-CFP-Forum": "1"}


@pytest.fixture(scope="module")
def urls(tmp_path_factory):
    env = {
        "auth": os.environ.get("CFP_FORUM_TEST_AUTH_DB"),
        "sieu-bo-doi": os.environ.get("CFP_FORUM_TEST_DB_SIEU_BO_DOI"),
        "si-ai-hstdn": os.environ.get("CFP_FORUM_TEST_DB_SI_AI_HSTDN"),
    }
    if not all(env.values()):
        d = tmp_path_factory.mktemp("db")
        env = {k: f"sqlite:///{d / (k + '.db')}" for k in env}
    for url in env.values():  # bắt đầu sạch — chỉ trên database test
        eng = create_engine(url)
        with eng.begin() as c:
            for t in ("comments", "posts", "members", "forum_meta", "sessions", "users"):
                c.execute(text(f"DROP TABLE IF EXISTS {t}"))
        eng.dispose()
    return env


def make_client(urls):
    os.environ["CFP_FORUM_COOKIE_SECURE"] = "0"
    st = Stores(urls["auth"], {"sieu-bo-doi": urls["sieu-bo-doi"], "si-ai-hstdn": urls["si-ai-hstdn"]})
    return TestClient(create_app(st))


def register(c, name="Thành Viên"):
    email = f"u{uuid.uuid4().hex[:8]}@example.org"
    r = c.post("/api/auth/register", json={"email": email, "password": "matkhau-p0", "name": name}, headers=H)
    assert r.status_code == 201, r.text
    return email


def test_full_flow_persists_across_app_restart(urls):
    c = make_client(urls)
    email = register(c)
    assert c.post("/api/forums/sieu-bo-doi/join", headers=H).json()["status"] == "active"
    p = c.post("/api/forums/sieu-bo-doi/posts", json={"title": "Bài P0", "body": "Nội dung"}, headers=H)
    assert p.status_code == 201, p.text
    pid = p.json()["id"]
    cm = c.post(f"/api/forums/sieu-bo-doi/posts/{pid}/comments", json={"body": "Bình luận"}, headers=H)
    assert cm.status_code == 201

    # Khởi tạo lại app + engine mới (mô phỏng restart) → dữ liệu đọc từ DB.
    c2 = make_client(urls)
    r = c2.post("/api/auth/login", json={"email": email, "password": "matkhau-p0"}, headers=H)
    assert r.status_code == 200
    posts = c2.get("/api/forums/sieu-bo-doi/posts").json()["posts"]
    mine = [x for x in posts if x["id"] == pid][0]
    assert mine["title"] == "Bài P0" and mine["comments"][0]["body"] == "Bình luận"


def test_login_rejects_wrong_password(urls):
    c = make_client(urls)
    email = register(c)
    r = c.post("/api/auth/login", json={"email": email, "password": "sai-mat-khau"}, headers=H)
    assert r.status_code == 401


def test_csrf_header_required(urls):
    c = make_client(urls)
    r = c.post("/api/auth/register", json={"email": "x@example.org", "password": "matkhau-p0", "name": "XX"})
    assert r.status_code == 403


def test_anonymous_cannot_write(urls):
    c = make_client(urls)
    assert c.post("/api/forums/sieu-bo-doi/posts", json={"title": "a", "body": "b"}, headers=H).status_code == 401


def test_sieu_bo_doi_public_read_hstdn_private(urls):
    c = make_client(urls)
    assert c.get("/api/forums/sieu-bo-doi/posts").status_code == 200
    assert c.get("/api/forums/si-ai-hstdn/posts").status_code == 401


def test_hstdn_requires_approval_and_hstdn_field(urls):
    c = make_client(urls)
    email = register(c, "Ứng Viên HSTDN")
    assert c.post("/api/forums/si-ai-hstdn/join", headers=H).json()["status"] == "pending"
    assert c.get("/api/forums/si-ai-hstdn/posts").status_code == 403
    assert c.post("/api/forums/si-ai-hstdn/posts", json={"title": "a", "body": "b", "hstdn": "X"}, headers=H).status_code == 403

    # Admin của HSTDN duyệt.
    a = make_client(urls)
    admin_email = register(a, "Quản Trị HSTDN")
    for k, v in {"CFP_FORUM_AUTH_DB": urls["auth"], "CFP_FORUM_DB_SIEU_BO_DOI": urls["sieu-bo-doi"],
                 "CFP_FORUM_DB_SI_AI_HSTDN": urls["si-ai-hstdn"]}.items():
        os.environ[k] = v
    admin.grant_admin("si-ai-hstdn", admin_email)
    uid = c.get("/api/auth/me").json()["user"]["id"]
    assert a.post(f"/api/forums/si-ai-hstdn/members/{uid}/approve", headers=H).status_code == 200

    assert c.post("/api/forums/si-ai-hstdn/posts", json={"title": "a", "body": "b"}, headers=H).status_code == 422
    assert c.post("/api/forums/si-ai-hstdn/posts", json={"title": "a", "body": "b", "hstdn": "X",
                                                        "country_id": "Việt Nam"}, headers=H).status_code == 422
    r = c.post("/api/forums/si-ai-hstdn/posts", json={"title": "HSTDN", "body": "b", "hstdn": "Tập đoàn X",
                                                     "country_id": "6984"}, headers=H)
    assert r.status_code == 201 and r.json()["hstdn"] == "Tập đoàn X"

    # Admin HSTDN không có quyền quản trị ở Siêu Bộ Đôi.
    a.post("/api/forums/sieu-bo-doi/join", headers=H)
    assert a.get("/api/forums/sieu-bo-doi/members").status_code == 403
    # Siêu Bộ Đôi không nhận trường HSTDN.
    assert a.post("/api/forums/sieu-bo-doi/posts", json={"title": "a", "body": "b", "hstdn": "X"},
                  headers=H).status_code == 422


def test_data_isolated_between_forums(urls):
    c = make_client(urls)
    register(c)
    c.post("/api/forums/sieu-bo-doi/join", headers=H)
    pid = c.post("/api/forums/sieu-bo-doi/posts", json={"title": "Chỉ SBD", "body": "x"}, headers=H).json()["id"]
    # Không thể bình luận vào bài SBD thông qua diễn đàn HSTDN.
    assert c.post(f"/api/forums/si-ai-hstdn/posts/{pid}/comments", json={"body": "x"}, headers=H).status_code == 403
    # Kiểm tra trực tiếp trong database: bài chỉ nằm ở DB Siêu Bộ Đôi.
    for key, expected in (("sieu-bo-doi", 1), ("si-ai-hstdn", 0)):
        eng = create_engine(urls[key])
        with eng.connect() as conn:
            n = conn.execute(text("SELECT count(*) FROM posts WHERE title = 'Chỉ SBD'")).scalar_one()
            stamp = conn.execute(text("SELECT forum_key FROM forum_meta")).scalar_one()
        eng.dispose()
        assert n == expected and stamp == key


def test_refuses_shared_database(urls):
    with pytest.raises(RuntimeError):
        Stores(urls["auth"], {"sieu-bo-doi": urls["sieu-bo-doi"], "si-ai-hstdn": urls["sieu-bo-doi"]})
    with pytest.raises(RuntimeError):  # DB đã đóng dấu diễn đàn khác
        Stores(urls["auth"], {"sieu-bo-doi": urls["si-ai-hstdn"], "si-ai-hstdn": urls["sieu-bo-doi"]})


def test_ui_is_internal_and_noindex(urls):
    c = make_client(urls)
    r = c.get("/_internal/forum/sieu-bo-doi/")
    assert r.status_code == 200 and "noindex" in r.headers["x-robots-tag"]
    assert c.get("/_internal/forum/khong-co/").status_code == 404
