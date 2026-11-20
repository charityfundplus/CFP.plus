"""CFP+ Forum + Văn Phòng • Cách ly kho theo NƠI GHI THẬT (kế thừa test của #193).

URL khác chuỗi chưa đủ: thêm `application_name`, đổi đường dẫn tệp (`./a.db`) hay dùng lại role
của kho khác đều trỏ cùng một database/schema. Stores phải từ chối khởi động TRƯỚC khi tạo bảng,
để không có bảng diễn đàn nào bị tạo lẫn vào schema auth/Văn Phòng.

- Phần SQLite chạy ở mọi môi trường.
- Phần Postgres chạy khi có CFP_FORUM_TEST_ADMIN_DB (tests/forum/run_all.sh, chế độ 4 schema/role).
"""
import os
import sqlite3

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

from services.forum.app import Stores
from tests.forum.pgschema import schema_of

PG = {
    "auth": os.environ.get("CFP_FORUM_TEST_AUTH_DB"),
    "sieu-bo-doi": os.environ.get("CFP_FORUM_TEST_DB_SIEU_BO_DOI"),
    "si-ai-hstdn": os.environ.get("CFP_FORUM_TEST_DB_SI_AI_HSTDN"),
    "office": os.environ.get("CFP_OFFICE_TEST_DB"),
    "admin": os.environ.get("CFP_FORUM_TEST_ADMIN_DB"),
}
needs_pg = pytest.mark.skipif(not all(PG.values()), reason="chỉ áp dụng chế độ schema/role (Supabase)")


def _alias(url: str, tag: str) -> str:
    return url + ("&" if "?" in url else "?") + f"application_name={tag}"


def _sqlite_tables(path) -> set[str]:
    with sqlite3.connect(path) as c:
        return {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}


# ---------------------------------------------------------------- SQLite (mọi môi trường)

def test_sqlite_same_file_different_string_is_refused(tmp_path):
    a = tmp_path / "a.db"
    with pytest.raises(RuntimeError, match="schema riêng biệt"):
        Stores(f"sqlite:///{a}", {"sieu-bo-doi": f"sqlite:///{tmp_path}/./a.db",
                                   "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"})
    # Từ chối TRƯỚC khi tạo bảng: tệp auth không bị lẫn bảng diễn đàn.
    assert not ({"posts", "forum_meta"} & (_sqlite_tables(a) if a.exists() else set()))


def test_sqlite_office_alias_of_forum_is_refused(tmp_path):
    with pytest.raises(RuntimeError, match="schema riêng biệt"):
        Stores(f"sqlite:///{tmp_path}/a.db",
               {"sieu-bo-doi": f"sqlite:///{tmp_path}/s.db", "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"},
               f"sqlite:///{tmp_path}/../{tmp_path.name}/s.db")


def test_sqlite_distinct_files_record_locations(tmp_path):
    st = Stores(f"sqlite:///{tmp_path}/a.db",
                {"sieu-bo-doi": f"sqlite:///{tmp_path}/s.db", "si-ai-hstdn": f"sqlite:///{tmp_path}/h.db"},
                f"sqlite:///{tmp_path}/o.db")
    try:
        assert set(st.locations) == {"auth", "sieu-bo-doi", "si-ai-hstdn", "office"}
        assert len(set(st.locations.values())) == 4
    finally:
        st.dispose()


# ---------------------------------------------------------------- Postgres (4 schema/role như Supabase)

@needs_pg
def test_each_store_lands_in_its_own_schema():
    st = Stores(PG["auth"], {k: PG[k] for k in ("sieu-bo-doi", "si-ai-hstdn")}, PG["office"])
    try:
        schemas = {k: v[2] for k, v in st.locations.items()}
        assert schemas == {k: schema_of(PG[k]) for k in ("auth", "sieu-bo-doi", "si-ai-hstdn", "office")}
        assert len(set(schemas.values())) == 4
        assert len({v[1] for v in st.locations.values()}) == 1  # cùng một database vật lý (Supabase)
    finally:
        st.dispose()


@needs_pg
def test_auth_role_reused_as_forum_is_refused_before_create():
    admin = create_engine(PG["admin"])
    auth_schema = schema_of(PG["auth"])
    q = text("SELECT count(*) FROM pg_tables WHERE schemaname = :s AND tablename IN ('posts', 'forum_meta')")
    try:
        with admin.connect() as c:
            before = c.execute(q, {"s": auth_schema}).scalar_one()
        with pytest.raises(RuntimeError, match="schema riêng biệt"):
            Stores(_alias(PG["auth"], "auth2"), {"sieu-bo-doi": PG["auth"], "si-ai-hstdn": PG["si-ai-hstdn"]})
        with admin.connect() as c:
            assert c.execute(q, {"s": auth_schema}).scalar_one() == before == 0
    finally:
        admin.dispose()


@needs_pg
def test_office_role_alias_is_refused():
    with pytest.raises(RuntimeError, match="schema riêng biệt"):
        Stores(PG["auth"], {k: PG[k] for k in ("sieu-bo-doi", "si-ai-hstdn")}, _alias(PG["sieu-bo-doi"], "o2"))


@needs_pg
@pytest.mark.parametrize("who, other", [("sieu-bo-doi", "si-ai-hstdn"), ("si-ai-hstdn", "auth"),
                                        ("auth", "sieu-bo-doi"), ("office", "auth")])
def test_role_cannot_delete_in_other_schema(who, other):
    Stores(PG["auth"], {k: PG[k] for k in ("sieu-bo-doi", "si-ai-hstdn")}, PG["office"]).dispose()  # bảng đã có
    admin = create_engine(PG["admin"])
    with admin.connect() as c:
        table = c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = :s ORDER BY tablename LIMIT 1"),
                          {"s": schema_of(PG[other])}).scalar_one()
    admin.dispose()
    eng = create_engine(PG[who])
    try:
        with eng.begin() as c, pytest.raises(ProgrammingError, match="permission denied"):
            c.execute(text(f'DELETE FROM "{schema_of(PG[other])}"."{table}"'))
    finally:
        eng.dispose()


@needs_pg
@pytest.mark.parametrize("who", ["auth", "sieu-bo-doi", "si-ai-hstdn", "office"])
def test_role_cannot_create_in_public(who):
    eng = create_engine(PG[who])
    try:
        with eng.begin() as c, pytest.raises(ProgrammingError, match="permission denied"):
            c.execute(text("CREATE TABLE public.cfp_forum_leak (id int)"))
    finally:
        eng.dispose()
