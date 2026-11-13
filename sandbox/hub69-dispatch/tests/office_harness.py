"""Start a REAL PR #195 backend (uvicorn, CFP_SANDBOX_EPHEMERAL=1 → throw-away SQLite) for integration tests
and for the autopilot pilot. Nothing here touches Supabase, Render or GitHub.

Where the #195 code comes from (first match):
  1. HUB69_OFFICE_SRC=<dir>                  e.g. the CI checkout of the pinned SHA
  2. git archive <OFFICE_SHA> from this clone (works locally when the #195 objects are fetched)
Missing → tests skip, unless HUB69_REQUIRE_OFFICE=1 (CI), then they fail.

Accounts: governance + ReviewSI come from #195's own bootstrap env (ephemeral mode only); SecuritySI's
reviewer role is granted with #195's own admin CLI on the same throw-away database. Passwords are random
per run and never written to disk.
"""
from __future__ import annotations

import os
import secrets
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from pathlib import Path

OFFICE_SHA = "29fb46914f72f74d6434a81a03939d8a02f8813b"  # PR #195 head used for this integration
ROOT = Path(__file__).resolve().parents[3]


def office_src() -> Path | None:
    env = os.environ.get("HUB69_OFFICE_SRC")
    if env and (Path(env) / "services" / "forum" / "app.py").is_file():
        return Path(env)
    cache = Path(tempfile.gettempdir()) / f"hub69-office-{OFFICE_SHA[:12]}"
    if (cache / "services" / "forum" / "app.py").is_file():
        return cache
    try:
        tar = subprocess.run(["git", "-C", str(ROOT), "archive", OFFICE_SHA], capture_output=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    tmp = Path(tempfile.mkdtemp())
    p = tmp / "a.tar"
    p.write_bytes(tar)
    with tarfile.open(p) as t:
        t.extractall(cache, filter="data")
    shutil.rmtree(tmp, ignore_errors=True)
    return cache


def deps_ok() -> bool:
    try:
        import fastapi, sqlalchemy, uvicorn  # noqa: F401,E401
        return True
    except ImportError:
        return False


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class OfficeServer:
    """`with OfficeServer() as srv:` → srv.base, srv.secrets, srv.stop()/srv.start() (same data dir = restart)."""

    def __init__(self, src: Path, data_dir: Path | None = None):
        self.src = src
        self.data = Path(data_dir or tempfile.mkdtemp(prefix="hub69-office-"))
        self.data.mkdir(parents=True, exist_ok=True)
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
        pw = secrets.token_urlsafe(18)
        self.secrets = {
            "gov": ("gov@sandbox.invalid", pw),
            "agent_password": secrets.token_urlsafe(18),
            "reviewer": {"ReviewSI": ("reviewsi@sandbox.invalid", pw),
                         "SecuritySI": ("securitysi@sandbox.invalid", secrets.token_urlsafe(18))},
        }
        self.env = {**os.environ, "CFP_SANDBOX_EPHEMERAL": "1", "CFP_EPHEMERAL_DIR": str(self.data),
                    "CFP_BOOTSTRAP_PASSWORD": pw, "CFP_BOOTSTRAP_GOV_EMAIL": "gov@sandbox.invalid",
                    "CFP_BOOTSTRAP_REVIEWER_EMAIL": "reviewsi@sandbox.invalid", "CFP_FORUM_COOKIE_SECURE": "0",
                    "CFP_FORUM_RL_AUTH_PER_MIN": "1000", "CFP_FORUM_RL_WRITE_PER_MIN": "1000",
                    "PYTHONPATH": str(src)}
        for k in [k for k in self.env if k.startswith(("CFP_FORUM_DB_", "CFP_OFFICE_DB", "CFP_WORKER_DB",
                                                        "CFP_FORUM_AUTH_DB"))]:
            self.env.pop(k)
        self.proc = None
        self.log = self.data / "uvicorn.log"

    def start(self):
        self.data.mkdir(parents=True, exist_ok=True)
        fh = open(self.log, "ab")
        self.proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "services.forum.asgi:app", "--host",
                                      "127.0.0.1", "--port", str(self.port)], cwd=self.src, env=self.env,
                                     stdout=fh, stderr=subprocess.STDOUT)
        for _ in range(100):
            try:
                with urllib.request.urlopen(self.base + "/api/health", timeout=1) as r:
                    if r.status == 200:
                        return self
            except OSError:
                time.sleep(0.15)
        raise RuntimeError("PR #195 server did not start: " + self.log.read_text()[-2000:])

    def stop(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(10)
            self.proc = None

    def grant_securitysi(self):
        """#195 admin CLI on the throw-away DB: register SecuritySI then grant reviewer role (sandbox only)."""
        from hub69_dispatch.office_client import OfficeClient
        email, pw = self.secrets["reviewer"]["SecuritySI"]
        OfficeClient(self.base).login(email, pw, register_name="SecuritySI (sandbox placeholder)")
        subprocess.run([sys.executable, "-m", "services.forum.admin", "grant-office-role", "reviewer", email],
                       cwd=self.src, env=self.env, check=True, capture_output=True)

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
