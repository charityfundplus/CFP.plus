"""Work Order MCP-DDB8FF1A5BD9: validator ID Số Sống theo quy tắc đã xác minh (Mẫu Chung 366)."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from sqz.api import create_app
from sqz.idformula import (FUNCTIONS, MMDD, check_assignments, daily_record_allowed, mmdd_for,
                           mmdd_keys, record_key, validate)
from sqz.store import Store


# R1, R2: chữ số 0–9, số 0 đầu
def test_digits_only_and_leading_zeros():
    for good in ("0", "00", "000", "0229", "6776", "87788", "000000000000"):
        assert validate(good)["valid"], good
    assert validate("00")["leading_zeros"] == 2 and validate("0229")["leading_zeros"] == 1
    for bad in ("", "6a", "-1", "1.0", " 69", "٦٧", "６７", "10\n"):
        assert not validate(bad)["valid"], repr(bad)
    r = validate(229)
    assert not r["valid"] and "R2" in r["errors"][0]  # số nguyên làm mất số 0 đầu


def test_ten_is_two_levels_not_branch_ten():
    r = validate("10")
    assert r["depth"] == 2 and [l["branch"] for l in r["levels"]] == ["1", "0"]
    assert r["chapter"] == "1" and r["structural_parent"] == "1"
    assert sorted(FUNCTIONS) == [str(d) for d in range(10)]  # không có nhãn 10


# R3: phân tầng, Chương, Nhóm
def test_hierarchy_levels_chapter_group():
    r = validate("87728")
    assert [l["prefix"] for l in r["levels"]] == ["8", "87", "877", "8772", "87728"]
    assert r["chapter"] == "8" and r["group"] == "789" and r["structural_parent"] == "8772"
    assert any("DỰ KIẾN" in p for p in r["pending"]) and any("registry" in p for p in r["pending"])
    assert validate("D")["kind"] == "GATE_GROUP" and validate("V")["valid"]
    assert {validate(str(d))["group"] for d in range(10)} == {"000", "135", "246", "789"}


# R4: MMDD + 0229
def test_mmdd_366_keys_and_leap_day():
    keys = mmdd_keys()
    assert len(keys) == len(set(keys)) == 366 and keys[0] == "0101" and keys[-1] == "1231"
    assert "0229" in MMDD and "0230" not in MMDD and "1131" not in MMDD and "0001" not in MMDD
    assert daily_record_allowed("0229", 2024) and daily_record_allowed("0229", 2000)
    assert not daily_record_allowed("0229", 2026) and not daily_record_allowed("0229", 1900)
    assert not daily_record_allowed("0229", 2100)
    # năm thường: 365 Daily Record; năm nhuận: 366
    assert sum(daily_record_allowed(k, 2026) for k in keys) == 365
    assert sum(daily_record_allowed(k, 2028) for k in keys) == 366
    d, seen = date(2024, 1, 1), set()
    while d.year == 2024:
        seen.add(mmdd_for(d))
        d += timedelta(days=1)
    assert seen == MMDD  # khớp lịch thật của một năm nhuận


def test_ddmm_legacy_detected_when_mmdd_required():
    assert validate("1127", as_mmdd=True)["valid"]  # 27/11
    r = validate("2711", as_mmdd=True)  # DDMM cũ của 27/11
    assert not r["valid"] and "1127" in r["errors"][0]
    assert not validate("229", as_mmdd=True)["valid"]
    assert validate("0102")["warnings"]  # đọc được cả hai nghĩa → cảnh báo, giữ nghĩa MMDD


# Kiêm nhiệm • chống trùng • idempotency
def test_concurrent_roles_duplicates_and_conflicts():
    recs = [
        {"id": "6776", "role": "software", "name": "Open Siêu Phần Mềm"},
        {"id": "6776", "role": "Software ", "name": "Open Siêu Phần Mềm"},  # trùng sau chuẩn hóa
        {"id": "6776", "role": "ops-1127", "context": "1127"},  # kiêm nhiệm hợp lệ
        {"id": "0229", "role": "host"},
        {"id": "229", "role": "host"},  # khác ID (mất số 0) → không gộp
        {"id": "6a", "role": "x"},
        {"id": "8882", "name": "A"}, {"id": "8882", "name": "B", "role": "r2"},
    ]
    r = check_assignments(recs)
    assert [d["index"] for d in r["duplicates"]] == [1]
    assert r["concurrent_roles"]["6776"] == ["ops-1127", "software"]
    assert {i["id"] for i in r["invalid"]} == {"6a"}
    assert r["name_conflicts"] == [{"id": "8882", "names": ["A", "B"]}] and not r["ok"]
    assert record_key({"id": "1", "role": "A", "context": "x"}) == record_key({"context": "x", "role": "a ", "id": "1"})


@pytest.fixture()
def client():
    with TestClient(create_app(Store())) as c:
        yield c


def test_api_validator_endpoints(client):
    assert client.get("/ids/0229/validate").json()["valid"]
    assert client.get("/ids/2711/validate", params={"as_mmdd": True}).json()["valid"] is False
    m = client.get("/ids/mmdd", params={"year": 2026}).json()
    assert m["count"] == 366 and m["includes_0229"] and m["daily_record_count"] == 365
    b = client.post("/ids/validate-batch", json={"ids": ["0", "00", "0", "6x"],
                                                 "assignments": [{"id": "6776", "role": "a"}]}).json()
    assert b["valid"] == 3 and b["duplicates"] == ["0"] and b["invalid"][0]["id"] == "6x"
    assert b["assignments"]["ok"]


def test_auto_pipeline_intake_execute_check_handover():
    from sqz.worker import Worker

    s = Store()
    ok = s.submit("6789", "maxcut", {"n": 4, "edges": [[0, 1, 1], [1, 2, 1], [2, 3, 1], [3, 0, 1]]}, "CLAUDE_CODE")
    bad = s.submit("6789", "maxcut", {"n": 3, "edges": [[0, 0, 1]]}, "CLAUDE_CODE")
    w = Worker(s, name="w", auto_handover=True)
    while w.step():
        pass
    rv = s.reviews_of(ok)
    assert rv and rv[0]["reviewer_id"] == "6788" and rv[0]["verdict"] == "APPROVED"
    events = [e for e in s.recent(limit=10)]
    assert s.get(bad)["status"] == "FAILED" and not s.reviews_of(bad)  # lỗi: không bàn giao tự động
    from sqz.pipeline import auto_check_and_handover

    h = auto_check_and_handover(s, ok)
    assert h["evidence_check"]["valid"] and h["report"]["status"] == "DONE"
    assert h["report"]["reviewer_id"] == "6788" and h["report"]["owner_id"] == "6789"
    assert s.verify_audit()["ok"] and events
