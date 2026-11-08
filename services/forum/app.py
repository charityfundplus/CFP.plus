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
import html
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
from sqlalchemy import text as sql_text
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
    engine = create_engine(url, **kw)
    if url.startswith("sqlite"):
        # pysqlite legacy mode otherwise releases an outermost SAVEPOINT before audit/link writes.
        # Serialize sandbox SQLite transactions so competing retries observe the complete receipt.
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def sqlite_connect(dbapi_connection, _):
            dbapi_connection.isolation_level = None

        @event.listens_for(engine, "begin")
        def sqlite_begin(conn):
            conn.exec_driver_sql("BEGIN IMMEDIATE")
    return engine


class HeadAsGet:
    """HEAD = GET không có body (RFC 9110). Uptime monitor/health check của Render gửi HEAD; trước đây 405."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "HEAD":
            return await self.app(scope, receive, send)

        async def send_no_body(msg):
            if msg["type"] == "http.response.body":
                msg = {**msg, "body": b""}
            await send(msg)
        return await self.app({**scope, "method": "GET"}, receive, send_no_body)


EPHEMERAL_BANNER = (
    '<div class="sandbox-ephemeral" role="alert" data-testid="ephemeral-banner">'
    '<strong>⚠️ DỮ LIỆU THỬ NGHIỆM</strong> — Sandbox lưu tạm: dữ liệu có thể <strong>mất khi máy chủ khởi động lại</strong>. '
    'Không nhập tài liệu, mật khẩu hay thông tin quan trọng. Chưa có lưu trữ bền vững/sao lưu.</div>')


class EphemeralBanner:
    """Chế độ CFP_SANDBOX_EPHEMERAL: chèn cảnh báo dữ liệu thử nghiệm vào MỌI trang HTML (quyết định 06/11)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        state = {"html": False, "start": None, "chunks": []}

        async def wrapped(msg):
            if msg["type"] == "http.response.start":
                ctype = dict(msg.get("headers") or []).get(b"content-type", b"")
                if ctype.startswith(b"text/html"):
                    state["html"], state["start"] = True, msg
                    return
                return await send(msg)
            if msg["type"] == "http.response.body" and state["html"]:
                state["chunks"].append(msg.get("body", b""))
                if msg.get("more_body"):
                    return
                body = b"".join(state["chunks"])
                body = re.sub(rb"(<body[^>]*>)", lambda m: m.group(1) + EPHEMERAL_BANNER.encode(), body, count=1)
                headers = [(k, v) for k, v in state["start"]["headers"] if k != b"content-length"]
                headers.append((b"content-length", str(len(body)).encode()))
                await send({**state["start"], "headers": headers})
                return await send({"type": "http.response.body", "body": body})
            return await send(msg)
        return await self.app(scope, receive, wrapped)


class Stores:
    def __init__(self, auth_url: str, forum_urls: dict[str, str], office_url: str | None = None,
                 worker_url: str | None = None):
        all_urls = [auth_url, *forum_urls.values()] + [u for u in (office_url, worker_url) if u]
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
        self.ephemeral = False  # True: SQLite tạm trên đĩa của instance (CFP_SANDBOX_EPHEMERAL=1)
        self.worker: Engine | None = None
        if worker_url:  # kho riêng của Worker P0 (004_worker.sql); app chỉ ĐỌC trạng thái
            from services.forum.worker import engine_for
            self.worker = engine_for(worker_url)

    def dispose(self) -> None:
        for eng in [self.auth, *self.forums.values(), *[e for e in (self.office, self.worker) if e is not None]]:
            eng.dispose()

    @classmethod
    def from_env(cls) -> "Stores":
        if os.environ.get("CFP_SANDBOX_EPHEMERAL") == "1":
            return cls.ephemeral_sandbox()
        auth = os.environ.get("CFP_FORUM_AUTH_DB")
        urls = {k: os.environ.get(f"CFP_FORUM_DB_{_env_key(k)}") for k in FORUMS}
        missing = [n for n, v in [("CFP_FORUM_AUTH_DB", auth)] +
                   [(f"CFP_FORUM_DB_{_env_key(k)}", v) for k, v in urls.items()] if not v]
        if missing:
            raise RuntimeError("Thiếu biến môi trường: " + ", ".join(missing))
        return cls(auth, urls, os.environ.get("CFP_OFFICE_DB") or None, os.environ.get("CFP_WORKER_DB") or None)

    @classmethod
    def ephemeral_sandbox(cls) -> "Stores":
        """SANDBOX tạm: mỗi kho một tệp SQLite riêng trên đĩa của instance — không cần secrets DB,
        không đụng Supabase/migration. Dữ liệu MẤT khi instance khởi động lại; health/ops báo rõ."""
        names = ["CFP_FORUM_AUTH_DB", *[f"CFP_FORUM_DB_{_env_key(k)}" for k in FORUMS], "CFP_OFFICE_DB", "CFP_WORKER_DB"]
        mixed = [n for n in names if os.environ.get(n)]
        if mixed:  # không trộn kho tạm với kho thật
            raise RuntimeError("CFP_SANDBOX_EPHEMERAL=1 không dùng cùng " + ", ".join(mixed))
        d = Path(os.environ.get("CFP_EPHEMERAL_DIR", "/tmp/cfp-sandbox-ephemeral"))
        d.mkdir(parents=True, exist_ok=True)
        u = lambda n: f"sqlite:///{d / n}.db"  # noqa: E731
        st = cls(u("auth"), {k: u(f"forum-{k}") for k in FORUMS}, u("office"), u("worker"))
        st.ephemeral = True
        return st

    def bootstrap_ephemeral(self) -> list[str]:
        """Chỉ ở chế độ tạm: tạo sẵn tài khoản governance/reviewer TRƯỚC khi nhận request, mật khẩu lấy
        từ secret CFP_BOOTSTRAP_PASSWORD (không ghi log). Tài khoản đã tồn tại mà mật khẩu không khớp
        → không cấp vai trò (chống chiếm email). Trả về danh sách vai trò đã cấp (để ghi log, không có mật khẩu)."""
        from services.forum.office import roles_t
        pw = os.environ.get("CFP_BOOTSTRAP_PASSWORD", "")
        want = [(os.environ.get("CFP_BOOTSTRAP_GOV_EMAIL", ""), "governance"),
                (os.environ.get("CFP_BOOTSTRAP_REVIEWER_EMAIL", ""), "reviewer")]
        if not self.ephemeral or self.office is None or len(pw) < 12:
            return []
        done = []
        for email, role in want:
            email = email.strip().lower()
            if not email:
                continue
            with self.auth.begin() as c:
                row = c.execute(select(users_t).where(users_t.c.email == email)).mappings().first()
                if row is None:
                    uid = c.execute(insert(users_t).values(email=email, name=f"Sandbox {role}", pw_hash=hash_password(pw))
                                    .returning(users_t.c.id)).scalar_one()
                elif verify_password(pw, row["pw_hash"]):
                    uid = row["id"]
                else:
                    done.append(f"SKIP {role}: tài khoản có sẵn, mật khẩu không khớp")
                    continue
            with self.office.begin() as c:
                if not c.execute(select(roles_t.c.user_id).where(roles_t.c.user_id == uid, roles_t.c.role == role)).first():
                    c.execute(insert(roles_t).values(user_id=uid, role=role))
            if role == "governance":  # quản trị cả hai diễn đàn để duyệt thành viên SI AI • HSTDN
                for eng in self.forums.values():
                    with eng.begin() as c:
                        if not c.execute(select(members_t.c.user_id).where(members_t.c.user_id == uid)).first():
                            c.execute(insert(members_t).values(user_id=uid, user_name=f"Sandbox {role}",
                                                               role="admin", status="active"))
            done.append(f"{role}: {email}")
        return done


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


class KillSwitchIn(BaseModel):
    paused: bool
    reason: str = Field(min_length=3, max_length=300)


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
    if st.ephemeral:
        app.add_middleware(EphemeralBanner)
    app.add_middleware(HeadAsGet)
    if st.ephemeral:
        for line in st.bootstrap_ephemeral():
            print(f"[cfp-sandbox] bootstrap {line}", flush=True)
    limiter = RateLimiter()
    limits = _limits()
    trust_proxy = os.environ.get("CFP_FORUM_TRUST_PROXY", "0") == "1"
    # Số proxy tin cậy đứng trước app (Render: 1). Chỉ lấy IP do proxy cuối cùng ghi vào X-Forwarded-For;
    # các giá trị bên trái do client tự gửi nên không tin (SEC-P0-195-05).
    proxy_hops = max(1, int(os.environ.get("CFP_FORUM_TRUSTED_PROXY_HOPS", "1")))
    cookie_secure_mode = os.environ.get("CFP_FORUM_COOKIE_SECURE", "1")  # "1" | "0" | "auto"
    allowed_origins = {o.strip().rstrip("/") for o in os.environ.get("CFP_FORUM_ALLOWED_ORIGINS", "").split(",") if o.strip()}

    def client_ip(request: Request) -> str:
        if trust_proxy and request.headers.get("x-forwarded-for"):
            hops = [h.strip() for h in request.headers["x-forwarded-for"].split(",") if h.strip()]
            if len(hops) >= proxy_hops:
                return hops[-proxy_hops]
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
        # Không dùng X-Forwarded-Host (client có thể giả mạo); chỉ Host + danh sách CFP_FORUM_ALLOWED_ORIGINS.
        host = request.headers.get("host", "").strip().lower()
        return origin.lower() in {f"https://{host}", f"http://{host}"}

    def deny(status: int, detail: str, headers: dict | None = None):
        return JSONResponse({"detail": detail}, status_code=status, headers={**SECURITY_HEADERS, **(headers or {})})

    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/office") and st.office is not None:
            # Danh tính cho RLS theo người dùng ở Postgres (003). Không có phiên → None (fail-closed).
            from starlette.concurrency import run_in_threadpool
            from services.forum.office import ACTOR
            u = await run_in_threadpool(current_user, request)
            ACTOR.set(u["id"] if u else None)
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
    from services.forum.catalog import Catalog
    catalog = Catalog(registry)
    app.state.catalog = catalog

    @app.get("/api/health")
    def health():
        out = {"status": "ok", "version": app.version, "build": os.environ.get("RENDER_GIT_COMMIT", "") or None,
               "storage": ("ephemeral-sqlite: dữ liệu mất khi instance khởi động lại" if st.ephemeral else "configured"),
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
        if st.ephemeral:
            out["data_inventory"] = data_inventory()
        return out

    def data_inventory() -> dict:
        """Chế độ tạm: đếm dữ liệu do NGƯỜI THẬT tạo (khác tài khoản thử nghiệm @example.org và tài khoản bootstrap)
        — điều kiện an toàn trước mỗi lần deploy/khởi động lại (dữ liệu tạm sẽ mất). Chỉ số đếm, không lộ nội dung."""
        boot = {os.environ.get(n, "").strip().lower() for n in ("CFP_BOOTSTRAP_GOV_EMAIL", "CFP_BOOTSTRAP_REVIEWER_EMAIL")}
        with st.auth.connect() as c:
            users = c.execute(select(users_t.c.id, users_t.c.email)).all()
        real = {u.id for u in users if not (u.email.endswith("@example.org") or u.email in boot)}
        posts = comments = 0
        for eng in st.forums.values():
            with eng.connect() as c:
                posts += sum(1 for (a,) in c.execute(select(posts_t.c.author_id)) if a in real)
                comments += sum(1 for (a,) in c.execute(select(comments_t.c.author_id)) if a in real)
        tasks = 0
        if st.office is not None:
            from services.forum.office import tasks_t as _tasks
            with st.office.connect() as c:
                tasks = sum(1 for (a, b, cr) in c.execute(select(_tasks.c.assignee_id, _tasks.c.reviewer_id,
                                                                   _tasks.c.created_by)) if {a, b, cr} & real)
        n = len(real) + posts + comments + tasks
        return {"real_users": len(real), "real_posts": posts, "real_comments": comments, "real_tasks": tasks,
                "test_users": len(users) - len(real), "safe_to_restart": n == 0}

    # ---- Worker P0: trạng thái chỉ đọc (heartbeat, số việc, cảnh báo) — không có thao tác ghi qua HTTP
    @app.get("/api/worker/status", tags=["worker"])
    def worker_status():
        if st.worker is None:
            return {"mode": "SANDBOX", "configured": False, "alive": False,
                    "note": "Chưa cấu hình CFP_WORKER_DB: không có worker chạy."}
        from services.forum.worker import status
        return {"configured": True, **status(st.worker)}

    @app.post("/api/worker/control", tags=["worker"])
    def worker_control(data: KillSwitchIn, user=Depends(require_user)):
        """Kill switch qua HTTP (Render Free không có shell): CHỈ governance của Văn Phòng SI AI.
        Ghi nhật ký append-only của worker (event=kill_switch, danh tính người bấm, lý do).
        Kho thật (Postgres) cần CFP_WORKER_ADMIN_DB (role được SET ROLE worker_governance)."""
        if st.worker is None or st.office is None:
            raise HTTPException(503, "Chưa cấu hình worker/Văn Phòng.")
        from services.forum.office import roles_t
        with st.office.begin() as c:
            if st.office.dialect.name == "postgresql":  # RLS 003: danh tính theo giao dịch
                c.execute(sql_text("select set_config('cfp.user_id', :u, true)"), {"u": str(user["id"])})
            gov = c.execute(select(roles_t.c.user_id).where(roles_t.c.user_id == user["id"],
                                                           roles_t.c.role == "governance")).first()
        if not gov:
            raise HTTPException(403, "Chỉ governance được bật/tắt worker.")
        admin = (st.worker.url.render_as_string(hide_password=False) if st.ephemeral
                 else os.environ.get("CFP_WORKER_ADMIN_DB"))
        if not admin:
            raise HTTPException(503, "Kill switch HTTP chưa cấu hình (CFP_WORKER_ADMIN_DB); dùng CLI quản trị.")
        from services.forum.worker import set_paused, status
        set_paused(admin, data.paused, f"user:{user['id']} • {data.reason.strip()}")
        return {"paused": status(st.worker)["paused"]}

    if st.worker is not None and os.environ.get("CFP_WORKER_INPROCESS") == "1":
        # Render Free chỉ có web service: chạy worker trong cùng tiến trình (1 uvicorn worker).
        # Instance Free ngủ khi không có truy cập → heartbeat sẽ trễ; status báo đúng điều đó.
        from services.forum.worker import Worker
        threading.Thread(target=Worker(st.worker).run_forever,
                         kwargs={"interval": float(os.environ.get("CFP_WORKER_INTERVAL", "30"))},
                         name="cfp-worker", daemon=True).start()

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
        return new_post(key, data, user)

    def new_post(key: str, data: PostIn, user: dict) -> dict:
        """Một đường duy nhất tạo bài (API diễn đàn + mở thảo luận từ nhiệm vụ Văn Phòng): cùng quy tắc quyền."""
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
        def forum_can_read(key: str, user: dict | None) -> bool:
            if key not in st.forums:
                return False
            try:
                can_read(forum_cfg(key), user)
                return True
            except HTTPException:
                return False

        bridge = {"keys": tuple(st.forums), "can_read": forum_can_read,
                  "create_post": lambda key, d, user: new_post(key, PostIn(**d), user)}
        app.include_router(build_router(st.office, registry, current_user, forums=bridge, catalog=catalog))

        @app.get("/_internal/office/office.js")
        def office_js():
            return FileResponse(WEB_DIR / "office.js", media_type="text/javascript")

        @app.get("/_internal/office/directory.js")
        def directory_js():
            return FileResponse(WEB_DIR / "directory.js", media_type="text/javascript")

        @app.get("/_internal/office/")
        def office_directory():
            return FileResponse(WEB_DIR / "directory.html", media_type="text/html",
                                headers={"X-Robots-Tag": "noindex, nofollow"})

        @app.get("/_internal/office/{cid}/")
        def office_page(cid: str):
            if not re.fullmatch(r"[0-9]{1,32}", cid):
                raise HTTPException(404)
            return FileResponse(WEB_DIR / "office.html", media_type="text/html",
                                headers={"X-Robots-Tag": "noindex, nofollow"})

        @app.get("/_internal/ops/ops.js")
        def ops_js():
            return FileResponse(WEB_DIR / "ops.js", media_type="text/javascript")

        @app.get("/_internal/ops/")
        def ops_page():  # bảng điều phối chỉ đọc; dữ liệu nhiệm vụ lọc theo quyền ở /api/office/board
            return FileResponse(WEB_DIR / "ops.html", media_type="text/html",
                                headers={"X-Robots-Tag": "noindex, nofollow"})

    # ---- UI tại đường dẫn kỹ thuật nội bộ (không phải public route)
    @app.get("/search.js", include_in_schema=False)  # ô tìm ID của website tĩnh (/69/, /0123456789/)
    def site_search_js():
        return FileResponse(WEB_DIR.parents[2] / "search.js", media_type="text/javascript")

    @app.get("/search-index.json", include_in_schema=False)  # sinh bởi scripts/build_search_index.py
    def site_search_index():
        return FileResponse(WEB_DIR.parents[2] / "search-index.json", media_type="application/json")

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

    # ---- Link Mẫu • danh mục công trình (chỉ đọc; chỉ trang ID số đã xuất bản + Registry; không cấp ID)
    from services.forum.catalog import MODULES as LINK_MODULES, PENDING, SANDBOX

    @app.get("/api/catalog", tags=["catalog"])
    def catalog_search(q: str | None = None, limit: int = 50):
        limit = max(1, min(limit, 200))
        return {"total": len(catalog.items), "items": catalog.search(q, limit),
                "source": "repo: trang <ID>/index.html đã xuất bản + Registry (parent)"}

    @app.get("/api/catalog/meta", tags=["catalog"])
    def catalog_meta():
        return {"modules": [{"n": n, "name": name, "status": st_} for n, name, st_ in LINK_MODULES],
                "sandbox": [dict(x, classification="INTERNAL") for x in SANDBOX],
                "pending": [dict(x, status="pending_verification", canonical_id=None) for x in PENDING],
                "registry_conflicts": registry.conflicts,  # cùng ID, khác nguồn: báo, không tự chọn/ghi đè
                "parent_counts": {s_: sum(1 for i in catalog.items.values() if i["parent_status"] == s_)
                                  for s_ in ("registry", "inferred_prefix", "pending_verification", "hold_conflict", "parent_hold")},
                "holds": catalog.holds}

    @app.get("/api/catalog/{cid}", tags=["catalog"])
    def catalog_item(cid: str):
        item = catalog.items.get(cid)
        if not item:
            raise HTTPException(404, "Chưa có trang ID này trong nguồn đã xác minh (không tự cấp ID).")
        children = [c for c in catalog.items.values() if c["parent_id"] == cid]
        return {**item, "children": [{"canonical_id": c["canonical_id"], "title": c["title"]} for c in children]}

    @app.get("/_internal/catalog/catalog.js", include_in_schema=False)
    def catalog_js():
        return FileResponse(WEB_DIR / "catalog.js", media_type="text/javascript")

    @app.get("/_internal/catalog/", include_in_schema=False)
    def catalog_page():
        return FileResponse(WEB_DIR / "catalog.html", media_type="text/html",
                            headers={"X-Robots-Tag": "noindex, nofollow"})

    from services.forum.ecosystem import ctttc_date, ctttc_days, ecosystem_map

    @app.get("/api/ecosystem", tags=["ecosystem"])
    def ecosystem():
        return ecosystem_map(catalog, office_on=st.office is not None)

    @app.get("/api/ecosystem/ctttc/days", tags=["ecosystem"])
    def ctttc_days_api(year: int | None = None):
        if year is not None and not 1 <= year <= 9999:
            raise HTTPException(422, "Năm 1–9999.")
        return ctttc_days(year)

    @app.get("/api/ecosystem/ctttc/date/{date_id}", tags=["ecosystem"])
    def ctttc_date_api(date_id: str):
        try:
            return ctttc_date(date_id)
        except ValueError as ex:
            raise HTTPException(422, str(ex)) from None

    for _name in ("map", "linkmau"):
        def _js(_n=_name):
            return FileResponse(WEB_DIR / f"{_n}.js", media_type="text/javascript")
        app.add_api_route(f"/_internal/{_name}/{_name}.js", _js, include_in_schema=False)

    @app.get("/_internal/map/", include_in_schema=False)
    def map_page():
        return FileResponse(WEB_DIR / "map.html", media_type="text/html", headers={"X-Robots-Tag": "noindex, nofollow"})

    if st.office is not None:  # Văn Phòng Siêu Bộ Đôi (tích hợp Canva) • INTERNAL • noindex
        @app.get("/_internal/van-phong-sieu-bo-doi/vpsbd.js", include_in_schema=False)
        def vpsbd_js():
            return FileResponse(WEB_DIR / "vpsbd.js", media_type="text/javascript")

        @app.get("/_internal/van-phong-sieu-bo-doi/", include_in_schema=False)
        def vpsbd_page():
            return FileResponse(WEB_DIR / "vpsbd.html", media_type="text/html", headers={"X-Robots-Tag": "noindex, nofollow"})

    if st.office is not None:
        @app.get("/_internal/linkmau/{cid}/", include_in_schema=False)
        def linkmau_page(cid: str):
            if cid not in catalog.items:
                raise HTTPException(404)
            return FileResponse(WEB_DIR / "linkmau.html", media_type="text/html",
                                headers={"X-Robots-Tag": "noindex, nofollow"})

    if st.office is not None:  # Văn Phòng Agent (đào tạo) • INTERNAL • noindex • không phải link công bố
        @app.get("/_internal/agent/agent.js", include_in_schema=False)
        def agent_js():
            return FileResponse(WEB_DIR / "agent.js", media_type="text/javascript")

        @app.get("/_internal/agent/{slug}/", include_in_schema=False)
        def agent_page(slug: str):
            from services.forum.agents import load_agents
            if slug not in load_agents():
                raise HTTPException(404)
            return FileResponse(WEB_DIR / "agent.html", media_type="text/html",
                                headers={"X-Robots-Tag": "noindex, nofollow"})

    # ---- Khung website trong SANDBOX (cờ CFP_SANDBOX_WEBSITE, mặc định bật; "0" để tắt).
    # Phục vụ CHỈ ĐỌC các trang tĩnh có sẵn trong repo (/, /{ID số}/) và chèn thanh lối vào
    # Siêu Bộ Đôi • Văn Phòng • Diễn Đàn • Bảng điều phối. Không sửa tệp tĩnh, không tạo route
    # Canonical mới, không cấp ID: chỉ ID đã có thư mục trong repo. noindex: bản chính là cfp.plus.
    if os.environ.get("CFP_SANDBOX_WEBSITE", "1") != "0":
        site_root = WEB_DIR.parents[2]
        office_on = st.office is not None

        def site_page(rel: Path, cid: str | None) -> Response:
            f = site_root / rel
            if not f.is_file():
                raise HTTPException(404)
            links = [("/_internal/office/", "HUB 69 • Văn Phòng SI AI"),
                     ("/_internal/forum/sieu-bo-doi/", "Diễn Đàn Siêu Bộ Đôi"),
                     ("/_internal/forum/si-ai-hstdn/", "Diễn Đàn SI AI • HSTDN"),
                     ("/_internal/ops/", "Bảng điều phối"),
                     ("/_internal/catalog/", "Danh mục Link Mẫu"),
                     ("/_internal/map/", "Bản đồ hệ sinh thái"),
                     ("/_internal/van-phong-sieu-bo-doi/", "Văn Phòng Siêu Bộ Đôi")]
            if cid and office_on and cid in catalog.items:
                links.insert(0, (f"/_internal/linkmau/{cid}/", f"Link Mẫu {cid}"))
            if cid and office_on and registry.get(cid) is not None:
                links.insert(0, (f"/_internal/office/{cid}/", f"Văn Phòng {cid}"))
            if not office_on:
                links = [x for x in links if not x[0].startswith(("/_internal/office/", "/_internal/ops/"))]
            bar = ('<div class="sandbox-entry" data-testid="sandbox-entry" role="region" aria-label="Lối vào sandbox">'
                   '<strong>SANDBOX • Siêu Bộ Đôi</strong> · '
                   + " · ".join(f'<a href="{h}">{html.escape(t)}</a>' for h, t in links)
                   + ' · <span>PRODUCTION NO GO</span></div>')
            page = f.read_text(encoding="utf-8")
            if cid == "69":
                # Enrich this sandbox response from the existing catalog. The source HUB page,
                # Registry, Canonical ID and production website remain the original files.
                fragment = (WEB_DIR / "all-in-one.html").read_text(encoding="utf-8")
                if not office_on:
                    fragment = re.sub(r'<nav class="aio-shortcuts".*?</nav>', '', fragment, count=1, flags=re.S)
                page = re.sub(r'<section class="hero">.*?</section>', lambda _m: fragment,
                              page, count=1, flags=re.S)
                page = page.replace("</head>", '<link rel="stylesheet" href="/_internal/site/all-in-one.css">'
                                    '<script src="/_internal/site/all-in-one.js" defer></script></head>', 1)
            page = page.replace("</head>", '<link rel="stylesheet" href="/_internal/site/sandbox.css"></head>', 1)
            page = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + bar, page, count=1)
            return Response(page, media_type="text/html; charset=utf-8",
                            headers={"X-Robots-Tag": "noindex, nofollow", "Cache-Control": "no-store"})

        @app.get("/_internal/site/sandbox.css", include_in_schema=False)
        def site_sandbox_css():
            return FileResponse(WEB_DIR / "sandbox.css", media_type="text/css")

        @app.get("/_internal/site/all-in-one.css", include_in_schema=False)
        def site_all_in_one_css():
            return FileResponse(WEB_DIR / "all-in-one.css", media_type="text/css")

        @app.get("/_internal/site/all-in-one.js", include_in_schema=False)
        def site_all_in_one_js():
            return FileResponse(WEB_DIR / "all-in-one.js", media_type="text/javascript")

        @app.get("/", include_in_schema=False)
        def site_home():
            return site_page(Path("index.html"), None)

        @app.get("/robots.txt", include_in_schema=False)
        def site_robots():  # bản sandbox không được lập chỉ mục
            return Response("User-agent: *\nDisallow: /\n", media_type="text/plain")

        @app.get("/{cid}/", include_in_schema=False)
        def site_id_page(cid: str):
            if not re.fullmatch(r"[0-9]{1,32}", cid):
                raise HTTPException(404)
            return site_page(Path(cid) / "index.html", cid)

        @app.get("/{cid}", include_in_schema=False)
        def site_id_redirect(cid: str):
            if not re.fullmatch(r"[0-9]{1,32}", cid) or not (site_root / cid / "index.html").is_file():
                raise HTTPException(404)
            return RedirectResponse(f"/{cid}/")

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
