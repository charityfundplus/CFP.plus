#!/usr/bin/env python3
"""Governance-safe P0 validator for the CFP+ United States AI reference branch.

Read-only checks only. This script never allocates or changes Canonical IDs/Links.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
errors = []
notes = []


def read(rel):
    p = ROOT / rel
    if not p.exists():
        errors.append(f"MISSING_FILE: {rel}")
        return ""
    return p.read_text(encoding="utf-8")

# Locked anchors and current Human-Governance developer allocation.
expected = {
    "69110": "Developer & Platform Directory",
    "69111": "Amazon",
    "69112": "Anthropic",
    "69113": "Apple",
    "69114": "Google DeepMind",
    "69115": "Meta",
    "69116": "Microsoft",
    "69117": "NVIDIA",
    "69118": "OpenAI",
    "69119": "xAI",
}

locked = read("registry/GLOBAL_COUNTRY_AI_ID_LOCKED.md")
if "United States | `911` | `6911`" not in locked:
    errors.append("LOCKED_ANCHOR_MISSING: expected United States 911 -> 6911")

# Every current developer profile must exist and identify the expected entity.
for cid, name in expected.items():
    text = read(f"registry/{cid}.md")
    if f"**Canonical ID:** {cid}" not in text:
        errors.append(f"CANONICAL_ID_MISMATCH: registry/{cid}.md")
    if f"**Entity Name:** {name}" not in text:
        errors.append(f"ENTITY_NAME_MISMATCH: {cid} expected {name}")
    if "**Parent:** 6911" not in text:
        errors.append(f"PARENT_MISMATCH: {cid} expected parent 6911")

# Active indexes must show current developer allocation, not legacy ownership.
for rel in ("AI_INDEX.md", "registry/AI_CANONICAL_ID_REGISTRY.md"):
    text = read(rel)
    for cid, name in expected.items():
        # flexible line check: ID and current name must occur on the same table line.
        if not any(cid in line and name in line for line in text.splitlines()):
            errors.append(f"ACTIVE_INDEX_MISSING_CURRENT: {rel} {cid} {name}")

# Known legacy AI-child files remain traceable but may not be silently promoted.
legacy_children = {
    "691100": "ChatGPT",
    "691110": "Claude",
    "691120": "Grok",
    "691130": "Gemini",
    "691131": "NotebookLM",
    "691140": "Meta AI",
    "691150": "Microsoft Copilot",
    "691160": "Perplexity AI",
    "691170": "Groq",
}
registry = read("registry/AI_CANONICAL_ID_REGISTRY.md")
for cid, name in legacy_children.items():
    if not (ROOT / f"registry/{cid}.md").exists():
        errors.append(f"LEGACY_EVIDENCE_MISSING: registry/{cid}.md")
    # Migration table must explicitly quarantine each legacy child.
    matching = [line for line in registry.splitlines() if cid in line and name in line]
    if not matching or not any("REMAP_REQUIRED" in line for line in matching):
        errors.append(f"LEGACY_NOT_QUARANTINED: {cid} {name}")

# Detect duplicate numeric registry filenames (case-normalized path identity).
seen = {}
for p in (ROOT / "registry").glob("*.md"):
    stem = p.stem
    if re.fullmatch(r"\d+", stem):
        key = stem.lstrip("0") or "0"
        if key in seen and seen[key] != p.name:
            errors.append(f"DUPLICATE_NUMERIC_PATH: {seen[key]} and {p.name}")
        seen[key] = p.name

# Public README should remain compact and route legacy handling away from active navigation.
readme = read("README.md")
if "GitHub Public Structure & Legacy Handling" not in readme:
    errors.append("PUBLIC_STRUCTURE_RULE_NOT_LINKED")
if len(readme.splitlines()) > 80:
    errors.append(f"README_TOO_LONG: {len(readme.splitlines())} lines")

if errors:
    print("CMP P0 US VALIDATION: FAIL")
    for e in errors:
        print(f"- {e}")
    sys.exit(1)

print("CMP P0 US VALIDATION: PASS")
print(f"- locked anchors: 911 -> 6911")
print(f"- current developer records checked: {len(expected)}")
print(f"- legacy child records quarantined: {len(legacy_children)}")
print(f"- numeric registry paths checked: {len(seen)}")
print("- no Canonical ID/Link mutation performed")
