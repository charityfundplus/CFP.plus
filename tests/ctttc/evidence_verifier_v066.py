import hashlib
import urllib.request
from datetime import datetime, timezone

EXPECTED_README_SHA256 = "0cca6b93c8b705abfeb2b58f2669bb10f244ab80e4b63a53561b0ffd14d5a254"
PINNED_README_URL = "https://raw.githubusercontent.com/charityfundplus/CFP.plus/99aab62ef356d015a682ae85328b3e80a9df2ffe/README.md"

def verify_evidence_artifact(source_url: str, declared_hash: str) -> dict:
    result = {
        "source_url": source_url,
        "declared_sha256": declared_hash,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "http_status": None,
        "resolved_url": None,
        "content_type": None,
        "content_length": 0,
        "computed_sha256": None,
        "hash_match": False,
        "verification_result": "FAIL"
    }
    req = urllib.request.Request(source_url, headers={"User-Agent": "CFP-Plus-CTTTC-Verifier/0.6.6"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()
        result.update(
            http_status=resp.getcode(),
            resolved_url=resp.geturl(),
            content_type=resp.headers.get("Content-Type", ""),
            content_length=len(data),
            computed_sha256=hashlib.sha256(data).hexdigest()
        )
    result["hash_match"] = result["computed_sha256"].lower() == declared_hash.lower()
    result["verification_result"] = "PASS_INTEGRITY" if result["http_status"] == 200 and result["hash_match"] else "FAIL_HASH_MISMATCH"
    return result

def classify_claim_support(record: dict, source_text: str):
    words = [w.strip(".,:;!?()[]{}").lower() for w in (record.get("title", "") + " " + record.get("summary", "")).split()]
    keywords = [w for w in words if len(w) > 4]
    if not keywords:
        return "SEMANTIC_REVIEW_REQUIRED", 0.0
    text = source_text.lower()
    ratio = sum(1 for w in keywords if w in text) / len(keywords)
    return "SEMANTIC_REVIEW_REQUIRED", ratio
