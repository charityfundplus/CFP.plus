"""Luồng xuyên suốt Link Mẫu SI AI trên sandbox, dùng chung cho pytest và cho server thật.

5 Nhóm → 10 Chương → Quốc gia → Nhà phát triển → SI AI → Thương hiệu/sản phẩm/dịch vụ → HSTDN
→ Chủ đề nghiên cứu → Kho dữ liệu → Văn Phòng Siêu Bộ Đôi → Nhiệm vụ → Evidence → Review.

Dữ liệu mẫu chỉ dùng ID đã có trong Registry (911 → 6911 → 69112 → 691121) và URL công khai
có thể kiểm chứng. Mọi mục thương hiệu gắn nhãn CFP_PUBLIC_SOURCE (không phải quảng bá được ủy quyền).

Chạy với server thật (cần đã cấp vai trò qua CLI, xem run_live()):
  python -m tests.forum.office_flow --base http://127.0.0.1:8000 --prefix demo1
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

H = {"X-CFP-Forum": "1"}
PW = "matkhau-office-p0"
CID = "691121"  # Claude • Registry: 911 → 6911 → 69112 → 691121

SAMPLE = {
    "office": {"canonical_id": CID, "platform": "Anthropic",
               "specialties": "Lập trình backend, API, migration, kiểm thử, review bảo mật",
               "capabilities": "Đọc/viết mã trong repo được cấp quyền; chạy test trong sandbox",
               "limits": "Không deploy production, không cấp ID, không thay đổi secrets/DNS/IAM"},
    "brand": [
        {"kind": "product", "name": "Claude", "url": "https://www.anthropic.com/claude",
         "source_url": "https://www.anthropic.com/claude", "description": "Trợ lý AI của Anthropic."},
        {"kind": "api", "name": "Claude API", "url": "https://docs.anthropic.com/",
         "source_url": "https://docs.anthropic.com/", "description": "Tài liệu API chính thức."},
        {"kind": "software", "name": "Claude Code", "url": "https://www.anthropic.com/claude-code",
         "source_url": "https://www.anthropic.com/claude-code", "description": "Công cụ lập trình agentic."},
    ],
    "enterprise": {"name": "Anthropic PBC", "country_id": "911", "chapter": "7",
                   "official_url": "https://www.anthropic.com/", "source_url": "https://www.anthropic.com/company",
                   "products": "Claude, Claude API, Claude Code",
                   "needs": "Nghiên cứu HSTDN Hoa Kỳ: chưa có thỏa thuận hợp tác/giao thương với CFP+."},
    "topic": {"title": "Phối hợp SI AI và Siêu Phần Mềm trong Văn Phòng Siêu Bộ Đôi", "chapter": "6",
              "field": "AI • Kỹ thuật phần mềm", "summary": "Quy trình nhận việc → ACK → thực thi → Evidence → Review."},
    "dataset": {"title": "CFP+ AI Entity Registry (JSON)", "kind": "dataset",
                "url": "https://github.com/charityfundplus/CFP.plus/blob/main/registry/ai-entity-registry.json",
                "author": "CFP+ Registry", "version": "8356163",
                "source_url": "https://github.com/charityfundplus/CFP.plus/tree/main/registry",
                "access": "public", "chapter": "6"},
}


def register(c, email, name):
    r = c.post("/api/auth/register", json={"email": email, "password": PW, "name": name}, headers=H)
    if r.status_code == 409:
        r = c.post("/api/auth/login", json={"email": email, "password": PW}, headers=H)
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def ok(r, *codes):
    assert r.status_code in codes, f"{r.request.method} {r.request.url} → {r.status_code} {r.text}"
    return r.json()


def run_flow(gov, lead, reviewer, lead_id: int, reviewer_id: int, prefix: str = "") -> dict:
    """gov/lead/reviewer: client đã đăng nhập (TestClient hoặc httpx.Client). Trả về các id đã tạo."""
    out = {}
    tax = ok(gov.get("/api/office/taxonomy"), 200)
    assert [g["code"] for g in tax["groups"]] == ["DV", "000", "135", "246", "789"]
    assert {c["key"] for c in tax["connections"]} >= {"hub69", "cmp267", "tmtc", "forum-sieu-bo-doi", "forum-si-ai-hstdn"}
    assert len(tax["chapters"]) == 10
    chain = ok(gov.get(f"/api/office/registry/{CID}"), 200)["chain"]
    assert [x["id"] for x in chain] == ["911", "6911", "69112", CID]

    r = gov.post("/api/office/offices", json=SAMPLE["office"], headers=H)
    assert r.status_code in (201, 409), r.text
    gov.post(f"/api/office/offices/{CID}/maintainers/{lead_id}", headers=H)
    for b in SAMPLE["brand"]:
        b = {**b, "name": f"{prefix}{b['name']}" if prefix else b["name"]}
        r = gov.post(f"/api/office/offices/{CID}/brand", json=b, headers=H)
        assert r.status_code in (201, 409), r.text

    ent = {**SAMPLE["enterprise"], "name": f"{prefix}{SAMPLE['enterprise']['name']}"}
    out["enterprise"] = ok(lead.post("/api/office/enterprises", json=ent, headers=H), 201)["id"]
    top = {**SAMPLE["topic"], "title": f"{prefix}{SAMPLE['topic']['title']}"}
    out["topic"] = ok(lead.post("/api/office/topics", json=top, headers=H), 201)["id"]
    ds = {**SAMPLE["dataset"], "version": f"{SAMPLE['dataset']['version']}{prefix}", "topic_id": out["topic"]}
    out["dataset"] = ok(lead.post("/api/office/datasets", json=ds, headers=H), 201)["id"]
    out["pair"] = ok(lead.post("/api/office/pairs", json={"canonical_id": CID, "software": f"{prefix}Claude Code",
                                                          "lead_user_id": lead_id}, headers=H), 201)["id"]
    task = {"pair_id": out["pair"], "title": f"{prefix}Luồng Link Mẫu SI AI xuyên suốt",
            "acceptance": "API + migration + test PASS; dữ liệu còn sau restart", "reviewer_id": reviewer_id,
            "idempotency_key": f"office-flow-{re.sub(r'[^A-Za-z0-9]', '', prefix) or 'base'}-{lead_id}",
            "refs": [f"enterprise:{out['enterprise']}", f"topic:{out['topic']}", f"dataset:{out['dataset']}",
                     f"registry:{CID}"]}
    out["task"] = ok(lead.post("/api/office/tasks", json=task, headers=H), 201)["id"]
    t = out["task"]
    ok(lead.post(f"/api/office/tasks/{t}/ack", json={"note": "ACK"}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H), 200)
    ok(lead.post(f"/api/office/tasks/{t}/evidence", json={
        "kind": "commit", "url": "https://github.com/charityfundplus/CFP.plus/commit/553e7a7",
        "sha": "553e7a7", "description": "Backend diễn đàn đã gia cố (nền tảng tái sử dụng)."}, headers=H), 201)
    ok(lead.post(f"/api/office/tasks/{t}/submit", json={"note": "Gửi review"}, headers=H), 200)
    ok(reviewer.post(f"/api/office/tasks/{t}/review", json={"decision": "ACCEPT", "notes": "Đạt tiêu chí."},
                     headers=H), 201)
    return out


def run_live(base: str, prefix: str) -> None:  # pragma: no cover - dùng với server thật
    import httpx
    env = os.environ.copy()
    clients = {}
    for who in ("gov", "lead", "reviewer"):
        c = httpx.Client(base_url=base, timeout=30)
        uid = register(c, f"{prefix}-{who}@example.org", f"{who.title()} {prefix}")
        clients[who] = (c, uid)
    for who, role in (("gov", "governance"), ("reviewer", "reviewer")):
        subprocess.run([sys.executable, "-m", "services.forum.admin", "grant-office-role", role,
                        f"{prefix}-{who}@example.org"], check=True, env=env)
    out = run_flow(clients["gov"][0], clients["lead"][0], clients["reviewer"][0],
                   clients["lead"][1], clients["reviewer"][1], prefix=f"[{prefix}] ")
    print(json.dumps(out))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--prefix", required=True)
    a = ap.parse_args()
    run_live(a.base, a.prefix)
