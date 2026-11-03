"""CFP+ Forum P0 • Cách ly 3 schema Postgres (một database, ba role riêng).

Chỉ chạy khi CFP_FORUM_TEST_SCHEMA_MODE=1 và ba URL role đã được đặt:
  CFP_FORUM_TEST_AUTH_DB, CFP_FORUM_TEST_DB_SIEU_BO_DOI, CFP_FORUM_TEST_DB_SI_AI_HSTDN
(sau khi chạy services/forum/sql/schemas_up.sql và đặt mật khẩu role).
"""
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from services.forum.app import Stores

pytestmark = pytest.mark.skipif(os.environ.get("CFP_FORUM_TEST_SCHEMA_MODE") != "1",
                                reason="Chỉ chạy ở chế độ 3 schema")

EXPECTED = {"auth": "cfp_forum_auth", "sieu-bo-doi": "cfp_forum_sbd", "si-ai-hstdn": "cfp_forum_hstdn"}


@pytest.fixture(scope="module")
def urls():
    u = {"auth": os.environ["CFP_FORUM_TEST_AUTH_DB"],
         "sieu-bo-doi": os.environ["CFP_FORUM_TEST_DB_SIEU_BO_DOI"],
         "si-ai-hstdn": os.environ["CFP_FORUM_TEST_DB_SI_AI_HSTDN"]}
    Stores(u["auth"], {k: u[k] for k in ("sieu-bo-doi", "si-ai-hstdn")})  # tạo bảng
    return u


def test_each_store_lands_in_its_own_schema(urls):
    st = Stores(urls["auth"], {k: urls[k] for k in ("sieu-bo-doi", "si-ai-hstdn")})
    assert {k: v[2] for k, v in st.locations.items()} == EXPECTED
    assert len({v[1] for v in st.locations.values()}) == 1  # cùng một database vật lý


@pytest.mark.parametrize("who, target", [
    ("sieu-bo-doi", "cfp_forum_hstdn.posts"),
    ("sieu-bo-doi", "cfp_forum_auth.users"),
    ("si-ai-hstdn", "cfp_forum_sbd.posts"),
    ("si-ai-hstdn", "cfp_forum_auth.sessions"),
    ("auth", "cfp_forum_sbd.members"),
    ("auth", "cfp_forum_hstdn.comments"),
])
def test_role_cannot_touch_other_schema(urls, who, target):
    eng = create_engine(urls[who])
    try:
        for sql in (f"SELECT 1 FROM {target} LIMIT 1", f"DELETE FROM {target}"):
            with eng.connect() as c, pytest.raises(ProgrammingError, match="permission denied"):
                c.execute(text(sql))
    finally:
        eng.dispose()


def test_role_cannot_create_in_public(urls):
    eng = create_engine(urls["sieu-bo-doi"])
    try:
        with eng.begin() as c, pytest.raises(ProgrammingError, match="permission denied"):
            c.execute(text("CREATE TABLE public.cfp_forum_leak (id int)"))
    finally:
        eng.dispose()


def test_refuses_two_urls_same_schema(urls):
    # URL khác chuỗi nhưng cùng role/schema → phải từ chối khởi động.
    sep = "&" if "?" in urls["sieu-bo-doi"] else "?"
    alias = urls["sieu-bo-doi"] + sep + "application_name=alias"
    with pytest.raises(RuntimeError, match="schema riêng biệt"):
        Stores(urls["auth"], {"sieu-bo-doi": urls["sieu-bo-doi"], "si-ai-hstdn": alias})
    # Diễn đàn dùng nhầm role auth (URL khác chuỗi) → cũng phải từ chối.
    auth_alias = urls["auth"] + ("&" if "?" in urls["auth"] else "?") + "application_name=a2"
    with pytest.raises(RuntimeError, match="schema riêng biệt"):
        Stores(auth_alias, {"sieu-bo-doi": urls["auth"], "si-ai-hstdn": urls["si-ai-hstdn"]})
