#!/usr/bin/env python3
"""CMP Orchestrator P0.

Reads assigned work items from a Notion data source, asks OpenAI to process
one item at a time, and writes the result and execution evidence back to the
same Notion page.

Required secrets:
  NOTION_TOKEN
  OPENAI_API_KEY
  NOTION_WORK_QUEUE_ID

Optional configuration is documented in docs/CMP_ORCHESTRATOR_SETUP.md.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

NOTION_VERSION = os.getenv("NOTION_VERSION", "2026-03-11")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")
MAX_ITEMS = int(os.getenv("CMP_MAX_ITEMS", "3"))
DRY_RUN = os.getenv("CMP_DRY_RUN", "false").lower() == "true"

TITLE_PROPERTY = os.getenv("CMP_TITLE_PROPERTY", "Name")
STATUS_PROPERTY = os.getenv("CMP_STATUS_PROPERTY", "Status")
PROMPT_PROPERTY = os.getenv("CMP_PROMPT_PROPERTY", "Prompt")
RESULT_PROPERTY = os.getenv("CMP_RESULT_PROPERTY", "Result")
EVIDENCE_PROPERTY = os.getenv("CMP_EVIDENCE_PROPERTY", "Evidence")
ASSIGNED_STATUS = os.getenv("CMP_ASSIGNED_STATUS", "Assigned")
IN_PROGRESS_STATUS = os.getenv("CMP_IN_PROGRESS_STATUS", "In Progress")
DONE_STATUS = os.getenv("CMP_DONE_STATUS", "Waiting for Review")
ERROR_STATUS = os.getenv("CMP_ERROR_STATUS", "Blocked")


@dataclass(frozen=True)
class Settings:
    notion_token: str
    openai_api_key: str
    work_queue_id: str

    @classmethod
    def from_env(cls) -> "Settings":
        values = {
            "NOTION_TOKEN": os.getenv("NOTION_TOKEN", "").strip(),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "").strip(),
            "NOTION_WORK_QUEUE_ID": os.getenv("NOTION_WORK_QUEUE_ID", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise RuntimeError("Missing required secrets/variables: " + ", ".join(missing))
        return cls(
            notion_token=values["NOTION_TOKEN"],
            openai_api_key=values["OPENAI_API_KEY"],
            work_queue_id=values["NOTION_WORK_QUEUE_ID"],
        )


def http_json(method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error calling {url}: {exc}") from exc


def notion_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def query_work_items(settings: Settings) -> list[dict[str, Any]]:
    url = f"https://api.notion.com/v1/data_sources/{settings.work_queue_id}/query"
    payload = {
        "filter": {
            "property": STATUS_PROPERTY,
            "status": {"equals": ASSIGNED_STATUS},
        },
        "page_size": min(MAX_ITEMS, 100),
        "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
    }
    data = http_json("POST", url, notion_headers(settings.notion_token), payload)
    return data.get("results", [])[:MAX_ITEMS]


def rich_text_value(prop: dict[str, Any]) -> str:
    values = prop.get("rich_text") or prop.get("title") or []
    return "".join(item.get("plain_text", "") for item in values).strip()


def get_title(page: dict[str, Any]) -> str:
    return rich_text_value(page.get("properties", {}).get(TITLE_PROPERTY, {})) or "Untitled work item"


def get_prompt(page: dict[str, Any]) -> str:
    prompt = rich_text_value(page.get("properties", {}).get(PROMPT_PROPERTY, {}))
    if not prompt:
        raise RuntimeError(f"Work item '{get_title(page)}' has no prompt in property '{PROMPT_PROPERTY}'")
    return prompt


def update_page(settings: Settings, page_id: str, properties: dict[str, Any]) -> None:
    if DRY_RUN:
        print(f"DRY RUN update {page_id}: {json.dumps(properties, ensure_ascii=False)}")
        return
    url = f"https://api.notion.com/v1/pages/{page_id}"
    http_json("PATCH", url, notion_headers(settings.notion_token), {"properties": properties})


def status_property(value: str) -> dict[str, Any]:
    return {"status": {"name": value}}


def rich_text_property(value: str) -> dict[str, Any]:
    # Notion rich text items are limited; keep the operational summary compact.
    compact = value[:1900]
    return {"rich_text": [{"type": "text", "text": {"content": compact}}]}


def call_openai(settings: Settings, title: str, prompt: str) -> tuple[str, str]:
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    system_instruction = (
        "You are the CMP execution agent for CFP+. Follow Evidence First, Reference First, "
        "Canonical First, and Human Governance. Do not claim publication, approval, locking, "
        "or completion without evidence. Return a concise operational result in Vietnamese. "
        "Clearly separate: Result, Evidence, Risks, and Human Decision Required."
    )
    payload = {
        "model": OPENAI_MODEL,
        "input": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Work item: {title}\n\n{prompt}"},
        ],
    }
    data = http_json("POST", url, headers, payload)
    output_text = data.get("output_text")
    if not output_text:
        chunks: list[str] = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                text = content.get("text")
                if text:
                    chunks.append(text)
        output_text = "\n".join(chunks).strip()
    if not output_text:
        raise RuntimeError("OpenAI returned no text output")
    return output_text, str(data.get("id", "unknown"))


def process_item(settings: Settings, page: dict[str, Any]) -> None:
    page_id = page["id"]
    title = get_title(page)
    prompt = get_prompt(page)
    print(f"Processing: {title} ({page_id})")

    update_page(settings, page_id, {STATUS_PROPERTY: status_property(IN_PROGRESS_STATUS)})
    result, response_id = call_openai(settings, title, prompt)
    timestamp = datetime.now(timezone.utc).isoformat()
    evidence = f"OpenAI response_id={response_id}; model={OPENAI_MODEL}; executed_at={timestamp}; source=GitHub Actions"
    update_page(
        settings,
        page_id,
        {
            RESULT_PROPERTY: rich_text_property(result),
            EVIDENCE_PROPERTY: rich_text_property(evidence),
            STATUS_PROPERTY: status_property(DONE_STATUS),
        },
    )
    print(f"Completed: {title}; response_id={response_id}")


def mark_blocked(settings: Settings, page: dict[str, Any], error: Exception) -> None:
    page_id = page.get("id")
    if not page_id:
        return
    message = f"CMP Orchestrator error: {error}"[:1900]
    try:
        update_page(
            settings,
            page_id,
            {
                EVIDENCE_PROPERTY: rich_text_property(message),
                STATUS_PROPERTY: status_property(ERROR_STATUS),
            },
        )
    except Exception as update_error:  # noqa: BLE001
        print(f"Could not mark item blocked: {update_error}", file=sys.stderr)


def main() -> int:
    try:
        settings = Settings.from_env()
        items = query_work_items(settings)
        if not items:
            print(f"No work items with status '{ASSIGNED_STATUS}'.")
            return 0
        failures = 0
        for page in items:
            try:
                process_item(settings, page)
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAILED: {exc}", file=sys.stderr)
                mark_blocked(settings, page, exc)
                time.sleep(1)
        return 1 if failures else 0
    except Exception as exc:  # noqa: BLE001
        print(f"FATAL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
