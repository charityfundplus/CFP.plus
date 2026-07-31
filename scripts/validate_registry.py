#!/usr/bin/env python3
"""Validate registry records and optionally request an OpenAI content review."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import requests

LOGGER = logging.getLogger("validate_registry")
REQUIRED_METADATA = ("Canonical ID", "Entity Name")
RECOMMENDED_METADATA = ("Visibility", "Lifecycle Status")
NUMERIC_STEM = re.compile(r"^\d+$")
METADATA_LINE = re.compile(r"^\*\*(.+?):\*\*\s*(.+?)\s*$")
LINK_PATTERN = re.compile(r"https://github\.com/charityfundplus/CFP\.plus/blob/main/registry/([^\s)]+)")
NUMERIC_ID_PATTERN = re.compile(r"(?<!\d)(\d{2,})(?!\d)")
DEFAULT_GITHUB_API_URL = "https://api.github.com"


@dataclass
class Finding:
    level: str
    code: str
    message: str
    path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {"level": self.level, "code": self.code, "message": self.message}
        if self.path:
            payload["path"] = self.path
        return payload


@dataclass
class RegistryRecord:
    path: Path
    relative_path: str
    format: str
    content: str
    metadata: dict[str, Any]
    canonical_id: str | None
    canonical_link: str | None
    record_type: str
    referenced_registry_ids: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    registry_path: str
    scanned_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    openai_review: dict[str, Any] = field(default_factory=dict)

    def add(self, level: str, code: str, message: str, path: str | None = None) -> None:
        self.findings.append(Finding(level=level, code=code, message=message, path=path))

    @property
    def error_count(self) -> int:
        return sum(1 for finding in self.findings if finding.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for finding in self.findings if finding.level == "warning")

    @property
    def info_count(self) -> int:
        return sum(1 for finding in self.findings if finding.level == "info")

    def status(self) -> str:
        if self.error_count:
            return "errors"
        if self.warning_count:
            return "warnings"
        return "pass"

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status(),
            "registry_path": self.registry_path,
            "scanned_files": self.scanned_files,
            "skipped_files": self.skipped_files,
            "summary": {
                "errors": self.error_count,
                "warnings": self.warning_count,
                "info": self.info_count,
                "total_findings": len(self.findings),
            },
            "findings": [finding.as_dict() for finding in self.findings],
            "openai_review": self.openai_review,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate registry records and generate reports.")
    parser.add_argument("--registry-path", default="registry", help="Path to the registry directory.")
    parser.add_argument("--changed-files-file", help="Optional file containing changed paths to review.")
    parser.add_argument("--json-report", default="validation_report.json", help="JSON report output path.")
    parser.add_argument("--markdown-report", default="validation_report.md", help="Markdown report output path.")
    parser.add_argument("--repo", help="owner/repo used when posting a PR comment.")
    parser.add_argument("--pr-number", type=int, help="Pull request number for optional commenting.")
    parser.add_argument("--post-pr-comment", action="store_true", help="Post the markdown report to the PR.")
    parser.add_argument("--github-api-url", default=DEFAULT_GITHUB_API_URL, help="GitHub API base URL.")
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"), help="OpenAI model name.")
    parser.add_argument(
        "--openai-max-files",
        type=int,
        default=int(os.getenv("OPENAI_MAX_FILES_REVIEW", "5")),
        help="Maximum number of files to send to OpenAI.",
    )
    parser.add_argument(
        "--openai-timeout",
        type=int,
        default=int(os.getenv("OPENAI_TIMEOUT", "30")),
        help="Timeout in seconds for the OpenAI request.",
    )
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Logging level.")
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(levelname)s: %(message)s")


def read_changed_files(path: str | None) -> list[str]:
    if not path:
        return []
    file_path = Path(path)
    if not file_path.exists():
        LOGGER.warning("Changed files list does not exist: %s", file_path)
        return []
    return [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def extract_first_numeric_id(text: str | None) -> str | None:
    if not text:
        return None
    match = NUMERIC_ID_PATTERN.search(text)
    return match.group(1) if match else None


def extract_canonical_link(content: str) -> str | None:
    lines = content.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower() == "## 1. canonical link":
            for candidate in lines[index + 1 :]:
                candidate = candidate.strip()
                if candidate:
                    return candidate
    return None


def parse_markdown_metadata(content: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in content.splitlines():
        match = METADATA_LINE.match(line.rstrip())
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        metadata[key] = value
    return metadata


def extract_registry_links(content: str) -> list[str]:
    return [Path(match).stem for match in LINK_PATTERN.findall(content) if NUMERIC_STEM.match(Path(match).stem)]


def sanitize_changed_files(changed_files: Iterable[str], registry_path: Path, report: ValidationReport) -> list[Path]:
    allowed_paths: list[Path] = []
    for changed_file in changed_files:
        candidate = Path(changed_file)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            resolved = (Path.cwd() / candidate).resolve()
        try:
            resolved.relative_to(registry_path)
        except ValueError:
            report.add("warning", "invalid_changed_path", f"Ignored path outside registry: {changed_file}")
            continue
        if resolved.suffix.lower() not in {".md", ".json"}:
            report.add("warning", "unsupported_changed_file", f"Ignored unsupported file type: {changed_file}")
            continue
        if not resolved.exists():
            report.add("warning", "missing_changed_file", f"Changed file no longer exists: {changed_file}")
            continue
        allowed_paths.append(resolved)
    return allowed_paths


def load_registry_files(registry_path: str, changed_files: list[str] | None = None, report: ValidationReport | None = None) -> list[RegistryRecord]:
    root = Path(registry_path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Registry path does not exist or is not a directory: {registry_path}")

    selected_paths: list[Path]
    if changed_files:
        if report is None:
            raise ValueError("A report instance is required when changed_files are provided.")
        selected_paths = sanitize_changed_files(changed_files, root, report)
    else:
        selected_paths = sorted(path for path in root.iterdir() if path.is_file() and path.suffix.lower() in {".md", ".json"})

    records: list[RegistryRecord] = []
    for path in sorted(selected_paths):
        try:
            relative_path = str(path.relative_to(Path.cwd()))
        except ValueError:
            relative_path = str(path.relative_to(root.parent))
        content = path.read_text(encoding="utf-8")
        stem = path.stem
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(content)
            except json.JSONDecodeError as exc:
                if report is not None:
                    report.add("error", "invalid_json", f"Invalid JSON: {exc}", relative_path)
                payload = {}
            canonical_id = str(payload.get("canonical_id") or payload.get("Canonical ID") or stem) if payload else None
            metadata = {str(key): value for key, value in payload.items()} if isinstance(payload, dict) else {}
            canonical_link = str(payload.get("canonical_link") or payload.get("Canonical Link") or "") or None if isinstance(payload, dict) else None
            record_type = "entry" if canonical_id and NUMERIC_STEM.match(canonical_id) else "supporting_document"
            referenced_registry_ids = extract_registry_links(content)
        else:
            metadata = parse_markdown_metadata(content)
            canonical_id = metadata.get("Canonical ID") or (stem if NUMERIC_STEM.match(stem) else None)
            canonical_link = extract_canonical_link(content)
            record_type = "entry" if NUMERIC_STEM.match(stem) else "supporting_document"
            referenced_registry_ids = extract_registry_links(content)

        records.append(
            RegistryRecord(
                path=path,
                relative_path=relative_path,
                format=path.suffix.lower().lstrip("."),
                content=content,
                metadata=metadata,
                canonical_id=canonical_id,
                canonical_link=canonical_link,
                record_type=record_type,
                referenced_registry_ids=referenced_registry_ids,
            )
        )
    return records


def validate_structure(records: list[RegistryRecord], report: ValidationReport) -> None:
    for record in records:
        report.scanned_files.append(record.relative_path)
        if record.record_type != "entry":
            report.skipped_files.append(record.relative_path)
            report.add("info", "skipped_supporting_document", "Skipped non-entry registry document.", record.relative_path)
            continue
        if record.format == "md" and not record.content.lstrip().startswith("# "):
            report.add("error", "missing_heading", "Markdown record must start with a level-1 heading.", record.relative_path)
        for required_key in REQUIRED_METADATA:
            if required_key not in record.metadata:
                report.add("error", "missing_required_metadata", f"Missing required metadata field: {required_key}", record.relative_path)
        if not record.canonical_link:
            report.add("error", "missing_canonical_link", "Missing canonical link section.", record.relative_path)


def validate_metadata(records: list[RegistryRecord], report: ValidationReport) -> None:
    seen_ids: dict[str, str] = {}
    for record in records:
        if record.record_type != "entry":
            continue
        if not record.canonical_id or not NUMERIC_STEM.match(str(record.canonical_id)):
            report.add("error", "invalid_canonical_id", "Canonical ID must be numeric.", record.relative_path)
            continue
        filename_id = record.path.stem
        if filename_id != record.canonical_id:
            report.add(
                "error",
                "canonical_id_filename_mismatch",
                f"Canonical ID {record.canonical_id} does not match filename {filename_id}.",
                record.relative_path,
            )
        previous_path = seen_ids.get(record.canonical_id)
        if previous_path:
            report.add(
                "error",
                "duplicate_canonical_id",
                f"Canonical ID {record.canonical_id} is duplicated in {previous_path} and {record.relative_path}.",
                record.relative_path,
            )
        seen_ids[record.canonical_id] = record.relative_path

        for recommended_key in RECOMMENDED_METADATA:
            if recommended_key not in record.metadata:
                report.add("warning", "missing_recommended_metadata", f"Missing recommended metadata field: {recommended_key}", record.relative_path)


def validate_canonical_links(records: list[RegistryRecord], report: ValidationReport) -> None:
    ids_to_paths = {record.canonical_id: record.relative_path for record in records if record.record_type == "entry" and record.canonical_id}
    registry_root = Path(report.registry_path).resolve()
    available_registry_ids = {
        path.stem
        for path in registry_root.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".json"} and NUMERIC_STEM.match(path.stem)
    }
    for record in records:
        if record.record_type != "entry" or not record.canonical_id:
            continue

        expected_link_suffix = f"registry/{record.path.name}"
        if record.canonical_link and expected_link_suffix not in record.canonical_link:
            report.add(
                "error",
                "canonical_link_mismatch",
                f"Canonical link should reference {expected_link_suffix}.",
                record.relative_path,
            )

        parent_fields = ["Parent ID", "Parent", "Parent Hub"]
        parent_id = None
        for field_name in parent_fields:
            parent_id = extract_first_numeric_id(str(record.metadata.get(field_name, "")))
            if parent_id:
                break

        if parent_id:
            if not record.canonical_id.startswith(parent_id):
                report.add(
                    "error",
                    "parent_child_mismatch",
                    f"Canonical ID {record.canonical_id} does not align with parent reference {parent_id}.",
                    record.relative_path,
                )
            elif field_name in {"Parent ID", "Parent"} and parent_id not in available_registry_ids:
                report.add(
                    "warning",
                    "missing_parent_record",
                    f"Referenced parent record {parent_id} is not present in registry.",
                    record.relative_path,
                )
        else:
            report.add("warning", "missing_parent_reference", "No parent relationship metadata found.", record.relative_path)

        for child_id in record.referenced_registry_ids:
            if child_id == record.canonical_id:
                continue
            if child_id not in available_registry_ids:
                report.add(
                    "warning",
                    "missing_linked_record",
                    f"Linked registry record {child_id} is not present in the repository.",
                    record.relative_path,
                )
            elif not child_id.startswith(record.canonical_id):
                report.add(
                    "warning",
                    "linked_record_outside_namespace",
                    f"Linked record {child_id} is outside the canonical namespace {record.canonical_id}.",
                    record.relative_path,
                )


def build_openai_payload(records: list[RegistryRecord], max_files: int) -> list[dict[str, Any]]:
    reviewed_records = []
    for record in records:
        if record.record_type != "entry":
            continue
        reviewed_records.append(
            {
                "path": record.relative_path,
                "canonical_id": record.canonical_id,
                "metadata": record.metadata,
                "canonical_link": record.canonical_link,
                "excerpt": record.content[:4000],
            }
        )
        if len(reviewed_records) >= max_files:
            break
    return reviewed_records


def extract_openai_text(response_json: dict[str, Any]) -> str:
    if isinstance(response_json.get("output_text"), str):
        return response_json["output_text"].strip()

    chunks: list[str] = []
    for item in response_json.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunk.strip() for chunk in chunks if chunk.strip())


def call_openai_api(records: list[RegistryRecord], report: ValidationReport, model: str, timeout: int, max_files: int) -> dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        message = "OPENAI_API_KEY is not configured; skipped OpenAI review."
        report.add("warning", "missing_openai_api_key", message)
        return {"status": "skipped", "reason": message}

    review_records = build_openai_payload(records, max_files=max_files)
    if not review_records:
        return {"status": "skipped", "reason": "No registry entry files available for OpenAI review."}

    prompt = {
        "governance_rules": [
            "Review only; do not propose automatic merges or canonical ID rewrites.",
            "Flag inconsistencies in canonical IDs, metadata, canonical links, and parent-child relationships.",
            "Return a concise markdown review with sections for risks, warnings, and human-governance recommendations.",
        ],
        "records": review_records,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "input": [
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "You are reviewing registry files for governance compliance. Only report findings and recommendations; never suggest automatic mutation.",
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": json.dumps(prompt, ensure_ascii=False)}],
                    },
                ],
                "max_output_tokens": 800,
            },
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        message = f"OpenAI review failed gracefully: {exc}"
        report.add("warning", "openai_review_failed", message)
        return {"status": "error", "reason": message}

    response_json = response.json()
    review_text = extract_openai_text(response_json)
    if not review_text:
        review_text = "OpenAI review completed but returned no review text."
        report.add("warning", "empty_openai_review", review_text)

    return {
        "status": "completed",
        "model": model,
        "reviewed_files": [item["path"] for item in review_records],
        "response_id": response_json.get("id"),
        "review": review_text,
    }


def render_markdown(report: ValidationReport) -> str:
    payload = report.as_dict()
    lines = [
        "# Registry Validation Report",
        "",
        f"- **Status:** {payload['status']}",
        f"- **Registry Path:** `{payload['registry_path']}`",
        f"- **Scanned Files:** {len(payload['scanned_files'])}",
        f"- **Skipped Files:** {len(payload['skipped_files'])}",
        f"- **Errors:** {payload['summary']['errors']}",
        f"- **Warnings:** {payload['summary']['warnings']}",
        f"- **Info:** {payload['summary']['info']}",
        "",
        "## Findings",
        "",
    ]
    if report.findings:
        for finding in report.findings:
            location = f" (`{finding.path}`)" if finding.path else ""
            lines.append(f"- **{finding.level.upper()}** `{finding.code}`{location}: {finding.message}")
    else:
        lines.append("- No structural or metadata findings.")

    lines.extend(["", "## OpenAI Review", ""])
    if report.openai_review:
        lines.append(f"- **Status:** {report.openai_review.get('status', 'unknown')}")
        if report.openai_review.get("reviewed_files"):
            lines.append("- **Reviewed Files:** " + ", ".join(f"`{path}`" for path in report.openai_review["reviewed_files"]))
        if report.openai_review.get("reason"):
            lines.append(f"- **Reason:** {report.openai_review['reason']}")
        if report.openai_review.get("review"):
            lines.extend(["", report.openai_review["review"]])
    else:
        lines.append("- OpenAI review was not requested.")

    return "\n".join(lines).rstrip() + "\n"


def generate_report(report: ValidationReport, json_report_path: str, markdown_report_path: str) -> tuple[str, str]:
    json_path = Path(json_report_path)
    markdown_path = Path(markdown_report_path)
    json_path.write_text(json.dumps(report.as_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(report)
    markdown_path.write_text(markdown, encoding="utf-8")
    return str(json_path), str(markdown_path)


def post_pr_comment(markdown_report: str, repo: str | None, pr_number: int | None, github_api_url: str) -> dict[str, Any]:
    if not repo or not pr_number:
        return {"status": "skipped", "reason": "Repository or PR number was not provided."}

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        return {"status": "skipped", "reason": "GITHUB_TOKEN is not available; skipped PR comment."}

    url = f"{github_api_url.rstrip('/')}/repos/{repo}/issues/{pr_number}/comments"
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
            },
            json={"body": markdown_report},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        return {"status": "error", "reason": f"Failed to post PR comment: {exc}"}
    payload = response.json()
    return {"status": "posted", "url": payload.get("html_url")}


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    report = ValidationReport(registry_path=args.registry_path)

    changed_files = read_changed_files(args.changed_files_file)
    LOGGER.info("Loaded %s changed file(s) for filtering.", len(changed_files))

    try:
        records = load_registry_files(args.registry_path, changed_files=changed_files, report=report)
    except FileNotFoundError as exc:
        LOGGER.error("%s", exc)
        return 1

    LOGGER.info("Loaded %s registry file(s) for validation.", len(records))

    validate_structure(records, report)
    validate_metadata(records, report)
    validate_canonical_links(records, report)
    report.openai_review = call_openai_api(records, report, args.openai_model, args.openai_timeout, args.openai_max_files)

    json_report_path, markdown_report_path = generate_report(report, args.json_report, args.markdown_report)
    LOGGER.info("Wrote JSON report to %s", json_report_path)
    LOGGER.info("Wrote Markdown report to %s", markdown_report_path)

    if args.post_pr_comment:
        comment_result = post_pr_comment(Path(markdown_report_path).read_text(encoding="utf-8"), args.repo, args.pr_number, args.github_api_url)
        LOGGER.info("PR comment result: %s", comment_result.get("status"))
        if comment_result.get("status") == "error":
            report.add("warning", "pr_comment_failed", comment_result["reason"])
            generate_report(report, args.json_report, args.markdown_report)

    return 1 if (report.error_count or report.warning_count) else 0


if __name__ == "__main__":
    sys.exit(main())
