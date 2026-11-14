"""Sandbox test: https://cfp.plus/<ID> resolves to the registered entity.

Emulates the Dockerfile nginx rule for numeric paths
(try_files $uri/index.html $uri /id/index.html) and runs the real resolver.
Run: python3 tests/routing/test_id_routing.py
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def resolve(i):
    if (ROOT / i / "index.html").exists():
        return {"id": i, "served": f"/{i}/index.html (static)"}
    out = subprocess.run(["node", str(ROOT / "tests/routing/resolve_id.mjs"), str(ROOT), i],
                         capture_output=True, text=True, check=True).stdout
    r = json.loads(out); r["served"] = "/id/index.html (resolver)"
    return r


def main():
    fails = []
    chk = subprocess.run([sys.executable, str(ROOT / "tools/build_registry_index.py"), "--check"],
                         capture_output=True, text=True)
    if chk.returncode:
        fails.append("index stale: " + chk.stdout.strip())
    idx = json.loads((ROOT / "registry/registry-md-index.json").read_text(encoding="utf-8"))
    ents = json.loads((ROOT / "registry/ai-entity-registry.json").read_text(encoding="utf-8"))
    rows = []
    for i, rec in idx["records"].items():
        r = resolve(i)
        if "title" in r:
            expect = ents[i]["name"] if i in ents else rec["name"]
            ok = expect in (r["title"] or "") and f"/{i}/" in r["body"]
            if rec.get("parent_id") and i not in ents:
                ok = ok and f'href="/{rec["parent_id"]}/"' in r["body"]
            if not ok:
                fails.append(f"{i}: expected '{expect}', got '{r['title']}'")
        rows.append((i, r["served"], r.get("title", "-")))
    # Unregistered, non-formula ID must not invent an entity.
    u = resolve("12345678901")
    if "Chưa định vị" not in u["title"]:
        fails.append("unknown ID rendered as entity: " + u["title"])
    rows.append(("12345678901", u["served"], u["title"]))
    # Hostile path segment must stay escaped.
    x = resolve('691183"><img src=x onerror=alert(1)>')
    if "<img" in x["body"]:
        fails.append("unescaped ID in body")
    for row in rows:
        print(" | ".join(row))
    print(f"\n{len(rows)} routes checked, {len(fails)} failures")
    for f in fails:
        print("FAIL", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
