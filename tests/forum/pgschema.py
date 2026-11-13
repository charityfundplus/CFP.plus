"""Helper test: suy ra schema của từng kho từ search_path của role (không hard-code tên schema).

Nền tảng diễn đàn: services/forum/sql/schemas_up.sql (#193, đang chạy trên Supabase) →
cfp_forum_auth / cfp_forum_sbd / cfp_forum_hstdn. Văn Phòng: 002_office.sql → cfp_office.
"""
from functools import lru_cache

from sqlalchemy import create_engine, text


@lru_cache(maxsize=None)
def schema_of(url: str) -> str:
    eng = create_engine(url)
    try:
        with eng.connect() as c:
            return c.execute(text("select current_schema()")).scalar_one()
    finally:
        eng.dispose()


def truncate_all(admin_url: str, role_urls) -> None:
    """Xoá dữ liệu test ở mọi bảng đang có trong schema của các role (giữ cấu trúc + dấu diễn đàn)."""
    schemas = sorted({schema_of(u) for u in role_urls})
    eng = create_engine(admin_url)
    with eng.begin() as c:
        rows = c.execute(text("select schemaname, tablename from pg_tables where schemaname = any(:s) "
                              "and tablename not in ('forum_meta')"), {"s": schemas}).all()
        if rows:
            c.execute(text("TRUNCATE " + ", ".join(f'"{s}"."{t}"' for s, t in rows) + " RESTART IDENTITY CASCADE"))
    eng.dispose()
