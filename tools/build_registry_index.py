#!/usr/bin/env python3
"""Build registry/registry-md-index.json from registry/<ID>.md records.

Read-only over the records: does not create, rename or renumber any ID.
The website resolver (/id/index.html) uses the index so https://cfp.plus/<ID>
shows the registered name instead of a generic reserved slot.

Usage: python3 tools/build_registry_index.py [--check]
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "registry"
OUT = REG / "registry-md-index.json"
SRC = "https://github.com/charityfundplus/CFP.plus/blob/main/registry/"

KEYS = {
    "canonical id": "id",
    "entity name": "name", "entity": "name", "ai name": "name",
    "entity type": "entity_type",
    "parent id": "parent", "parent canonical id": "parent", "parent": "parent",
    "parent entity": "parent", "parent hub": "parent",
    "lifecycle status": "status", "status": "status",
    "developer": "developer", "country": "country",
}
KV = re.compile(r"^\s*(?:\*\*)?([A-Za-z][A-Za-z ]{1,30}?)(?::\*\*|\*\*:|:)\s*(.+?)\s*$")


def clean(v):
    v = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", v)  # markdown links -> text
    return v.replace("**", "").strip()


def parse(path):
    text = path.read_text(encoding="utf-8")
    rec, heading = {}, ""
    for line in text.splitlines()[:60]:
        if not heading and line.startswith("# "):
            heading = line[2:].strip()
        m = KV.match(line)
        if m:
            k = KEYS.get(m.group(1).strip().lower())
            if k and k not in rec:
                rec[k] = clean(m.group(2))
    return text, heading, rec


def build():
    index, issues = {}, []
    for path in sorted(REG.glob("*.md"), key=lambda p: (len(p.stem), p.stem)):
        fid = path.stem
        if not fid.isdigit():
            continue
        text, heading, rec = parse(path)
        if not text.strip():
            issues.append({"id": fid, "issue": "EMPTY_RECORD"})
            continue
        rid = re.sub(r"\D", "", rec.get("id", "")) or fid
        if rid != fid:
            issues.append({"id": fid, "issue": f"FILENAME_ID_MISMATCH:{rid}"})
            continue
        name = rec.get("name")
        if not name:
            name = re.sub(r"^\d+\s*•\s*", "", heading).strip() or None
        parent = re.match(r"\d+", rec.get("parent", "")) if rec.get("parent") else None
        entry = {
            "id": fid,
            "name": name,
            "entity_type": rec.get("entity_type"),
            "parent_id": parent.group(0) if parent else None,
            "status": rec.get("status"),
            "developer": rec.get("developer"),
            "country": rec.get("country"),
            "source": SRC + path.name,
        }
        index[fid] = {k: v for k, v in entry.items() if v}
        if not name:
            issues.append({"id": fid, "issue": "NAME_NOT_FOUND"})
    return {
        "_meta": {
            "purpose": "Machine index of registry/<ID>.md for the https://cfp.plus/<ID> resolver",
            "generator": "tools/build_registry_index.py",
            "rule": "Derived data only. registry/<ID>.md stays the source of record; no ID is created or changed here.",
            "count": len(index),
            "issues": issues,
        },
        "records": index,
    }


def main():
    data = json.dumps(build(), ensure_ascii=False, indent=1, sort_keys=False) + "\n"
    if "--check" in sys.argv:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != data:
            print("registry-md-index.json is stale: run python3 tools/build_registry_index.py")
            return 1
        print("registry-md-index.json is up to date")
        return 0
    OUT.write_text(data, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
