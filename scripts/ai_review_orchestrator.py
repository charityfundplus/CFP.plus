#!/usr/bin/env python3
"""CFP+ multi-AI review orchestrator.

Reads a GitHub Issue, calls every configured provider whose API key exists,
normalizes the responses, and posts one consolidated evidence-first comment.
No provider may assign or modify Canonical IDs.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ReviewResult:
    reviewer: str
    status: str
    text: str


def request_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None,
                 payload: dict[str, Any] | None = None, timeout: int = 120) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    if payload is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Connection error for {url}: {exc}") from exc


def github_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {required_env('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "CFP-plus-AI-review-orchestrator",
    }


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_prompt(issue: dict[str, Any]) -> str:
    return f"""You are an independent reviewer for CFP+.

Review the GitHub Issue below using Evidence First. Check factual claims, official/public sources, broken or outdated links, internal consistency, and implementation risks.

MANDATORY RULES:
1. Do not assign, invent, renumber, or modify any Canonical ID.
2. Do not claim that a source was verified unless you actually accessed it.
3. Classify each material finding as exactly one of: VERIFIED, EVIDENCE_REQUIRED, BROKEN, OUTDATED.
4. Separate evidence from inference.
5. End with one overall result: PASS, PASS WITH CHANGES, BLOCKED, or FAIL.
6. Keep the response suitable for posting directly to GitHub Markdown.

Required structure:
- Reviewer
- Scope reviewed
- Findings table: Finding | Classification | Evidence | Recommended action
- Access limitations
- Overall result

ISSUE #{issue.get('number')}: {issue.get('title', '')}

{issue.get('body') or '(No issue body provided.)'}
"""


def call_openai(prompt: str) -> str:
    data = request_json(
        "https://api.openai.com/v1/responses",
        method="POST",
        headers={"Authorization": f"Bearer {required_env('OPENAI_API_KEY')}"},
        payload={
            "model": os.getenv("OPENAI_MODEL", "gpt-5-mini"),
            "input": prompt,
            "max_output_tokens": 3500,
        },
    )
    if data.get("output_text"):
        return data["output_text"]
    parts: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
    return "\n".join(parts).strip() or "No textual response returned."


def call_anthropic(prompt: str) -> str:
    data = request_json(
        "https://api.anthropic.com/v1/messages",
        method="POST",
        headers={
            "x-api-key": required_env("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
        },
        payload={
            "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
            "max_tokens": 3500,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    return "\n".join(x.get("text", "") for x in data.get("content", []) if x.get("type") == "text").strip()


def call_gemini(prompt: str) -> str:
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    key = required_env("GEMINI_API_KEY")
    data = request_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        method="POST",
        payload={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 3500},
        },
    )
    candidates = data.get("candidates", [])
    if not candidates:
        return "No candidate response returned."
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(p.get("text", "") for p in parts).strip()


def call_xai(prompt: str) -> str:
    data = request_json(
        "https://api.x.ai/v1/chat/completions",
        method="POST",
        headers={"Authorization": f"Bearer {required_env('XAI_API_KEY')}"},
        payload={
            "model": os.getenv("XAI_MODEL", "grok-4-fast"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 3500,
            "temperature": 0.1,
        },
    )
    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


def run_reviewer(name: str, key_env: str, caller: Callable[[str], str], prompt: str) -> ReviewResult:
    if not os.getenv(key_env, "").strip():
        return ReviewResult(name, "SKIPPED", f"Secret `{key_env}` is not configured.")
    try:
        text = caller(prompt)
        return ReviewResult(name, "COMPLETED", text or "Provider returned an empty response.")
    except Exception as exc:  # continue other independent reviewers
        return ReviewResult(name, "ERROR", str(exc))


def post_comment(repo: str, issue_number: int, body: str) -> None:
    request_json(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments",
        method="POST",
        headers=github_headers(),
        payload={"body": body},
    )


def main() -> int:
    repo = required_env("GITHUB_REPOSITORY")
    issue_number = int(required_env("ISSUE_NUMBER"))
    issue = request_json(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        headers=github_headers(),
    )
    prompt = build_prompt(issue)

    reviewers = [
        ("OpenAI", "OPENAI_API_KEY", call_openai),
        ("Anthropic", "ANTHROPIC_API_KEY", call_anthropic),
        ("Gemini", "GEMINI_API_KEY", call_gemini),
        ("xAI", "XAI_API_KEY", call_xai),
    ]
    results = [run_reviewer(name, env, caller, prompt) for name, env, caller in reviewers]

    completed = sum(result.status == "COMPLETED" for result in results)
    sections = [
        "## CFP+ Automated Independent Review",
        "",
        f"**Issue:** #{issue_number}",
        f"**Completed reviewers:** {completed}/{len(results)}",
        "**Governance guard:** No AI response may assign or modify Canonical IDs. Human Governance retains final authority.",
    ]
    for result in results:
        sections.extend([
            "",
            "---",
            "",
            f"### {result.reviewer} — {result.status}",
            "",
            result.text[:60000],
        ])
    sections.extend([
        "",
        "---",
        "",
        "### Human Governance checkpoint",
        "This automated report is evidence input only. Merge, Canonical Lock, ID assignment, and final decisions require explicit Human Governance approval.",
        "",
        f"_Generated by CFP+ AI Review Orchestrator at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}._",
    ])
    post_comment(repo, issue_number, "\n".join(sections))

    if completed == 0:
        print("No provider completed. Configure at least one API secret.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
