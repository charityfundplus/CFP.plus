"""Invoke from the existing trusted CMP executor, never from an anonymous HTTP route."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys
import time

from notion_bridge import BridgeError, Journal, Model, Notion, Policy, Transport, digest, execute, open_private, page_id, prepare, require


def private_json(path):
    fd = open_private(path, os.O_RDONLY)
    with os.fdopen(fd, encoding="utf-8") as handle:
        require(os.fstat(handle.fileno()).st_size <= 100_000, "UNSAFE_PRIVATE_FILE")
        return json.load(handle)


def save_private(path, value):
    fd = open_private(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False)
        handle.flush()
        os.fsync(handle.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "execute"])
    parser.add_argument("--plan", required=True, help="Private plan path; must not be a public CI artifact")
    parser.add_argument("--provider", choices=["gemini", "meta"])
    parser.add_argument("--execution-id")
    parser.add_argument("--source-page")
    parser.add_argument("--parent-page")
    args = parser.parse_args(argv)
    try:
        raw = private_json(os.environ["CMP_POLICY_FILE"])
        policy = Policy(frozenset(page_id(x) for x in raw["read_pages"]),
                        frozenset(page_id(x) for x in raw["sandbox_parents"]),
                        raw.get("private_parent_confirmed") is True,
                        frozenset(raw.get("provider_access", [])),
                        frozenset(page_id(x) for x in raw.get("egress_pages", [])))
        transport = Transport()
        notion = Notion(os.environ.get("CMP_NOTION_TOKEN", ""), transport)
        state = Path(os.environ["CMP_STATE_DIR"])
        info = state.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() and
                not info.st_mode & 0o077, "UNSAFE_STATE_DIRECTORY")

        def audit(event):
            fd = open_private(state / "notion-bridge.audit.jsonl", os.O_CREAT | os.O_APPEND | os.O_WRONLY)
            with os.fdopen(fd, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(dict(event, timestamp=int(time.time())), sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

        if args.action == "prepare":
            model = Model(args.provider, os.environ.get("CMP_MODEL", ""),
                          os.environ.get("CMP_MODEL_TOKEN", ""), transport)
            plan = prepare(policy, notion, model, args.execution_id, args.source_page, args.parent_page, audit)
            save_private(args.plan, plan)
            print(json.dumps({"status": "AWAITING_APPROVAL", "plan_sha256": digest(plan)}))
        else:
            plan = private_json(args.plan)
            approval = private_json(os.environ["CMP_APPROVAL_FILE"])
            journal = Journal(str(state / "notion-bridge.sqlite"))

            try:
                receipt = execute(policy, notion, plan, approval, os.environ.get("CMP_APPROVAL_KEY", ""),
                                  journal, audit)
            finally:
                journal.db.close()
            # Local stdout is for the private executor, not a public Actions log.
            print(json.dumps(receipt, sort_keys=True))
        return 0
    except BridgeError as error:
        print(json.dumps({"status": "BLOCKED", "code": str(error)}))
    except Exception:
        # Last boundary: never expose upstream objects, paths, credentials or traceback.
        print(json.dumps({"status": "BLOCKED", "code": "CONFIG_OR_STORAGE_INVALID"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())
