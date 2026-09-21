import json
import os
from pathlib import Path
from typing import Any, Dict


class EvidenceStore:
    """P0 persistent Evidence Store using atomic filesystem writes.

    This is operational storage, not CFP+ Canonical content. Production storage
    can replace this implementation behind the same interface.
    """

    def __init__(self, root: str | Path | None = None):
        configured = root or os.getenv("CFP_EVIDENCE_DIR", "var/evidence")
        self.root = Path(configured)
        self.root.mkdir(parents=True, exist_ok=True)

    def write(self, execution_id: str, package: Dict[str, Any]) -> str:
        if not execution_id or any(part in execution_id for part in ("/", "\\", "..")):
            raise ValueError("Invalid Operational Execution ID for evidence storage")

        target = self.root / f"{execution_id}.json"
        temp = self.root / f".{execution_id}.json.tmp"
        serialized = json.dumps(
            package,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        temp.write_text(serialized, encoding="utf-8")
        os.replace(temp, target)
        return target.resolve().as_uri()

    def read(self, execution_id: str) -> Dict[str, Any]:
        target = self.root / f"{execution_id}.json"
        return json.loads(target.read_text(encoding="utf-8"))
