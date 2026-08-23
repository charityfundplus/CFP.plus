import re
import unicodedata


def _normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _same_similarity_scope(left: dict, right: dict) -> bool:
    return (
        left.get("day_key") == right.get("day_key")
        and _normalize_text(left.get("title", "")) == _normalize_text(right.get("title", ""))
        and _normalize_text(left.get("domain", "")) == _normalize_text(right.get("domain", ""))
        and _normalize_text(left.get("scale", "")) == _normalize_text(right.get("scale", ""))
    )


def control_duplicate(record: dict, existing_records: list) -> str:
    fp = record.get("exact_fingerprint")
    if fp and any(x.get("exact_fingerprint") == fp for x in existing_records):
        return "EXACT_DUPLICATE"
    if any(_same_similarity_scope(record, existing) for existing in existing_records):
        return "SIMILARITY_REVIEW"
    return "DISTINCT_EVENT"
