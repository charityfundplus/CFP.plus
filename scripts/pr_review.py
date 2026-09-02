#!/usr/bin/env python3
"""Claude-powered pull request reviewer for CFP+.

Reads the pull request diff through the GitHub API, filters review-relevant files,
submits bounded chunks to Anthropic, aggregates a governance-aware review, and
posts one PR comment. The script never mutates files, approves governance, or
merges a pull request.
"""
from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Any, Iterable

GITHUB_API = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
ANTHROPIC_API = os.getenv("ANTHROPIC_API_URL", "https://api.anthropic.com/v1/messages")
ANTHROPIC_VERSION = "2023-06-01"
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
REQUEST_TIMEOUT = int(os.getenv("PR_REVIEW_TIMEOUT_SECONDS", "60"))
MAX_RETRIES = int(os.getenv("PR_REVIEW_MAX_RETRIES", "4"))
MAX_CHARS_PER_CHUNK = int(os.getenv("PR_REVIEW_CHUNK_CHARS", "45000"))
MAX_TOTAL_CHARS = int(os.getenv("PR_REVIEW_MAX_TOTAL_CHARS", "220000"))
COMMENT_MARKER = "<!-- cfp-plus-claude-pr-review -->"

RELEVANT_PATTERNS = (
    "registry/**/*.md", "registry/*.md", "governance/**/*.md", "governance/*.md",
    "**/*governance*.md", "**/*.json", "**/*.yaml", "**/*.yml",
    "scripts/**/*.py", "scripts/*.py", "tools/validator/**/*", ".github/workflows/*",
)
STATUS_ORDER = {"PASS": 0, "PASS WITH CHANGES": 1, "FAIL": 2}


@dataclass(frozen=True)
class ReviewContext:
    repository: str
    pr_number: int
    title: str
    body: str
    base_sha: str
    head_sha: str
    author: str


class ReviewError(RuntimeError):
    pass


def _safe_log(message: str) -> None:
    print(message, flush=True)


def _request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None,
             body: bytes | None = None, timeout: int = REQUEST_TIMEOUT) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(url, data=body, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    for attempt in range(MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read(), dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            retryable = exc.code in {408, 425, 429, 500, 502, 503, 504}
            if not retryable or attempt >= MAX_RETRIES:
                detail = exc.read(1200).decode("utf-8", "replace")
                raise ReviewError(f"HTTP {exc.code} from {url}: {detail}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else min(2**attempt, 20)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt >= MAX_RETRIES:
                raise ReviewError(f"Network timeout/error calling {url}: {exc}") from exc
            delay = min(2**attempt, 20)
        delay += random.random()
        _safe_log(f"Transient API error; retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES}).")
        time.sleep(delay)
    raise ReviewError("Unreachable retry state")


def github_json(path: str, token: str, *, method: str = "GET", payload: Any | None = None) -> Any:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    raw, _ = _request(f"{GITHUB_API}{path}", method=method, body=body, headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "cfp-plus-pr-reviewer",
        **({"Content-Type": "application/json"} if body else {}),
    })
    return json.loads(raw.decode("utf-8")) if raw else None


def get_pr_context(repository: str, pr_number: int, token: str) -> ReviewContext:
    data = github_json(f"/repos/{repository}/pulls/{pr_number}", token)
    return ReviewContext(repository, pr_number, data.get("title") or "", data.get("body") or "",
                         data["base"]["sha"], data["head"]["sha"],
                         (data.get("user") or {}).get("login") or "unknown")


def get_full_pr_diff(repository: str, pr_number: int, token: str) -> str:
    raw, _ = _request(f"{GITHUB_API}/repos/{repository}/pulls/{pr_number}", headers={
        "Accept": "application/vnd.github.v3.diff", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "cfp-plus-pr-reviewer",
    }, timeout=max(REQUEST_TIMEOUT, 120))
    return raw.decode("utf-8", "replace")


def split_diff_by_file(diff_text: str) -> list[tuple[str, str]]:
    sections, current, filename = [], [], None
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if filename is not None:
                sections.append((filename, "".join(current)))
            current = [line]
            match = re.match(r"diff --git a/(.+?) b/(.+)$", line.rstrip("\n"))
            filename = match.group(2) if match else "unknown"
        elif filename is not None:
            current.append(line)
    if filename is not None:
        sections.append((filename, "".join(current)))
    return sections


def is_relevant_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(fnmatch(normalized, pattern) for pattern in RELEVANT_PATTERNS)


def filter_relevant_diff(diff_text: str) -> tuple[str, list[str], list[str]]:
    relevant, included, excluded = [], [], []
    for filename, section in split_diff_by_file(diff_text):
        if is_relevant_file(filename):
            included.append(filename); relevant.append(section)
        else:
            excluded.append(filename)
    return "".join(relevant), included, excluded


def chunk_diff(diff_text: str, max_chars: int = MAX_CHARS_PER_CHUNK) -> tuple[list[str], bool]:
    truncated = len(diff_text) > MAX_TOTAL_CHARS
    bounded = diff_text[:MAX_TOTAL_CHARS]
    chunks, current = [], ""
    for _, section in split_diff_by_file(bounded):
        if len(section) > max_chars:
            if current: chunks.append(current); current = ""
            chunks.extend(section[start:start + max_chars] for start in range(0, len(section), max_chars))
        elif current and len(current) + len(section) > max_chars:
            chunks.append(current); current = section
        else:
            current += section
    if current: chunks.append(current)
    return chunks or ([bounded] if bounded else []), truncated


def anthropic_message(api_key: str, prompt: str, *, max_tokens: int = 3500) -> str:
    payload = {"model": MODEL, "max_tokens": max_tokens, "temperature": 0,
               "system": "You are Claude acting as an independent technical and governance reviewer for CFP+. Use only supplied PR evidence. Human Governance retains final authority. Never recommend auto-merge or autonomous governance approval.",
               "messages": [{"role": "user", "content": prompt}]}
    raw, _ = _request(ANTHROPIC_API, method="POST", body=json.dumps(payload).encode("utf-8"), headers={
        "x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json", "user-agent": "cfp-plus-pr-reviewer",
    }, timeout=max(REQUEST_TIMEOUT, 120))
    data = json.loads(raw.decode("utf-8"))
    text = "\n".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
    if not text.strip(): raise ReviewError("Anthropic returned no review text")
    return text.strip()


def chunk_prompt(context: ReviewContext, chunk: str, index: int, total: int, truncated: bool) -> str:
    return f"""Review chunk {index}/{total} of PR #{context.pr_number} in {context.repository}.
PR title: {context.title}
PR author: {context.author}
Diff truncated by safety limit: {str(truncated).lower()}
Return evidence-grounded observations only. For every issue include Finding, Severity, Evidence, Governance Impact, Recommendation, and Closure Criteria. Do not issue final status yet.
```diff
{chunk}
```"""


def synthesis_prompt(context: ReviewContext, partials: Iterable[str], included: list[str], excluded: list[str], truncated: bool) -> str:
    joined = "\n\n--- PARTIAL REVIEW ---\n\n".join(partials)
    return f"""Synthesize final independent review for PR #{context.pr_number} in {context.repository}.
PR title: {context.title}
Reviewed files: {', '.join(included) if included else 'none'}
Excluded as unrelated: {', '.join(excluded) if excluded else 'none'}
Diff truncated by safety limit: {str(truncated).lower()}
Allowed statuses: PASS, PASS WITH CHANGES, FAIL.
Use exactly:
## Status
**PASS|PASS WITH CHANGES|FAIL**
## Summary
...
## Findings
### Finding N — title
- **Severity:** ...
- **Evidence:** ...
- **Governance Impact:** ...
- **Recommendation:** ...
- **Closure Criteria:** ...
If none, write No material findings. End with: Human Governance retains final decision authority. Do not claim excluded or truncated evidence was reviewed.
Partial reviews:
{joined}"""


def normalize_status(review: str) -> str:
    match = re.search(r"\b(PASS WITH CHANGES|FAIL|PASS)\b", review, flags=re.IGNORECASE)
    return match.group(1).upper() if match and match.group(1).upper() in STATUS_ORDER else "FAIL"


def build_no_relevant_comment(included: list[str], excluded: list[str]) -> str:
    return f"""{COMMENT_MARKER}
## Status
**PASS**
## Summary
No review-relevant files were changed.
## Findings
No material findings.
- **Severity:** INFO
- **Evidence:** Reviewed: {', '.join(included) if included else 'none'}; excluded: {', '.join(excluded) if excluded else 'none'}
- **Governance Impact:** None identified.
- **Recommendation:** Human Governance may continue normal review.
- **Closure Criteria:** Human Governance confirms file-scope classification.
Human Governance retains final decision authority."""


def post_or_update_comment(repository: str, pr_number: int, token: str, body: str) -> None:
    comments = github_json(f"/repos/{repository}/issues/{pr_number}/comments?per_page=100", token)
    for comment in comments:
        if COMMENT_MARKER in (comment.get("body") or ""):
            github_json(f"/repos/{repository}/issues/comments/{comment['id']}", token, method="PATCH", payload={"body": body}); return
    github_json(f"/repos/{repository}/issues/{pr_number}/comments", token, method="POST", payload={"body": body})


def load_event() -> tuple[str, int]:
    repository, event_path = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_EVENT_PATH", "")
    if not repository or not event_path: raise ReviewError("GITHUB_REPOSITORY and GITHUB_EVENT_PATH are required")
    with open(event_path, "r", encoding="utf-8") as handle: event = json.load(handle)
    number = event.get("pull_request", {}).get("number") or event.get("number")
    if not isinstance(number, int): raise ReviewError("Could not determine pull request number")
    return repository, number


def main() -> int:
    github_token, anthropic_key = os.environ.get("GITHUB_TOKEN"), os.environ.get("ANTHROPIC_API_KEY")
    if not github_token: raise ReviewError("GITHUB_TOKEN is required")
    if not anthropic_key: raise ReviewError("ANTHROPIC_API_KEY is required")
    repository, pr_number = load_event()
    context = get_pr_context(repository, pr_number, github_token)
    _safe_log(f"Reviewing PR #{pr_number} in {repository}.")
    full_diff = get_full_pr_diff(repository, pr_number, github_token)
    relevant_diff, included, excluded = filter_relevant_diff(full_diff)
    _safe_log(f"Relevant files: {len(included)}; excluded files: {len(excluded)}.")
    if not relevant_diff.strip():
        post_or_update_comment(repository, pr_number, github_token, build_no_relevant_comment(included, excluded)); return 0
    chunks, truncated = chunk_diff(relevant_diff)
    partials = [anthropic_message(anthropic_key, chunk_prompt(context, chunk, i, len(chunks), truncated)) for i, chunk in enumerate(chunks, 1)]
    final_review = anthropic_message(anthropic_key, synthesis_prompt(context, partials, included, excluded, truncated), max_tokens=5000)
    status = normalize_status(final_review)
    body = f"{COMMENT_MARKER}\n{final_review}\n\n---\nAutomated Claude review status: **{status}**. This comment does not merge, modify files, or approve governance."
    post_or_update_comment(repository, pr_number, github_token, body)
    _safe_log(f"Posted PR review comment with status: {status}.")
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except ReviewError as exc:
        _safe_log(f"PR review failed: {exc}"); raise SystemExit(1)
