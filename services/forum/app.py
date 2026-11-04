"""CFP+ Forum Service • P0

Backend FastAPI + SQLAlchemy (cùng stack với cfp-gateway) cho hai diễn đàn
tách biệt: Diễn Đàn Siêu Bộ Đôi và Diễn Đàn SI AI • HSTDN.

Tách biệt:
- Dữ liệu: mỗi diễn đàn một database riêng (CFP_FORUM_DB_<KEY>), tài khoản ở
  database auth riêng. Mỗi forum DB được đóng dấu forum_key; khởi động sẽ thất
  bại nếu hai diễn đàn trỏ cùng một database.
- Quyền: thành viên/quản trị tính riêng theo từng diễn đàn.
- Chức năng: cấu hình riêng (quyền đọc, chính sách tham gia, trường bắt buộc).

Không có public route chính thức. UI chỉ phục vụ tại đường dẫn kỹ thuật nội
bộ /_internal/forum/<key>/ cho đến khi Registry phê duyệt Canonical ID.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text,
                        create_engine, func, insert, select, update)
from sqlalchemy.engine import Engine

WEB_DIR = Path(__file__).parent / "web"
SESSION_COOKIE = "cfp_forum_session"
SESSION_TTL = timedelta(days=14)
CSRF_HEADER = "x-cfp-forum"
MAX_BODY_BYTES = 64 * 1024
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                                "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"),
}


class RateLimiter:
    """Cửa sổ trượt trong bộ nhớ (theo tiến trình). Production nhiều instance cần Redis/DB."""

    def __init__(self):
        self._hits: dict[tuple, deque] = {}
        self._lock = threading.Lock()

    def hit(self, key: tuple, limit: int, window: float) -> float:
        """Trả 0 nếu cho phép, ngược lại trả số giây cần chờ."""
        now = time.monotonic()
        with self._lock:
            q = self._hits.setdefault(key, deque())
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                return max(0.0, q[0] + window - now)
            q.append(now)
            if len(self._hits) > 50_000:  # tránh phình bộ nhớ
                self._hits = {k: v for k, v in self._hits.items() if v and v[-1] > now - window}
            return 0.0


def _limits() -> dict[str, tuple[int, float]]:
    def env(name, default):
        return int(os.environ.get(name, default))
    return {
        "auth": (env("CFP_FORUM_RL_AUTH_PER_MIN", 10), 60.0),    # đăng ký/đăng nhập theo IP
        "write": (env("CFP_FORUM_RL_WRITE_PER_MIN", 30), 60.0),  # ghi khác theo IP
    }


# ---------------------------------------------------------------- forums

@dataclass(frozen=True)
class ForumConfig:
    key: str
    title: str
    public_read: bool          # khách chưa đăng nhập có được đọc không
    join_policy: str           # "open" | "approval"
    post_fields: tuple[str, ...]  # trường bổ sung bắt buộc khi đăng bài


FORUMS: dict[str, ForumConfig] = {
    "sieu-bo-doi": ForumConfig("sieu-bo-doi", "Diễn Đàn Siêu Bộ Đôi",
                               public_read=True, join_policy="open", post_fields=()),
    "si-ai-hstdn": ForumConfig("si-ai-hstdn", "Diễn Đàn SI AI • HSTDN",
                               public_read=False, join_policy="approval", post_fields=("hstdn",)),
}


def _env_key(key: str) -> str:
    return key.upper().replace("-", "_")


# ---------------------------------------------------------------- schema

auth_md = MetaData()
users_t = Table("users", auth_md,
                Column("id", Integer, primary_key=True),
                Column("email", String(254), unique=True, nullable=False),
                Column("name", String(60), nullable=False),
                Column("pw_hash", String(255), nullable=False),
                Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()))
sessions_t = Table("sessions", auth_md,
                   Column("token_hash", String(64), primary_key=True),
                   Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
                   Column("expires_at", DateTime(timezone=True), nullable=False))

forum_md = MetaData()
meta_t = Table("forum_meta", forum_md,
               Column("forum_key", String(64), primary_key=True))
members_t = Table("members", forum_md,
                  Column("user_id", Integer, primary_key=True),   # id từ auth DB
                  Column("user_name", String(60), nullable=False),
                  Column("role", String(16), nullable=False, default="member"),      # member|admin
                  Column("status", String(16), nullable=False, default="active"),    # active|pending
                  Column("joined_at", DateTime(timezone=True), nullable=False, server_default=func.now()))
posts_t = Table("posts", forum_md,
                Column("id", Integer, primary_key=True),
                Column("author_id", Integer, nullable=False),
                Column("author_name", String(60), nullable=False),
                Column("title", String(200), nullable=False),
                Column("body", Text, nullable=False),
                Column("hstdn", String(200)),
                Column("country_id", String(32)),
                Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()))
comments_t = Table("comments", forum_md,
                   Column("id", Integer, primary_key=True),
                   Column("post_id", Integer, ForeignKey("posts.id"), nullable=False),
                   Column("author_id", Integer, nullable=False),
                   Column("author_name", String(60), nullable=False),
                   Column("body", Text, nullable=False),
                   Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()))


def _engine(url: str) -> Engine:
    kw = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kw["connect_args"] = {"check_same_thread": False}
    else:
        # Mỗi role diễn đàn trên Supabase có CONNECTION LIMIT 20 (schemas_up.sql #193) → pool nhỏ.
        kw["pool_size"] = int(os.environ.get("CFP_FORUM_POOL_SIZE", "3"))
        kw["max_overflow"] = int(os.environ.get("CFP_FORUM_POOL_OVERFLOW", "2"))
        kw["pool_recycle"] = 300
    return create_engine(url, **kw)


class Stores:
    def __init__(self, auth_url: str, forum_urls: dict[str, str], office_url: str | None = None):
        all_urls = [auth_url, *forum_urls.values()] + ([office_url] if office_url else [])
        if len(set(all_urls)) != len(all_urls):
            raise RuntimeError("Mỗi diễn đàn, auth và Văn Phòng phải dùng database/role riêng biệt.")
        self.auth = _engine(auth_url)
        auth_md.create_all(self.auth)
        self.forums: dict[str, Engine] = {}
        for key, url in forum_urls.items():
            eng = _engine(url)
            forum_md.create_all(eng)
            with eng.begin() as c:
                stamped = c.execute(select(meta_t.c.forum_key)).scalars().all()
                if not stamped:
                    c.execute(insert(meta_t).values(forum_key=key))
                elif stamped != [key]:
                    raise RuntimeError(f"Database của '{key}' đã thuộc về diễn đàn {stamped}.")
            self.forums[key] = eng
        self.office: Engine | None = None
        if office_url:
            from services.forum.office import md as office_md
            self.office = _engine(office_url)
            office_md.create_all(self.office)

    def dispose(self) -> None:
        for eng in [self.auth, *self.forums.values(), *([self.office] if self.office is not None else [])]:
            eng.dispose()

    @classmethod
    def from_env(cls) -> "Stores":
        auth = os.environ.get("CFP_FORUM_AUTH_DB")
        urls = {k: os.environ.get(f"CFP_FORUM_DB_{_env_key(k)}") for k in FORUMS}
        missing = [n for n, v in [("CFP_FORUM_AUTH_DB", auth)] +
                   [(f"CFP_FORUM_DB_{_env_key(k)}", v) for k, v in urls.items()] if not v]
        if missing:
            raise RuntimeError("Thiếu biến môi trường: " + ", ".join(missing))
        return cls(auth, urls, os.environ.get("CFP_OFFICE_DB") or None)


# ---------------------------------------------------------------- auth helpers

def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1)
    return f"scrypt${salt.hex()}${dk.hex()}"


def verify_password(pw: str, stored: str) -> bool:
    try:
        _, salt, dk = stored.split("$")
        got = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1)
        return hmac.compare_digest(got.hex(), dk)
    except Exception:
        return False


def _tok_hash(tok: str) -> str:
    return hashlib.sha256(tok.encode()).hexdigest()


_DUMMY_HASH = hash_password(secrets.token_hex(16))
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class RegisterIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=200)
    name: str = Field(min_length=2, max_length=60)


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=200)


class PostIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)
    hstdn: str | None = Field(default=None, max_length=200)
    country_id: str | None = Field(default=None, max_length=32)


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


# ---------------------------------------------------------------- app

def create_app(stores: Stores | None = None) -> FastAPI:
    app = FastAPI(title="CFP+ Backend API (sandbox)", version="0.2.0-p0", docs_url=None, redoc_url=None,
                  openapi_url="/api/openapi.json",
                  description="API dùng chung: hai diễn đàn, Văn Phòng SI AI, HUB 69, AI Directory (Registry chỉ đọc). "
                              "SANDBOX • NOT DEPLOYED.")
    st = stores or Stores.from_env()
    app.state.stores = st
    limiter = RateLimiter()
    limits = _limits()
    trust_proxy = os.environ.get("CFP_FORUM_TRUST_PROXY", "0") == "1"
    cookie_secure_mode = os.environ.get("CFP_FORUM_COOKIE_SECURE", "1")  # "1" | "0" | "auto"
    allowed_origins = {o.strip().rstrip("/") for o in os.environ.get("CFP_FORUM_ALLOWED_ORIGINS", "").split(",") if o.strip()}

    def client_ip(request: Request) -> str:
        if trust_proxy and request.headers.get("x-forwarded-for"):
            return request.headers["x-forwarded-for"].split(",")[0].strip()
        return request.client.host if request.client else "?"

    def is_https(request: Request) -> bool:
        if trust_proxy and request.headers.get("x-forwarded-proto"):
            return request.headers["x-forwarded-proto"].split(",")[0].strip() == "https"
        return request.url.scheme == "https"

    def origin_ok(request: Request) -> bool:
        origin = request.headers.get("origin")
        if not origin:
            return True  # trình duyệt hiện đại luôn gửi Origin cho fetch POST; header tuỳ chỉnh vẫn bắt buộc
        origin = origin.rstrip("/")
        if origin in allowed_origins:
            return True
        host = request.headers.get("x-forwarded-host") if trust_proxy else None
        host = host or request.headers.get("host", "")
        return origin in {f"https://{host}", f"http://{host}"}

    def deny(status: int, detail: str, headers: dict | None = None):
        return JSONResponse({"detail": detail}, status_code=status, headers={**SECURITY_HEADERS, **(headers or {})})

    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and path.startswith("/api/"):
            # CSRF: header tuỳ chỉnh (form chéo site không gửi được) + Origin phải khớp.
            if request.headers.get(CSRF_HEADER) != "1":
                return deny(403, "Thiếu header chống CSRF.")
            if not origin_ok(request):
                return deny(403, "Origin không được phép.")
            try:
                if int(request.headers.get("content-length") or 0) > MAX_BODY_BYTES:
                    return deny(413, "Yêu cầu quá lớn.")
            except ValueError:
                return deny(400, "Content-Length không hợp lệ.")
            bucket = "auth" if path in {"/api/auth/login", "/api/auth/register"} else "write"
            limit, window = limits[bucket]
            wait = limiter.hit((bucket, client_ip(request)), limit, window)
            if wait:
                return deny(429, "Quá nhiều yêu cầu, vui lòng thử lại sau.", {"Retry-After": str(int(wait) + 1)})
        resp = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            resp.headers.setdefault(k, v)
        if is_https(request):
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return resp

    def current_user(request: Request) -> dict | None:
        tok = request.cookies.get(SESSION_COOKIE)
        if not tok:
            return None
        with st.auth.connect() as c:
            row = c.execute(select(users_t.c.id, users_t.c.email, users_t.c.name, sessions_t.c.expires_at)
                            .join(sessions_t, sessions_t.c.user_id == users_t.c.id)
                            .where(sessions_t.c.token_hash == _tok_hash(tok))).mappings().first()
        if not row:
            return None
        exp = row["expires_at"]
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return None
        return {"id": row["id"], "email": row["email"], "name": row["name"]}

    def require_user(user=Depends(current_user)) -> dict:
        if not user:
            raise HTTPException(401, "Vui lòng đăng nhập.")
        return user

    def forum_cfg(key: str) -> ForumConfig:
        cfg = FORUMS.get(key)
        if not cfg:
            raise HTTPException(404, "Không có diễn đàn này.")
        return cfg

    def membership(key: str, user: dict | None) -> dict | None:
        if not user:
            return None
        with st.forums[key].connect() as c:
            m = c.execute(select(members_t).where(members_t.c.user_id == user["id"])).mappings().first()
        return dict(m) if m else None

    def require_active_member(key: str, user: dict) -> dict:
        m = membership(key, user)
        if not m or m["status"] != "active":
            raise HTTPException(403, "Bạn chưa là thành viên đang hoạt động của diễn đàn này.")
        return m

    def start_session(request: Request, resp: Response, user_id: int) -> None:
        tok = secrets.token_urlsafe(32)
        with st.auth.begin() as c:
            c.execute(insert(sessions_t).values(token_hash=_tok_hash(tok), user_id=user_id,
                                                expires_at=datetime.now(timezone.utc) + SESSION_TTL))
        resp.set_cookie(SESSION_COOKIE, tok, httponly=True, samesite="strict",
                        secure=(is_https(request) if cookie_secure_mode == "auto" else cookie_secure_mode != "0"),
                        max_age=int(SESSION_TTL.total_seconds()), path="/")

    # ---- health
    from services.forum.registry import Registry
    registry = Registry()

    @app.get("/api/health")
    def health():
        out = {"status": "ok", "version": app.version, "build": os.environ.get("RENDER_GIT_COMMIT", "")[:12] or None,
               "auth_db": st.auth.dialect.name, "forums": {},
               "registry": {"entities": len(registry.entities), "read_only": True}}
        for k, eng in st.forums.items():
            with eng.connect() as c:
                out["forums"][k] = {"db": eng.dialect.name,
                                    "stamp": c.execute(select(meta_t.c.forum_key)).scalar_one()}
        if st.office is not None:
            from services.forum.office import offices_t
            with st.office.connect() as c:
                out["office"] = {"db": st.office.dialect.name,
                                 "offices": c.execute(select(func.count()).select_from(offices_t)).scalar_one()}
        else:
            out["office"] = None
        return out

    # ---- auth
    @app.post("/api/auth/register", status_code=201)
    def register(data: RegisterIn, request: Request, resp: Response):
        email = data.email.strip().lower()
        if not EMAIL_RE.match(email):
            raise HTTPException(422, "Email không hợp lệ.")
        with st.auth.begin() as c:
            if c.execute(select(users_t.c.id).where(users_t.c.email == email)).first():
                raise HTTPException(409, "Email đã được đăng ký.")
            uid = c.execute(insert(users_t).values(email=email, name=data.name.strip(),
                                                   pw_hash=hash_password(data.password))
                            .returning(users_t.c.id)).scalar_one()
        start_session(request, resp, uid)
        return {"id": uid, "email": email, "name": data.name.strip()}

    @app.post("/api/auth/login")
    def login(data: LoginIn, request: Request, resp: Response):
        with st.auth.connect() as c:
            row = c.execute(select(users_t).where(users_t.c.email == data.email.strip().lower())).mappings().first()
        # Luôn băm một lần để thời gian phản hồi không lộ email có tồn tại hay không.
        ok = verify_password(data.password, row["pw_hash"] if row else _DUMMY_HASH)
        if not row or not ok:
            raise HTTPException(401, "Email hoặc mật khẩu không đúng.")
        start_session(request, resp, row["id"])
        return {"id": row["id"], "email": row["email"], "name": row["name"]}

    @app.post("/api/auth/logout")
    def logout(request: Request, resp: Response):
        tok = request.cookies.get(SESSION_COOKIE)
        if tok:
            with st.auth.begin() as c:
                c.execute(sessions_t.delete().where(sessions_t.c.token_hash == _tok_hash(tok)))
        resp.delete_cookie(SESSION_COOKIE, path="/")
        return {"ok": True}

    @app.get("/api/auth/me")
    def me(user=Depends(current_user)):
        return {"user": user}

    # ---- forums
    @app.get("/api/forums/{key}")
    def forum_info(key: str, user=Depends(current_user)):
        cfg = forum_cfg(key)
        m = membership(key, user)
        return {"key": cfg.key, "title": cfg.title, "public_read": cfg.public_read,
                "join_policy": cfg.join_policy, "post_fields": list(cfg.post_fields),
                "membership": {"role": m["role"], "status": m["status"]} if m else None}

    @app.post("/api/forums/{key}/join")
    def join(key: str, user=Depends(require_user)):
        cfg = forum_cfg(key)
        if membership(key, user):
            raise HTTPException(409, "Bạn đã gửi yêu cầu hoặc đã là thành viên.")
        status = "active" if cfg.join_policy == "open" else "pending"
        with st.forums[key].begin() as c:
            c.execute(insert(members_t).values(user_id=user["id"], user_name=user["name"],
                                               role="member", status=status))
        return {"status": status}

    @app.get("/api/forums/{key}/members")
    def list_members(key: str, user=Depends(require_user)):
        forum_cfg(key)
        m = require_active_member(key, user)
        if m["role"] != "admin":
            raise HTTPException(403, "Chỉ quản trị viên của diễn đàn này.")
        with st.forums[key].connect() as c:
            rows = c.execute(select(members_t.c.user_id, members_t.c.user_name, members_t.c.role,
                                    members_t.c.status).order_by(members_t.c.user_id)).mappings().all()
        return {"members": [dict(r) for r in rows]}

    @app.post("/api/forums/{key}/members/{member_id}/approve")
    def approve(key: str, member_id: int, user=Depends(require_user)):
        forum_cfg(key)
        m = require_active_member(key, user)
        if m["role"] != "admin":
            raise HTTPException(403, "Chỉ quản trị viên của diễn đàn này.")
        with st.forums[key].begin() as c:
            n = c.execute(update(members_t).where(members_t.c.user_id == member_id,
                                                  members_t.c.status == "pending")
                          .values(status="active")).rowcount
        if not n:
            raise HTTPException(404, "Không có yêu cầu chờ duyệt.")
        return {"status": "active"}

    def can_read(cfg: ForumConfig, user) -> None:
        if cfg.public_read:
            return
        if not user:
            raise HTTPException(401, "Diễn đàn này yêu cầu đăng nhập.")
        require_active_member(cfg.key, user)

    @app.get("/api/forums/{key}/posts")
    def list_posts(key: str, user=Depends(current_user)):
        cfg = forum_cfg(key)
        can_read(cfg, user)
        with st.forums[key].connect() as c:
            posts = c.execute(select(posts_t).order_by(posts_t.c.id.desc())).mappings().all()
            comments = c.execute(select(comments_t).order_by(comments_t.c.id)).mappings().all()
        by_post: dict[int, list] = {}
        for cm in comments:
            by_post.setdefault(cm["post_id"], []).append(_comment_out(cm))
        return {"posts": [_post_out(p, by_post.get(p["id"], [])) for p in posts]}

    @app.post("/api/forums/{key}/posts", status_code=201)
    def create_post(key: str, data: PostIn, user=Depends(require_user)):
        cfg = forum_cfg(key)
        require_active_member(key, user)
        title, body = data.title.strip(), data.body.strip()
        if not title or not body:
            raise HTTPException(422, "Tiêu đề và nội dung không được để trống.")
        values = {"author_id": user["id"], "author_name": user["name"], "title": title, "body": body}
        if "hstdn" in cfg.post_fields:
            hstdn = (data.hstdn or "").strip()
            if not hstdn:
                raise HTTPException(422, "Diễn đàn này yêu cầu trường HSTDN.")
            if data.country_id and not re.fullmatch(r"[0-9]+", data.country_id.strip()):
                raise HTTPException(422, "Mã quốc gia phải là ID số.")
            values.update(hstdn=hstdn, country_id=(data.country_id or "").strip() or None)
        elif data.hstdn or data.country_id:
            raise HTTPException(422, "Diễn đàn này không dùng trường HSTDN.")
        with st.forums[key].begin() as c:
            row = c.execute(insert(posts_t).values(**values).returning(*posts_t.c)).mappings().one()
        return _post_out(row, [])

    @app.post("/api/forums/{key}/posts/{post_id}/comments", status_code=201)
    def create_comment(key: str, post_id: int, data: CommentIn, user=Depends(require_user)):
        forum_cfg(key)
        require_active_member(key, user)
        body = data.body.strip()
        if not body:
            raise HTTPException(422, "Bình luận không được để trống.")
        with st.forums[key].begin() as c:
            if not c.execute(select(posts_t.c.id).where(posts_t.c.id == post_id)).first():
                raise HTTPException(404, "Không tìm thấy bài viết trong diễn đàn này.")
            row = c.execute(insert(comments_t).values(post_id=post_id, author_id=user["id"],
                                                      author_name=user["name"], body=body)
                            .returning(*comments_t.c)).mappings().one()
        return _comment_out(row)

    # ---- Văn Phòng SI AI (kho dữ liệu riêng, tuỳ chọn)
    if st.office is not None:
        from services.forum.office import build_router
        app.include_router(build_router(st.office, registry, current_user))

        @app.get("/_internal/office/office.js")
        def office_js():
            return FileResponse(WEB_DIR / "office.js", media_type="text/javascript")

        @app.get("/_internal/office/{cid}/")
        def office_page(cid: str):
            if not re.fullmatch(r"[0-9]{1,32}", cid):
                raise HTTPException(404)
            return FileResponse(WEB_DIR / "office.html", media_type="text/html",
                                headers={"X-Robots-Tag": "noindex, nofollow"})

    # ---- UI tại đường dẫn kỹ thuật nội bộ (không phải public route)
    @app.get("/styles.css")
    def site_css():  # stylesheet chung của site, chỉ để chạy độc lập trong sandbox
        return FileResponse(WEB_DIR.parents[2] / "styles.css", media_type="text/css")

    @app.get("/_internal/forum/forum.js")
    def ui_js():
        return FileResponse(WEB_DIR / "forum.js", media_type="text/javascript")

    @app.get("/_internal/forum/forum.css")
    def ui_css():
        return FileResponse(WEB_DIR / "forum.css", media_type="text/css")

    @app.get("/_internal/forum/{key}")
    def ui_redirect(key: str):
        forum_cfg(key)
        return RedirectResponse(f"/_internal/forum/{key}/")

    @app.get("/_internal/forum/{key}/")
    def ui_page(key: str):
        forum_cfg(key)
        return FileResponse(WEB_DIR / f"{key}.html", media_type="text/html",
                            headers={"X-Robots-Tag": "noindex, nofollow"})

    from services.forum.hub import build_hub_router
    app.include_router(build_hub_router(registry, st, FORUMS))

    # Gắn tag OpenAPI theo module (dùng cho hợp đồng API và bảng kiểm kê).
    from fastapi.routing import APIRoute
    for route in app.routes:
        if isinstance(route, APIRoute) and not route.tags:
            p = route.path
            route.tags = (["auth"] if p.startswith("/api/auth") else ["forums"] if p.startswith("/api/forums")
                          else ["health"] if p == "/api/health" else ["ui-internal"])
        if isinstance(route, APIRoute) and not route.path.startswith("/api/"):
            route.include_in_schema = False  # trang/tệp tĩnh nội bộ không thuộc hợp đồng API
    app.openapi_schema = None
    return app


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


def _post_out(p, comments):
    return {"id": p["id"], "title": p["title"], "body": p["body"], "hstdn": p["hstdn"],
            "country_id": p["country_id"], "author": {"id": p["author_id"], "name": p["author_name"]},
            "created_at": _iso(p["created_at"]), "comments": comments}


def _comment_out(c):
    return {"id": c["id"], "body": c["body"], "author": {"id": c["author_id"], "name": c["author_name"]},
            "created_at": _iso(c["created_at"])}
