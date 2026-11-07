"""Evidence • chạy bộ hỏi đáp tư vấn qua /api/office/answer-check trên server thật (HTTPS sandbox).

Dùng tài khoản thử nghiệm tự đăng ký (@example.org, dữ liệu sandbox tạm) — không cần secrets, không quyền đặc biệt.
Evidence JSON KHÔNG chứa nội dung bản nháp/câu hỏi/câu trích: chỉ case id • sha256 bản nháp • build • guard_version •
verdict • reason codes • categories • trạng thái ID • PASS/FAIL. AUTO REPLY HOLD được kiểm cho mọi case.
"""
import argparse
import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from tests.forum.smoke_live import H, Smoke, expect

ROOT = Path(__file__).resolve().parents[2]


def run(base: str, cases_file: Path, allow_http: bool = False) -> dict:
    if not base.startswith("https://") and not allow_http:
        raise SystemExit("Chỉ chạy trên HTTPS (dùng --allow-http cho server local).")
    doc = json.loads(cases_file.read_text("utf-8"))
    s = Smoke(base)
    u = s.client()
    health = expect(u.get("/api/health"), 200)
    tag = uuid.uuid4().hex[:8]
    expect(u.post("/api/auth/register", headers=H, json={"email": f"agent-ev-{tag}@example.org",
                                                         "password": f"agent-ev-{tag}-pw", "name": f"Agent Evidence {tag}"}), 200, 201)
    rows = []
    for c in doc["cases"]:
        r = expect(u.post("/api/office/answer-check", headers=H, json={
            "draft": c["draft"], "question": c["question"], "agent": "Meta Business Agent (simulated)"}), 200)
        if "guard_version" not in r or "ids" not in r:
            raise SystemExit(f"AGENT_EVIDENCE=FAIL runtime build={health.get('build')} chưa có guard 6 nhóm rủi ro "
                             "(thiếu guard_version/ids) — cần deploy bản mới trước khi lấy Evidence.")
        codes = sorted({f["code"] for f in r["findings"]})
        ids = {x["id"]: x["status"] for x in r["ids"]}
        ok = (r["verdict"] == c["expected_verdict"] and set(c["required_codes"]) <= set(codes)
              and all(ids.get(k) == v for k, v in c["expected_id_status"].items()) and r["auto_reply"] == "HOLD")
        rows.append({"case": c["id"], "risk": c["risk"], "draft_sha256": r["draft_sha256"],
                     "expected": c["expected_verdict"], "verdict": r["verdict"], "codes": codes,
                     "categories": r["categories"], "ids": ids, "auto_reply": r["auto_reply"], "pass": ok})
        print(f"[{'PASS' if ok else 'FAIL'}] {c['id']} {c['risk']:16} → {r['verdict']:22} {codes} {ids}", flush=True)
    u.post("/api/auth/logout", headers=H)
    passed = sum(x["pass"] for x in rows)
    return {"evidence": "agent.answer_check", "base": base, "at": datetime.now(timezone.utc).isoformat(),
            "build": health.get("build"), "guard_version": rows and r.get("guard_version"),
            "cases_file": str(cases_file.relative_to(ROOT)), "cases_sha256": hashlib.sha256(cases_file.read_bytes()).hexdigest()[:16],
            "origin": doc["origin"], "passed": passed, "failed": len(rows) - passed, "total": len(rows),
            "result": "PASS" if passed == len(rows) else "FAIL", "auto_reply": "HOLD",
            "redaction": "không lưu nội dung bản nháp/câu hỏi; chỉ sha256 + mã kết quả", "rows": rows}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--cases", default=str(ROOT / "services/forum/agents/cases/app-cfp-simulated.json"))
    ap.add_argument("--out", default="agent-evidence.json")
    ap.add_argument("--allow-http", action="store_true")
    a = ap.parse_args()
    ev = run(a.base, Path(a.cases), a.allow_http)
    Path(a.out).write_text(json.dumps(ev, ensure_ascii=False, indent=1), "utf-8")
    print(f"AGENT_EVIDENCE={ev['result']} passed={ev['passed']}/{ev['total']} build={ev['build']} guard={ev['guard_version']}")
    sys.exit(0 if ev["result"] == "PASS" else 1)
