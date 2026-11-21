"""Public CFP+ work tracking for the HUB 69 sandbox."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
import re
from threading import Lock
from time import monotonic
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPO = "charityfundplus/CFP.plus"
SOURCES = (
    ("Codex", "issues", 178),
    ("Codex", "pulls", 179),
    ("ChatGPT", "issues", 238),
    ("ChatGPT", "pulls", 124),
    ("ReviewSI", "issues", 180),
    ("SecuritySI", "pulls", 214),
    ("SecuritySI", "pulls", 216),
    ("Siêu Bộ Đôi", "issues", 200),
    ("Siêu Bộ Đôi", "pulls", 195),
    ("Link Mẫu", "issues", 239),
)
REFRESH_SECONDS = 900


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_github(kind, number):
    request = Request(
        f"https://api.github.com/repos/{REPO}/{kind}/{number}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "CFP-HUB69-Sandbox"},
    )
    with build_opener(NoRedirect()).open(request, timeout=5) as response:
        return json.loads(response.read(1024 * 1024))


def normalize(data, lane, kind, number):
    url = f"https://github.com/{REPO}/{kind if kind == 'issues' else 'pull'}/{number}"
    if data["html_url"] != url or data["number"] != number:
        raise ValueError("Unexpected GitHub source")
    state = data["state"]
    if state not in ("open", "closed"):
        raise ValueError("Unexpected GitHub state")
    updated = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    if updated.tzinfo is None:
        raise ValueError("Timestamp missing timezone")
    labels = {label["name"].casefold() for label in data.get("labels", [])}
    status = "GitHub " + state.upper()
    blocker = "Chưa ghi nhận blocker có cấu trúc."
    if "blocked" in labels:
        status = "BLOCKED"
        blocker = "GitHub gắn nhãn blocked. Xem nguồn để biết chi tiết."
    elif data.get("draft"):
        status = "GitHub DRAFT"
        blocker = "Đang ở Draft PR. Xem nguồn để biết điều kiện review."
    elif data.get("merged"):
        status = "GitHub MERGED"
    sha = (data.get("head") or {}).get("sha", "")
    evidence = url + "/commits/" + sha if kind == "pulls" and re.fullmatch(r"[0-9a-f]{40}", sha) else None
    return {
        "lane": lane, "title": data["title"], "owner": ", ".join(a["login"] for a in data.get("assignees", [])),
        "status": status, "blocker": blocker, "updated_at": updated.astimezone(timezone.utc).isoformat(),
        "evidence_urls": [evidence] if evidence else [], "url": url,
    }


class GitHubResults:
    def __init__(self, read=read_github):
        self.read = read
        self.rows = {}
        self.errors = []
        self.next_refresh = 0
        self.checked_at = None
        self.lock = Lock()

    def _fetch(self, source):
        lane, kind, number = source
        try:
            return normalize(self.read(kind, number), lane, kind, number)
        except (URLError, OSError, ValueError, KeyError, TypeError, AttributeError):
            return None

    def snapshot(self):
        if os.getenv("CFP_HUB69_GITHUB_PUBLIC_SYNC") != "1":
            return {"state": "disabled", "checked_at": None, "rows": [], "errors": []}
        with self.lock:
            if monotonic() >= self.next_refresh:
                self.errors = []
                with ThreadPoolExecutor(max_workers=4) as pool:
                    for source, result in zip(SOURCES, pool.map(self._fetch, SOURCES)):
                        if result is None:
                            _, kind, number = source
                            self.errors.append(f"{kind}/{number}")
                        else:
                            self.rows[source] = result
                self.checked_at = datetime.now(timezone.utc).isoformat()
                self.next_refresh = monotonic() + REFRESH_SECONDS
            return {
                "state": "partial" if self.errors else "current", "checked_at": self.checked_at,
                "rows": [dict(row, stale=f"{source[1]}/{source[2]}" in self.errors)
                         for source, row in self.rows.items()],
                "errors": list(self.errors),
            }
