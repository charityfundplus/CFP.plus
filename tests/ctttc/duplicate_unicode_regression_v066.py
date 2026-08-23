from tests.ctttc.duplicate_control_v066 import control_duplicate


def main():
    existing = [
        {
            "day_key": "08-23",
            "title": "人工智能全球事件",
            "domain": "人工智能",
            "scale": "全球",
            "exact_fingerprint": "a" * 64,
        },
        {
            "day_key": "08-23",
            "title": "世界AIイベント",
            "domain": "技術",
            "scale": "世界",
            "exact_fingerprint": "b" * 64,
        },
        {
            "day_key": "08-23",
            "title": "글로벌 AI 이벤트",
            "domain": "기술",
            "scale": "글로벌",
            "exact_fingerprint": "c" * 64,
        },
    ]

    tests = [
        (
            {
                "day_key": "08-23",
                "title": "人工智能全球事件！",
                "domain": "人工智能",
                "scale": "全球",
                "exact_fingerprint": "d" * 64,
            },
            "SIMILARITY_REVIEW",
            "Chinese punctuation normalization",
        ),
        (
            {
                "day_key": "08-23",
                "title": "世界AIイベント",
                "domain": "別分野",
                "scale": "世界",
                "exact_fingerprint": "e" * 64,
            },
            "DISTINCT_EVENT",
            "Japanese content preserved and domain separates scope",
        ),
        (
            {
                "day_key": "08-23",
                "title": "글로벌 AI 이벤트",
                "domain": "기술",
                "scale": "글로벌",
                "exact_fingerprint": "f" * 64,
            },
            "SIMILARITY_REVIEW",
            "Korean content preserved",
        ),
        (
            {
                "day_key": "08-23",
                "title": "完全不同",
                "domain": "完全不同",
                "scale": "完全不同",
                "exact_fingerprint": "0" * 64,
            },
            "DISTINCT_EVENT",
            "different CJK text must not collapse to empty normalization",
        ),
    ]

    failed = 0
    for record, expected, label in tests:
        got = control_duplicate(record, existing)
        ok = got == expected
        print(f"[{'PASS' if ok else 'FAIL'}] {label}: expected={expected} got={got}")
        failed += int(not ok)
    print("Unicode duplicate regression failed:", failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
