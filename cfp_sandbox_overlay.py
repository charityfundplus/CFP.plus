"""Explicit, hash-pinned fixtures for isolated SQLite sandbox instances."""
import hashlib
import json
import os
from pathlib import Path


def load_overlay(canonical_ids, *, ephemeral=None):
    path = os.environ.get("HUB69_SANDBOX_REGISTRY_OVERLAY")
    if not path:
        return {}
    enabled = os.environ.get("CFP_SANDBOX_EPHEMERAL") == "1" if ephemeral is None else ephemeral
    if not enabled:
        raise ValueError("SANDBOX_OVERLAY_REQUIRES_EPHEMERAL")
    raw = Path(path).read_bytes()
    expected = os.environ.get("HUB69_SANDBOX_REGISTRY_SHA256")
    if len(raw) > 65536 or not expected or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("SANDBOX_OVERLAY_CHECKSUM")
    doc = json.loads(raw)
    if doc.get("version") != 1 or doc.get("synthetic") is not True:
        raise ValueError("SANDBOX_OVERLAY_FORMAT")
    records = doc.get("records")
    if not isinstance(records, list) or len(records) > 94:
        raise ValueError("SANDBOX_OVERLAY_RECORDS")
    result = {}
    for row in records:
        key = row.get("key")
        if (not isinstance(key, str) or not key.isascii() or not key.isdigit()
                or not 1 <= len(key) <= 32 or key in canonical_ids or key in result
                or row.get("parent") is not None or row.get("sandbox_fixture") is not True
                or not isinstance(row.get("name"), str) or not row["name"].strip()
                or not isinstance(row.get("source"), str) or not row["source"].startswith("https://")
                or not row.get("source_revision")):
            raise ValueError("SANDBOX_OVERLAY_BINDING")
        result[key] = row
    return result
