#!/usr/bin/env python3
"""Read a Notion page, review it with OpenAI, and append the report to Notion.

Required environment variables:
  OPENAI_API_KEY
  NOTION_TOKEN

Optional environment variables:
  OPENAI_MODEL (default: gpt-5-mini)
  NOTION_VERSION (default: 2026-03-11)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

OPENAI_URL = "https://api.openai.com/v1/responses"
NOTION_BASE_URL = "https://api.notion.com/v1"
MAX_SOURCE_CHARS = 120_000
MAX_NOTION_TEXT = 1900


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def http_json(
    method: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc}") from exc


def notion_headers(token: str, notion_version: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": notion_version,
        "Content-Type": "application/json",
    }


def rich_text_to_plain(items: list[dict[str, Any]]) -> str:
    return "".join(str(item.get("plain_text", "")) for item in items)


def block_to_text(block: dict[str, Any]) -> str:
    block_type = block.get("type", "")
    data = block.get(block_type, {}) if block_type else {}
    rich_text = data.get("rich_text") or data.get("caption") or []
    text = rich_text_to_plain(rich_text) if isinstance(rich_text, list) else ""

    prefixes = {
        "heading_1": "# ",
        "heading_2": "## ",
        "heading_3": "### ",
        "heading_4": "#### ",
        "bulleted_list_item": "- ",
        "numbered_list_item": "1. ",
        "to_do": "- [ ] ",
        "quote": "> ",
        "code": "```\n",
    }
    if block_type == "divider":
        return "---"
    if block_type == "child_page":
        return f"[Child page] {data.get('title', '')}"
    if block_type == "child_database":
        return f"[Child database] {data.get('title', '')}"
    if block_type == "code":
        return f"```\n{text}\n```"
    return f"{prefixes.get(block_type, '')}{text}".strip()


def get_block_children(
    block_id: str,
    token: str,
    notion_version: str,
    depth: int = 0,
    max_depth: int = 4,
) -> list[str]:
    if depth > max_depth:
        return []

    headers = notion_headers(token, notion_version)
    cursor: str | None = None
    output: list[str] = []

    while True:
        query = {"page_size": "100"}
        if cursor:
            query["start_cursor"] = cursor
        url = f"{NOTION_BASE_URL}/blocks/{block_id}/children?{urllib.parse.urlencode(query)}"
        response = http_json("GET", url, headers)

        for block in response.get("results", []):
            text = block_to_text(block)
            if text:
                output.append(("  " * depth) + text)
            if block.get("has_children"):
                output.extend(
                    get_block_children(
                        block["id"], token, notion_version, depth + 1, max_depth
                    )
                )

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
        if not cursor:
            break

    return output


def review_with_openai(source: str, api_key: str, model: str) -> str:
    instructions = (
        "You are an independent technical and governance reviewer for CFP+. "
        "Use Evidence First. Do not invent missing facts. Review the supplied Notion page. "
        "Return Vietnamese Markdown with: Overall conclusion (PASS, PASS WITH CHANGES, or FAIL); "
        "findings with ID, related Canonical ID, type, severity, current content, problem, required change; "
        "evidence gaps; and prioritized next actions. Preserve the rule that HUB is reserved exclusively "
        "for HUB 69. Distinguish Review Candidate from Canonical Locked."
    )
    payload = {
        "model": model,
        "instructions": instructions,
        "input": source[:MAX_SOURCE_CHARS],
    }
    response = http_json(
        "POST",
        OPENAI_URL,
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload,
    )

    if isinstance(response.get("output_text"), str):
        return response["output_text"].strip()

    chunks: list[str] = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                chunks.append(content["text"])
    result = "\n".join(chunks).strip()
    if not result:
        raise RuntimeError("OpenAI response did not contain output text")
    return result


def split_text(text: str, limit: int = MAX_NOTION_TEXT) -> list[str]:
    paragraphs = text.split("\n")
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n{paragraph}"
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
        while len(paragraph) > limit:
            chunks.append(paragraph[:limit])
            paragraph = paragraph[limit:]
        current = paragraph
    if current:
        chunks.append(current)
    return chunks


def append_report(
    page_id: str,
    report: str,
    token: str,
    notion_version: str,
    model: str,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    children: list[dict[str, Any]] = [
        {"object": "block", "type": "divider", "divider": {}},
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"OpenAI Independent Review — {timestamp}"},
                    }
                ]
            },
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"Model: {model} • Generated through CFP+ GitHub Actions"},
                        "annotations": {"italic": True},
                    }
                ]
            },
        },
    ]

    for chunk in split_text(report):
        children.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                },
            }
        )

    headers = notion_headers(token, notion_version)
    for index in range(0, len(children), 100):
        http_json(
            "PATCH",
            f"{NOTION_BASE_URL}/blocks/{page_id}/children",
            headers,
            {"children": children[index : index + 100]},
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-id", required=True, help="Notion page UUID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate the review but do not append it to Notion",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    openai_key = require_env("OPENAI_API_KEY")
    notion_token = require_env("NOTION_TOKEN")
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini"
    notion_version = os.getenv("NOTION_VERSION", "2026-03-11").strip()

    source_lines = get_block_children(args.page_id, notion_token, notion_version)
    source = "\n".join(source_lines).strip()
    if not source:
        raise RuntimeError(
            "No readable page content found. Confirm the page is shared with the Notion integration."
        )

    report = review_with_openai(source, openai_key, model)
    print(report)
    if not args.dry_run:
        append_report(args.page_id, report, notion_token, notion_version, model)
        print("\nReview appended to Notion.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
