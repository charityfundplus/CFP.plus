"""Quản trị thành viên theo từng diễn đàn (không có quyền xuyên diễn đàn).

python -m services.forum.admin grant-admin <forum_key> <email>
python -m services.forum.admin grant-office-role <governance|reviewer> <email>
"""
import sys

from sqlalchemy import insert, select, update

from services.forum.app import FORUMS, Stores, members_t, users_t


def grant_admin(forum_key: str, email: str) -> None:
    if forum_key not in FORUMS:
        raise SystemExit(f"Không có diễn đàn {forum_key}")
    st = Stores.from_env()
    with st.auth.connect() as c:
        u = c.execute(select(users_t.c.id, users_t.c.name).where(users_t.c.email == email.lower())).first()
    if not u:
        raise SystemExit("Không tìm thấy tài khoản.")
    with st.forums[forum_key].begin() as c:
        if c.execute(select(members_t.c.user_id).where(members_t.c.user_id == u.id)).first():
            c.execute(update(members_t).where(members_t.c.user_id == u.id).values(role="admin", status="active"))
        else:
            c.execute(insert(members_t).values(user_id=u.id, user_name=u.name, role="admin", status="active"))
    print(f"OK: {email} là admin của {forum_key}")


def grant_office_role(role: str, email: str) -> None:
    from services.forum.office import roles_t
    if role not in {"governance", "reviewer"}:
        raise SystemExit("Vai trò phải là governance hoặc reviewer")
    import os
    from sqlalchemy import create_engine
    st = Stores.from_env()
    if st.office is None:
        raise SystemExit("Chưa cấu hình CFP_OFFICE_DB")
    with st.auth.connect() as c:
        u = c.execute(select(users_t.c.id).where(users_t.c.email == email.lower())).first()
    if not u:
        raise SystemExit("Không tìm thấy tài khoản.")
    # Role của app không có quyền ghi office_roles; dùng kết nối quản trị nếu có (CFP_OFFICE_ADMIN_DB).
    admin_url = os.environ.get("CFP_OFFICE_ADMIN_DB")
    eng = create_engine(admin_url, connect_args={"options": "-c search_path=cfp_office"}) if admin_url else st.office
    with eng.begin() as c:
        if admin_url and eng.dialect.name == "postgresql":
            c.exec_driver_sql("SET LOCAL ROLE office_governance")
        if not c.execute(select(roles_t.c.user_id).where(roles_t.c.user_id == u.id, roles_t.c.role == role)).first():
            c.execute(insert(roles_t).values(user_id=u.id, role=role))
    print(f"OK: {email} có vai trò {role} tại Văn Phòng SI AI")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "grant-admin":
        grant_admin(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 4 and sys.argv[1] == "grant-office-role":
        grant_office_role(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
