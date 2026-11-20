"""Canva → #195 → autopilot → reviewer, end to end, with a backend restart in the middle.

  python3 sandbox/hub69-dispatch/canva_e2e.py --office-src <checkout of PR #195 with services/forum/web/canva-code.html> \\
      --pg "postgresql+psycopg://%s@localhost:5433/<db prepared by tests/forum/setup_pg.sh <db> --no-003>" --out <dir>

What is REAL here: the #195 backend (Postgres, the same migrations as Supabase sandbox: #193 + 002), the Canva client file,
a real Chromium (iPhone 13 emulation) clicking in a sandboxed iframe on another origin, the autopilot.
What is NOT: Canva itself (its Canva Code iframe/CSP is not reachable from this runtime), HTTPS (local http), the people
(accounts are test accounts driven by the script), the review (left for a real reviewer — the script never clicks it).
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "tests"))

from hub69_dispatch.adapters import ForumSource  # noqa: E402
from hub69_dispatch.autopilot import Autopilot  # noqa: E402
from hub69_dispatch.cli import load_config  # noqa: E402
from hub69_dispatch.office_client import OfficeClient  # noqa: E402
from office_harness import free_port  # noqa: E402

BRANCH = "claude/cool-euler-gnwkfm"


class Backend:
    def __init__(self, src: Path, pg: str, embed: str, log: Path):
        self.src, self.port, self.log = src, free_port(), log
        self.base = f"http://127.0.0.1:{self.port}"
        self.env = {**os.environ, "PYTHONPATH": str(src), "CFP_FORUM_COOKIE_SECURE": "0",
                    "CFP_FORUM_AUTH_DB": pg % "cfp_forum_auth_rw", "CFP_FORUM_DB_SIEU_BO_DOI": pg % "cfp_forum_sbd_rw",
                    "CFP_FORUM_DB_SI_AI_HSTDN": pg % "cfp_forum_hstdn_rw", "CFP_OFFICE_DB": pg % "office_app",
                    "CFP_OFFICE_ADMIN_DB": pg % "cfp_migrator", "CFP_EMBED_ORIGINS": embed,
                    "CFP_FORUM_RL_AUTH_PER_MIN": "1000", "CFP_FORUM_RL_WRITE_PER_MIN": "1000"}
        self.env.pop("CFP_SANDBOX_EPHEMERAL", None)
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "services.forum.asgi:app", "--port", str(self.port)],
                                     cwd=self.src, env=self.env, stdout=open(self.log, "ab"), stderr=subprocess.STDOUT)
        for _ in range(100):
            try:
                with urllib.request.urlopen(self.base + "/api/health", timeout=1) as r:
                    return json.load(r)
            except OSError:
                time.sleep(0.15)
        raise RuntimeError(self.log.read_text()[-2000:])

    def stop(self):
        self.proc.terminate()
        self.proc.wait(10)

    def grant(self, role: str, email: str):
        subprocess.run([sys.executable, "-m", "services.forum.admin", "grant-office-role", role, email],
                       cwd=self.src, env=self.env, check=True, capture_output=True)


def serve_static(d: Path) -> tuple[int, http.server.ThreadingHTTPServer]:
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(d))
    h.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv.server_address[1], srv


def browser(phase: int, args: dict, out: Path) -> list[dict]:
    f = out / f"browser-args-{phase}.json"
    f.write_text(json.dumps(args), encoding="utf-8")
    r = subprocess.run(["node", str(HERE / "canva_e2e_browser.cjs"), str(phase), str(f)], capture_output=True, text=True,
                       timeout=300, env={**os.environ, "NODE_PATH": subprocess.run(["npm", "root", "-g"], capture_output=True,
                                                                                    text=True).stdout.strip()})
    f.unlink()
    line = [x for x in r.stdout.splitlines() if x.startswith("{")]
    if not line:
        raise RuntimeError(r.stderr[-3000:])
    return json.loads(line[-1])["checks"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--office-src", required=True)
    ap.add_argument("--pg", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src, out = Path(a.office_src), Path(a.out)
    client_file = src / "services" / "forum" / "web" / "canva-code.html"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("*.png"):
        f.unlink()
    tmp = Path(tempfile.mkdtemp(prefix="canva-e2e-"))
    static = tmp / "static"
    static.mkdir()
    shutil.copy(client_file, static / "canva-code.html")
    sport, ssrv = serve_static(static)
    backend = Backend(src, a.pg, f"null,http://127.0.0.1:{sport}", tmp / "backend.log")
    (static / "host.html").write_text(
        "<!doctype html><meta name=viewport content='width=device-width,initial-scale=1'><title>Mô phỏng khung Canva</title>"
        "<style>body{margin:0}iframe{border:0;width:100vw;height:100vh}</style>"
        f"<iframe id=canva sandbox='allow-scripts allow-forms' src='canva-code.html?api={backend.base}'></iframe>",
        encoding="utf-8")
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pw = lambda: secrets.token_urlsafe(14)  # noqa: E731
    acct = lambda k, n: {"email": f"{k}-{run.lower()}@sandbox.invalid", "password": pw(), "name": n}  # noqa: E731
    users = {"A": acct("a", "Thành viên A"), "B": acct("b", "Thành viên B"),
             "gov": acct("gov", "Governance sandbox"), "ReviewSI": acct("reviewsi", "ReviewSI (sandbox)")}
    report = {"run": run, "office_src_head": subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True,
                                                            text=True).stdout.strip(),
              "client_sha256": hashlib.sha256(client_file.read_bytes()).hexdigest(),
              "storage": None, "checks": [], "autopilot": None}
    try:
        h = backend.start()
        if json.load(urllib.request.urlopen(backend.base + "/api/forums/sieu-bo-doi/posts"))["posts"]:
            raise SystemExit("cần database MỚI (tests/forum/setup_pg.sh <db> --no-003): Diễn Đàn đã có bài")
        report["storage"] = {"auth_db": h.get("auth_db"), "office": h.get("office"), "storage": h.get("storage")}
        for k in ("gov", "ReviewSI"):
            OfficeClient(backend.base).login(users[k]["email"], users[k]["password"], register_name=users[k]["name"])
        backend.grant("governance", users["gov"]["email"])
        backend.grant("reviewer", users["ReviewSI"]["email"])
        args = {"host_url": f"http://127.0.0.1:{sport}/host.html", "out": str(out), "userA": users["A"], "userB": users["B"],
                "reviewer": users["ReviewSI"], "post_title": f"Chào Diễn Đàn từ Canva {run}",
                "reply_text": f"B đã đọc và phản hồi {run}", "task_title": f"Kiểm tra toàn vẹn Registry từ Canva {run}"}
        report["checks"] += [{"phase": 1, **c} for c in browser(1, args, out)]

        agents_doc, policy = load_config()
        agents = {x["key"]: x for x in agents_doc["agents"]}
        state = tmp / "autopilot"
        evb = f"https://github.com/charityfundplus/CFP.plus/blob/{BRANCH}/sandbox/hub69-dispatch/evidence/canva-e2e/results"
        secrets_ = {"gov": (users["gov"]["email"], users["gov"]["password"]), "agent_password": pw(),
                    "reviewer": {"ReviewSI": (users["ReviewSI"]["email"], users["ReviewSI"]["password"])}}
        pilot = Autopilot(base=backend.base, state_dir=state, agents=agents, policy=policy, secrets=secrets_,
                          evidence_base=evb, office_src=src, forum_reply=True)
        res = pilot.tick(ForumSource(f"{backend.base}#sieu-bo-doi"), datetime.now(timezone.utc), "canva-tick-1")
        res2 = pilot.tick(ForumSource(f"{backend.base}#sieu-bo-doi"), datetime.now(timezone.utc), "canva-tick-2")
        report["autopilot"] = {"tick1": {k: res[k] for k in ("handled", "replies", "rejections")},
                               "tick2": {k: res2[k] for k in ("handled", "replies")}, "status": pilot.store.status()}
        key = next(r["task"] for r in res["handled"])
        report["checks"].append({"phase": "autopilot", "name": "Bộ điều phối nhận bài nhiệm vụ từ Diễn Đàn và chuyển reviewer",
                                 "pass": res["handled"][0]["stage"] == "HANDED_TO_REVIEWER", "detail": res["handled"]})
        report["checks"].append({"phase": "autopilot", "name": "Lượt 2 không ghi trùng (Office + phản hồi)",
                                 "pass": res2["replies"] == [] and all(not h["changed"] for h in res2["handled"])})
        before = pilot.readback(key)
        posts_before = json.load(urllib.request.urlopen(backend.base + "/api/forums/sieu-bo-doi/posts"))["posts"]

        backend.stop()
        backend.start()  # same Postgres: restart must not lose anything
        posts_after = json.load(urllib.request.urlopen(backend.base + "/api/forums/sieu-bo-doi/posts"))["posts"]
        pilot2 = Autopilot(base=backend.base, state_dir=state, agents=agents, policy=policy, secrets=secrets_,
                           evidence_base=evb, office_src=src, forum_reply=True)
        after = pilot2.readback(key)
        same = lambda x: {k: x[k] for k in ("office_tid", "office_status", "evidence", "history")}  # noqa: E731
        report["checks"].append({"phase": "restart", "name": "Dữ liệu Diễn Đàn còn nguyên sau khởi động lại",
                                 "pass": posts_before == posts_after,
                                 "detail": {"posts": len(posts_after), "comments": sum(len(p["comments"]) for p in posts_after)}})
        report["checks"].append({"phase": "restart", "name": "Nhiệm vụ + Evidence trong Văn Phòng còn nguyên",
                                 "pass": same(before) == same(after), "detail": same(after)})
        report["checks"] += [{"phase": 2, **c} for c in browser(2, args, out)]
        (out / "results").mkdir(exist_ok=True)
        for f in (state / "results").glob("*.json"):
            shutil.copy(f, out / "results" / f.name)
        (out / "readback.json").write_text(json.dumps(after, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
        (out / "run-log.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in pilot2.store.logs()),
                                           encoding="utf-8")
        (out / "forum-after-restart.json").write_text(json.dumps(posts_after, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    finally:
        try:
            backend.stop()
        except Exception:  # noqa: BLE001
            pass
        ssrv.shutdown()
    report["passed"] = sum(1 for c in report["checks"] if c["pass"])
    report["failed"] = sum(1 for c in report["checks"] if not c["pass"])
    (out / "checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    for c in report["checks"]:
        print(("PASS " if c["pass"] else "FAIL ") + str(c["phase"]) + " • " + c["name"])
    print(f"passed={report['passed']} failed={report['failed']}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
