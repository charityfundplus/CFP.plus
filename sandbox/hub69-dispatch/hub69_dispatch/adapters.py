"""Channel adapters. Each one reports its REAL connection status; none assumes another SI AI is connected.

Sources normalise comments to: {ref, body, author_login, created_at, url}.

  • github:<owner>/<repo>#<issue>   read via REST with GITHUB_TOKEN (read works for public issues without one);
                                      post only through post_comment(), which the CLI gates behind HOLD.
  • file:<path.json>                 Working Link / fixture export (list of the same dicts).
  • Notion, CMP 267                  sinks: build the exact payload they would receive and say NOT_CONNECTED
                                      unless credentials/base URL are configured. They never send in this sandbox.
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

API = "https://api.github.com"


def _gh_request(url: str, token: str | None, method: str = "GET", data: dict | None = None):
    req = urllib.request.Request(url, method=method, data=json.dumps(data).encode() if data else None)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "hub69-dispatch-sandbox")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (fixed https host)
        return json.load(r), r.headers.get("Link", "")


class GitHubIssueSource:
    channel = "github"

    def __init__(self, spec: str):
        repo, issue = spec.split("#")
        self.repo, self.issue = repo, int(issue)
        self.token = os.environ.get("GITHUB_TOKEN")

    def status(self) -> dict:
        return {"channel": "github", "target": f"{self.repo}#{self.issue}",
                "read": "CONFIGURED", "write": "TOKEN PRESENT" if self.token else "NO TOKEN"}

    def fetch(self) -> list[dict]:
        out, url = [], f"{API}/repos/{self.repo}/issues/{self.issue}/comments?per_page=100"
        while url:
            page, link = _gh_request(url, self.token)
            for c in page:
                out.append({"ref": f"{self.issue}#{c['id']}", "body": c.get("body") or "",
                            "author_login": (c.get("user") or {}).get("login", ""),
                            "created_at": c["created_at"], "url": c["html_url"]})
            url = next((p.split(";")[0].strip("<> ") for p in link.split(",") if 'rel="next"' in p), None)
        return out

    def post_comment(self, body: str) -> dict:
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN missing")
        res, _ = _gh_request(f"{API}/repos/{self.repo}/issues/{self.issue}/comments", self.token, "POST",
                             {"body": body})
        return {"id": res["id"], "url": res["html_url"]}


class FileSource:
    channel = "working_link"

    def __init__(self, path: str):
        self.path = Path(path)

    def status(self) -> dict:
        return {"channel": "working_link", "target": str(self.path), "read": "FILE", "write": "NONE"}

    def fetch(self) -> list[dict]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data["comments"] if isinstance(data, dict) else data

    def post_comment(self, body: str) -> dict:
        raise RuntimeError("file source is read-only")


class ForumSource:
    """Diễn Đàn Siêu Bộ Đôi trên backend PR #195 (cùng dữ liệu mà giao diện Canva đọc/ghi).
    spec: forum:<https base>#<forum key>. Đọc công khai (forum public_read); mỗi bài và bình luận là một thông điệp.
    Mã task = 'sbd#<post id>' (tham chiếu gốc, không cấp ID mới)."""
    channel = "forum_195"

    def __init__(self, spec: str):
        base, _, key = spec.rpartition("#")
        self.base, self.key = base.rstrip("/"), key or "sieu-bo-doi"
        self.prefix = "sbd" if self.key == "sieu-bo-doi" else self.key

    def status(self) -> dict:
        return {"channel": self.channel, "target": f"{self.base} • {self.key}", "read": "PUBLIC API", "write": "dispatcher account"}

    def fetch(self) -> list[dict]:
        req = urllib.request.Request(f"{self.base}/api/forums/{self.key}/posts", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (operator-configured sandbox base)
            posts = json.load(r)["posts"]
        out = []
        for p in posts:
            ref = f"{self.prefix}#{p['id']}"
            out.append({"ref": ref, "body": f"{p['title']}\n{p['body']}", "author_login": f"forum:{p['author']['id']}",
                        "author_name": p["author"]["name"], "created_at": p["created_at"], "post_id": p["id"],
                        "url": f"{self.base}/canva/#post-{p['id']}"})
            for c in p.get("comments", []):
                out.append({"ref": f"{ref}/c{c['id']}", "body": c["body"], "author_login": f"forum:{c['author']['id']}",
                            "author_name": c["author"]["name"], "created_at": c["created_at"], "post_id": p["id"],
                            "url": f"{self.base}/canva/#post-{p['id']}"})
        return out

    def post_comment(self, body: str) -> dict:
        raise RuntimeError("forum replies go through Autopilot.forum_reply (authenticated dispatcher account)")


def make_source(spec: str):
    kind, _, rest = spec.partition(":")
    if kind == "forum":
        return ForumSource(rest)
    if kind == "github":
        return GitHubIssueSource(rest)
    if kind == "file":
        return FileSource(rest)
    raise ValueError(f"unknown source {spec!r} (use github:owner/repo#N or file:path.json)")


class NotionSink:
    """CMP 267 Office on Notion. The only verified Notion write so far is ChatGPT's own session
    (#178 issuecomment-6836178883); this sandbox has no Notion credential, so it only prepares rows."""

    def status(self) -> dict:
        ok = bool(os.environ.get("NOTION_TOKEN") and os.environ.get("HUB69_NOTION_DATA_SOURCE"))
        return {"channel": "notion", "status": "CONFIGURED (not used in sandbox)" if ok else "NOT_CONNECTED",
                "reason": None if ok else "no NOTION_TOKEN / HUB69_NOTION_DATA_SOURCE in this runtime"}

    def payload(self, snapshot: dict) -> list[dict]:
        return [{"Task": t["key"], "Nhiệm vụ": t["title"], "Priority": t["priority"], "State": t["state"],
                 "Assignee": t["assignee"], "Reviewer": t["reviewer"], "Slot": t["slot"],
                 "Source": t["source_url"],
                 "Evidence": [u for e in t["evidence"] for u in e["urls"]],
                 "ACK provenance": (t["ack"] or {}).get("provenance")} for t in snapshot["tasks"]]


class CMP267Sink:
    """Maps queue state onto the PR #195 Office API (POST /api/office/tasks, /ack, /evidence, /review).
    That API enforces its own auth/RLS and 5-task limit; we only build the request plan here."""

    def status(self) -> dict:
        base = os.environ.get("HUB69_OFFICE_API")
        return {"channel": "cmp_267_office_api", "status": "CONFIGURED (not used in sandbox)" if base else "NOT_CONNECTED",
                "reason": None if base else "no HUB69_OFFICE_API + governance session; PR #195 sandbox auth (SMOKE_*) pending Human"}

    def payload(self, snapshot: dict) -> list[dict]:
        plan = []
        for t in snapshot["tasks"]:
            plan.append({"method": "POST", "path": "/api/office/tasks",
                         "json": {"title": t["title"], "assignee": t["assignee"], "reviewer": t["reviewer"],
                                  "external_ref": t["key"]}})
            for h in t["history"][1:]:
                p = {"ACK": "ack", "EVIDENCE": "evidence", "REVIEW": "review"}.get(h["kind"])
                if p:
                    plan.append({"method": "POST", "path": f"/api/office/tasks/{{tid:{t['key']}}}/{p}",
                                 "json": {"external_ref": h["ref"]}})
        return plan
