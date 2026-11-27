"""Generate a read-only coverage inventory from pinned Git sources."""

import argparse
import json
import re
import subprocess
from collections import defaultdict
from datetime import date, timedelta

GROUPS = {
    "000": "0",
    "135": "135",
    "246": "246",
    "789": "789",
    "V & D": "",
}
CHAPTER_GROUP = {digit: group for group, digits in GROUPS.items() for digit in digits}
TRIO_ROOT = "sandbox/87788-super-trio"
TRIO_INDEX = f"{TRIO_ROOT}/data/source/SUPER_PAIRS_INDEX@77102841.md"
TRIO_ADDITIONS = f"{TRIO_ROOT}/data/additions.json"


def inventory(repo_ref, trio_ref):
    sources = defaultdict(set)

    def git(*args):
        return subprocess.check_output(["git", *args], text=True)

    repo_ref = git("rev-parse", "--verify", repo_ref + "^{commit}").strip()
    trio_ref = git("rev-parse", "--verify", trio_ref + "^{commit}").strip()
    for path in git("ls-tree", "-r", "--name-only", repo_ref).splitlines():
        match = re.match(r"^([0-9]+)/(?:index\.html|README\.md)$|^registry/([0-9]+)\.md$", path)
        if match:
            sources[match[1] or match[2]].add(path)
    entities = json.loads(git("show", f"{repo_ref}:registry/ai-entity-registry.json"))
    for record in entities.values():
        if "id" in record:
            sources[record["id"]].add("registry/ai-entity-registry.json")

    trio_rows = defaultdict(list)
    for line_number, line in enumerate(git("show", f"{trio_ref}:{TRIO_INDEX}").splitlines(), 1):
        match = re.match(r"^\|\s*`([0-9]+)`\s*\|", line)
        if match:
            trio_rows[match[1]].append(f"{TRIO_INDEX}:{line_number}")
    additions = json.loads(git("show", f"{trio_ref}:{TRIO_ADDITIONS}"))
    for record in additions["records"]:
        if re.fullmatch(r"[0-9]+", record["id"]):
            trio_rows[record["id"]].append(f"{TRIO_ADDITIONS}:{record['name']}")
    for identity, refs in trio_rows.items():
        sources[identity].update(refs)

    roles = defaultdict(list)
    for size, role in [(1, "Chương"), (2, "Con"), (3, "Cháu")]:
        for index in range(10 ** size):
            roles[f"{index:0{size}d}"].append(role)
    roles["5"].append("V")
    roles["500"].append("D")
    for offset in range(366):
        day = date(2024, 1, 1) + timedelta(days=offset)
        roles[day.strftime("%m%d")].append("Ngày")
    for identity in sources:
        if len(identity) >= 4:
            roles[identity].append("Chuyên trách")

    return {
        "registry_commit": repo_ref,
        "pr_253_commit": trio_ref,
        "groups": GROUPS,
        "records": {
            identity: {
                "roles": bindings,
                "chapter": identity[0],
                "group": CHAPTER_GROUP[identity[0]],
                "additional_groups": ["V & D"] if identity in {"5", "500"} else [],
                "sources": sorted(sources[identity]),
                "status": (
                    "review_overlap" if len(bindings) > 1 or len(trio_rows[identity]) > 1
                    else "source_match" if sources[identity] else "unbound"
                ),
            }
            for identity, bindings in sorted(roles.items())
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry_git_ref")
    parser.add_argument("pr_253_git_ref")
    args = parser.parse_args()
    print(json.dumps(inventory(args.registry_git_ref, args.pr_253_git_ref),
                     ensure_ascii=False, indent=2))
