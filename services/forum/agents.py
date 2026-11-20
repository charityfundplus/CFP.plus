"""Siêu Bộ Đôi • Agent bên ngoài (vd. Meta Business Agent) + Siêu Phần Mềm giám sát — chế độ TRAINING trong sandbox.

Cấu hình đào tạo: services/forum/agents/<slug>.json (chỉ đọc lúc chạy; đổi cấu hình = commit có review).
  • knowledge   : chỉ trang ID đã xuất bản trên cfp.plus (Link Mẫu, version sha256). HOLD → loại; Parent HOLD → "verifying".
  • scenarios   : bộ kiểm thử tình huống tư vấn; chạy bằng answer_guard → kết quả xác định (deterministic).
  • test-run sha: sha256(cấu hình + version nguồn + kết quả). Evidence URL /test-runs/<sha> tính lại được bởi bất kỳ ai;
                  nguồn/cấu hình đổi → sha khác → Evidence cũ báo 409 (không coi là còn hiệu lực).
Không kết nối Meta API, không gửi trả lời cho khách, không cấp ID. stage/flags chỉ đổi qua commit + Human Governance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from services.forum.answer_guard import check_answer

AGENTS_DIR = Path(__file__).resolve().parent / "agents"
LOCKED_FLAGS = {"auto_reply": "HOLD", "production": "NO-GO"}  # trước HUMAN_APPROVAL không được khác


def load_agents(d: Path = AGENTS_DIR) -> dict[str, dict]:
    out = {}
    for f in sorted(d.glob("*.json")):
        raw = f.read_bytes()
        cfg = json.loads(raw)
        cfg["config_version"] = "sha256:" + hashlib.sha256(raw).hexdigest()[:16]
        cfg["config_source"] = f"repo:services/forum/agents/{f.name}"
        if cfg.get("stage") != "PRODUCTION":
            for k, v in LOCKED_FLAGS.items():
                if cfg.get("flags", {}).get(k) != v:
                    raise ValueError(f"{f.name}: {k} phải là {v} khi chưa HUMAN_APPROVAL")
        out[cfg["slug"]] = cfg
    return out


def knowledge(cfg: dict, catalog) -> dict:
    rows = []
    for cid in cfg["knowledge"]["core_ids"]:
        it = catalog.items.get(cid) if catalog is not None else None
        if not it:
            rows.append({"id": cid, "status": "missing", "use": False, "note": "Chưa có trang đã xuất bản — không dùng."})
            continue
        st = it["parent_status"]
        use = st != "hold_conflict" and it["classification"] == "PUBLIC"
        rows.append({"id": cid, "url": it["canonical_url"], "title": it["title"], "version": it["version"],
                     "status": "excluded_hold" if st == "hold_conflict" else "verifying" if st == "parent_hold" else "approved_source",
                     "use": use, "parent_status": st})
    return {"rule": cfg["knowledge"]["rule"], "sources": rows,
            "approved": sum(r["status"] == "approved_source" for r in rows),
            "verifying": sum(r["status"] == "verifying" for r in rows),
            "excluded": sum(not r["use"] for r in rows)}


def run_tests(cfg: dict, catalog, registry=None) -> dict:
    results = []
    for s in cfg["scenarios"]:
        res = check_answer(s["draft"], catalog, s.get("question"), registry=registry)
        got = sorted({f["code"] for f in res["findings"]})
        ok = res["verdict"] == s["verdict"] and set(s["codes"]) <= set(got) and res["auto_reply"] == "HOLD"
        results.append({"name": s["name"], "expected": s["verdict"], "got": res["verdict"], "codes": got,
                        "required": s["codes"], "pass": ok})
    kb = knowledge(cfg, catalog)
    from services.forum.answer_guard import GUARD_VERSION
    basis = {"config": cfg["config_version"], "guard": GUARD_VERSION, "sources": [(r["id"], r.get("version")) for r in kb["sources"]],
             "results": results}
    sha = hashlib.sha256(json.dumps(basis, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    return {"slug": cfg["slug"], "sha": sha, "config_version": cfg["config_version"], "guard_version": GUARD_VERSION,
            "passed": sum(r["pass"] for r in results), "failed": sum(not r["pass"] for r in results),
            "total": len(results), "results": results, "auto_reply": "HOLD", "stage": cfg["stage"],
            "note": "Kết quả kiểm thử trong sandbox — chưa phải nghiệm thu. Nghiệm thu = Evidence + Review độc lập + Human Approval."}


def public_view(cfg: dict, catalog, registry=None) -> dict:
    run = run_tests(cfg, catalog, registry)
    return {k: cfg[k] for k in ("slug", "name", "developer", "developer_ref", "canonical_id", "id_status", "pair", "stage",
                                "pipeline", "flags", "languages", "instructions", "escalate", "contact",
                                "config_version", "config_source")} | {
        "developer_ref_status": (catalog.items.get(cfg["developer_ref"]) or {}).get("parent_status") if catalog else None,
        "knowledge": knowledge(cfg, catalog),
        "tests": {k: run[k] for k in ("sha", "passed", "failed", "total")},
        "human_review": "Mỗi đợt đào tạo = 1 nhiệm vụ Văn Phòng: Evidence kind=test_report, url=/api/office/agents/"
                        f"{cfg['slug']}/test-runs/<sha> → Review độc lập (ReviewSI) → Closure. Không tự chuyển stage.",
    }
