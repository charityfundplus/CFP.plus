def control_duplicate(record: dict, existing_records: list) -> str:
    fp = record.get("exact_fingerprint")
    if fp and any(x.get("exact_fingerprint") == fp for x in existing_records):
        return "EXACT_DUPLICATE"
    if any(x.get("day_key") == record.get("day_key") and x.get("title") == record.get("title") for x in existing_records):
        return "SIMILARITY_REVIEW"
    return "DISTINCT_EVENT"
