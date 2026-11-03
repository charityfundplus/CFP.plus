"""Quản trị thành viên theo từng diễn đàn (không có quyền xuyên diễn đàn).

python -m services.forum.admin grant-admin <forum_key> <email>
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


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "grant-admin":
        grant_admin(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)
