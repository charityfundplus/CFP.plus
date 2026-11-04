"""Smoke test cho một server sandbox ĐANG CHẠY (Render/HTTPS hoặc local), chỉ qua HTTP API.

Mỗi lần chạy tạo dữ liệu mới gắn tiền tố [smoke-<ts>] (không xoá, không sửa dữ liệu hiện hữu,
không cấp ID mới: dùng ID 691121 đã có trong Registry). Kết quả ghi ra tệp JSON làm Evidence.

Luồng: bảo mật cơ bản → Đăng nhập → Giao nhiệm vụ → ACK → Start → mở thảo luận ở Diễn Đàn
Siêu Bộ Đôi → phản hồi trên diễn đàn → trao đổi nhiệm vụ → Evidence → Submit → Independent
Review → Closure → audit; kèm trạng thái worker (chỉ ghi nhận, không tính PASS/FAIL).

Tài khoản governance và reviewer phải được cấp vai trò TRƯỚC (một lần, bằng CLI quản trị có
kết nối DB sandbox):
  python -m services.forum.admin grant-office-role governance <email>
  python -m services.forum.admin grant-office-role reviewer <email>
Tài khoản người thực thi được đăng ký mới mỗi lần chạy.

Biến môi trường (không ghi vào mã, không in ra):
  SMOKE_GOV_EMAIL, SMOKE_REVIEWER_EMAIL, SMOKE_PASSWORD
Chạy:
  python -m tests.forum.smoke_live --base https://<sandbox>.onrender.com --out smoke.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import httpx

H = {"X-CFP-Forum": "1"}
CID = "691121"  # Claude • Registry: 911 → 6911 → 69112 → 691121 (ID có sẵn)
FORUM = "sieu-bo-doi"


class RespectRateLimit(httpx.HTTPTransport):
    """Gặp 429 thì chờ đúng Retry-After của server rồi gửi lại (tối đa 2 lần). Không nới giới hạn server."""
    throttled = 0

    def handle_request(self, request):
        for _ in range(3):
            r = super().handle_request(request)
            if r.status_code != 429:
                return r
            wait = min(int(r.headers.get("retry-after", "5")), 65)
            RespectRateLimit.throttled += 1
            r.close()
            time.sleep(wait)
        return r


class Smoke:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.results: list[dict] = []
        self.ctx: dict = {}

    def client(self) -> httpx.Client:
        # Origin đúng server (backend kiểm tra Origin cho request ghi)
        return httpx.Client(base_url=self.base, timeout=30, headers={"Origin": self.base}, follow_redirects=False,
                            transport=RespectRateLimit())

    def check(self, group: str, step: str, fn):
        t0 = time.monotonic()
        rec = {"group": group, "step": step}
        try:
            detail = fn()
            rec.update(ok=True, detail=detail)
        except Exception as e:  # ghi lại, không dừng nhóm khác
            rec.update(ok=False, detail=f"{type(e).__name__}: {e}"[:500])
        rec["ms"] = int((time.monotonic() - t0) * 1000)
        self.results.append(rec)
        print(f"[{'PASS' if rec['ok'] else 'FAIL'}] {group} • {step} — {rec['detail']}", flush=True)
        return rec["ok"]


def expect(r: httpx.Response, *codes: int):
    if r.status_code not in codes:
        raise AssertionError(f"{r.request.method} {r.request.url.path} → {r.status_code} (cần {codes}) {r.text[:200]}")
    try:
        return r.json()
    except ValueError:
        return {}


def login(c: httpx.Client, email: str, pw: str) -> dict:
    return expect(c.post("/api/auth/login", json={"email": email, "password": pw}, headers=H), 200)


def run(base: str, allow_http: bool, public_only: bool = False) -> dict:
    s = Smoke(base)
    gov_email, rev_email = os.environ.get("SMOKE_GOV_EMAIL"), os.environ.get("SMOKE_REVIEWER_EMAIL")
    pw = os.environ.get("SMOKE_PASSWORD")
    if not public_only and not (gov_email and rev_email and pw):
        sys.exit("Thiếu SMOKE_GOV_EMAIL / SMOKE_REVIEWER_EMAIL / SMOKE_PASSWORD (hoặc dùng --public-only)")
    tag = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    prefix = f"[smoke-{tag}] "
    guest, gov, lead, rev = s.client(), s.client(), s.client(), s.client()
    x = s.ctx

    # ---- 1. Nền tảng + bảo mật cơ bản
    def https():
        if not base.startswith("https://") and not allow_http:
            raise AssertionError("URL không phải HTTPS")
        return base.split("://")[0]
    s.check("platform", "HTTPS", https)

    def health():
        h = expect(guest.get("/api/health"), 200)
        x["build"], x["storage"] = h.get("build"), h.get("storage")
        assert h["status"] == "ok" and h.get("office"), "office chưa cấu hình"
        assert set(h["forums"]) == {"sieu-bo-doi", "si-ai-hstdn"}, h["forums"]
        return {"build": h.get("build"), "storage": h.get("storage"), "auth_db": h["auth_db"], "office_db": h["office"]["db"],
                "forums": {k: v["db"] for k, v in h["forums"].items()}, "registry": h["registry"]}
    s.check("platform", "/api/health", health)

    def website():
        out = {}
        for path in ("/", f"/{CID}/"):
            r = guest.get(path)
            assert r.status_code == 200 and 'data-testid="sandbox-entry"' in r.text, f"{path} → {r.status_code}"
            out[path] = 200
        assert f'href="/_internal/office/{CID}/"' in guest.get(f"/{CID}/").text, "thiếu lối vào Văn Phòng"
        return out
    s.check("platform", "website sandbox: lối vào Siêu Bộ Đôi / Văn Phòng", website)

    def csrf():
        r = guest.post("/api/auth/login", json={"email": "x@example.org", "password": "x" * 10})
        assert r.status_code == 403, f"thiếu header CSRF → {r.status_code}"
        r = guest.post("/api/auth/login", json={"email": "x@example.org", "password": "x" * 10},
                       headers={**H, "Origin": "https://evil.example"})
        assert r.status_code == 403, f"Origin lạ → {r.status_code}"
        return "thiếu header → 403; Origin lạ → 403"
    s.check("security", "CSRF header + Origin", csrf)

    def guest_denied():
        expect(guest.post("/api/office/tasks", json={}, headers=H), 401)
        expect(guest.get("/api/office/audit", params={"ref": "task:1"}), 401)
        expect(guest.post(f"/api/forums/{FORUM}/posts", json={"title": "x", "body": "x"}, headers=H), 401)
        return "ghi nhiệm vụ / audit / đăng bài khi chưa đăng nhập → 401"
    s.check("security", "khách không ghi được", guest_denied)

    def forums_isolated():
        out = {}
        for key in ("sieu-bo-doi", "si-ai-hstdn"):
            info = expect(guest.get(f"/api/forums/{key}"), 200)
            r = guest.get(f"/_internal/forum/{key}/")
            assert r.status_code == 200, f"/_internal/forum/{key}/ → {r.status_code}"
            posts = guest.get(f"/api/forums/{key}/posts")
            out[key] = {"page": 200, "posts_guest": posts.status_code, "title": info.get("title"), "public_read": info.get("public_read")}
        # SI AI • HSTDN chỉ cho thành viên đã duyệt; Siêu Bộ Đôi công khai
        assert out["sieu-bo-doi"]["posts_guest"] == 200 and out["si-ai-hstdn"]["posts_guest"] in (401, 403), out
        return out
    s.check("forum", "hai Diễn Đàn: trang + API riêng, HSTDN chặn khách", forums_isolated)

    if public_only:
        s.check("worker", "trạng thái (thông tin)", lambda: expect(guest.get("/api/worker/status"), 200))
        return finish(s, base, tag)

    # ---- 2. Đăng nhập
    def accounts():
        x["gov"] = login(gov, gov_email, pw)["id"]
        x["rev"] = login(rev, rev_email, pw)["id"]
        r = lead.post("/api/auth/register", headers=H, json={
            "email": f"smoke-{tag}-lead@example.org", "password": f"smoke-{tag}-pw", "name": f"Smoke Lead {tag}"})
        x["lead"] = expect(r, 200, 201)["id"]
        cookie = r.headers.get("set-cookie", "").lower()
        flags = {f: f in cookie for f in ("httponly", "samesite=strict", "secure")}
        assert flags["httponly"] and flags["samesite=strict"], flags
        if base.startswith("https://"):
            assert flags["secure"], "cookie thiếu Secure trên HTTPS"
        me = expect(lead.get("/api/auth/me"), 200)
        assert (me.get("user") or {}).get("id") == x["lead"], "phiên đăng nhập không được giữ (cookie)"
        return {"cookie": flags}
    if not s.check("auth", "đăng nhập gov/reviewer + đăng ký người thực thi", accounts):
        return finish(s, base, tag)

    # ---- 3. Văn Phòng: giao nhiệm vụ → ACK → Start
    def assign():
        tax = expect(gov.get("/api/office/taxonomy"), 200)
        assert [g["code"] for g in tax["groups"]] == ["DV", "000", "135", "246", "789"]
        assert len(tax["chapters"]) == 10
        chain = [e["id"] for e in expect(gov.get(f"/api/office/registry/{CID}"), 200)["chain"]]
        assert chain == ["911", "6911", "69112", CID], chain
        expect(gov.post("/api/office/offices", headers=H, json={
            "canonical_id": CID, "platform": "Anthropic", "specialties": "Backend, API, kiểm thử",
            "capabilities": "Làm việc trong sandbox", "limits": "Không deploy production"}), 201, 409)
        expect(gov.post(f"/api/office/offices/{CID}/maintainers/{x['lead']}", headers=H), 200, 201, 409)
        x["pair"] = expect(lead.post("/api/office/pairs", headers=H, json={
            "canonical_id": CID, "software": f"{prefix}Claude Code", "lead_user_id": x["lead"]}), 201)["id"]
        x["task"] = expect(lead.post("/api/office/tasks", headers=H, json={
            "pair_id": x["pair"], "title": f"{prefix}Smoke Link Mẫu Chung",
            "acceptance": "Luồng nhiệm vụ ↔ diễn đàn ↔ Evidence ↔ Review chạy trên URL sandbox",
            "reviewer_id": x["rev"], "idempotency_key": f"smoke-{tag}", "refs": [f"registry:{CID}"]}), 201)["id"]
        return {"registry_chain": chain, "task": x["task"]}
    if not s.check("office", "giao nhiệm vụ (ID 691121 có sẵn)", assign):
        return finish(s, base, tag)
    t = x["task"]
    s.check("office", "ACK", lambda: expect(lead.post(f"/api/office/tasks/{t}/ack", json={"note": "ACK"}, headers=H), 200)["status"])
    s.check("office", "Start", lambda: expect(lead.post(f"/api/office/tasks/{t}/start", json={}, headers=H), 200)["status"])

    # ---- 4. Diễn Đàn: mở thảo luận → phản hồi → quay lại nhiệm vụ
    def discussion():
        expect(lead.post(f"/api/forums/{FORUM}/join", headers=H), 200, 201, 409)
        d = expect(lead.post(f"/api/office/tasks/{t}/discussions", headers=H, json={
            "forum": FORUM, "title": f"{prefix}Thảo luận nhiệm vụ #{t}", "body": "Mở từ Văn Phòng (smoke)."}), 201)
        x["post"] = d["post_id"]
        return {"forum": d["forum"], "post_id": d["post_id"]}
    disc_ok = s.check("forum", f"mở thảo luận ở {FORUM}", discussion)

    def reply():
        expect(rev.post(f"/api/forums/{FORUM}/join", headers=H), 200, 201, 409)
        expect(rev.post(f"/api/forums/{FORUM}/posts/{x['post']}/comments", headers=H,
                        json={"body": "Reviewer phản hồi trên diễn đàn (smoke)."}), 201)
        posts = expect(guest.get(f"/api/forums/{FORUM}/posts"), 200)
        posts = posts.get("posts", posts) if isinstance(posts, dict) else posts
        p = next(p for p in posts if p["id"] == x["post"])
        assert len(p["comments"]) >= 1
        return {"comments": len(p["comments"])}
    if disc_ok:
        s.check("forum", "phản hồi trên diễn đàn (khách đọc được ở Siêu Bộ Đôi)", reply)

        def backlinks():
            mine = expect(lead.get("/api/office/forum-links", params={"forum": FORUM}), 200)["links"]
            assert any(l["post_id"] == x["post"] and l["task_id"] == t for l in mine), mine
            other = expect(guest.get("/api/office/forum-links", params={"forum": FORUM}), 200)["links"]
            assert not any(l["task_id"] == t for l in other), "khách thấy liên kết nhiệm vụ nội bộ"
            return "người tham gia thấy liên kết bài ↔ nhiệm vụ; khách không thấy"
        s.check("forum", "liên kết hai chiều + ẩn với khách", backlinks)

    s.check("office", "trao đổi nhiệm vụ", lambda: expect(lead.post(
        f"/api/office/tasks/{t}/comments", json={"body": "Đã đọc phản hồi diễn đàn, tiếp tục."}, headers=H), 201) and "201")

    # ---- 5. Evidence → Submit → Independent Review → Closure
    s.check("office", "Evidence", lambda: expect(lead.post(f"/api/office/tasks/{t}/evidence", headers=H, json={
        "kind": "url", "description": "Smoke: health của sandbox (hoặc PR khi chạy local)", "url": f"{base}/api/health"
        if base.startswith("https://") else "https://github.com/charityfundplus/CFP.plus/pull/195"}), 201)["id"])
    s.check("office", "Submit", lambda: expect(lead.post(f"/api/office/tasks/{t}/submit", json={"note": "Gửi review"}, headers=H), 200)["status"])

    def review():
        expect(lead.post(f"/api/office/tasks/{t}/review", json={"decision": "ACCEPT", "notes": "tự duyệt"}, headers=H), 403)
        expect(rev.post(f"/api/office/tasks/{t}/review", json={"decision": "ACCEPT", "notes": "Đạt (smoke)."}, headers=H), 201)
        return "tự duyệt → 403; reviewer độc lập → ACCEPT"
    s.check("office", "Independent Review", review)

    def closure():
        expect(lead.post(f"/api/office/tasks/{t}/close", json={"note": "tự đóng"}, headers=H), 403)
        return expect(gov.post(f"/api/office/tasks/{t}/close", json={"note": "Đóng sau review (smoke)."}, headers=H), 200)["status"]
    s.check("office", "Closure (người thực thi tự đóng → 403)", closure)

    def audit():
        ev = expect(gov.get("/api/office/audit", params={"ref": f"task:{t}"}), 200)["events"]
        acts = [e["action"] for e in ev]
        need = ["task.create", "task.acked", "task.in_progress", "task.comment", "evidence.create",
                "task.in_review", "task.accepted", "task.closed"] + (["task.discussion"] if disc_ok else [])
        missing = [a for a in need if a not in acts]
        assert not missing, f"thiếu {missing}; có {acts}"
        expect(guest.get("/api/office/audit", params={"ref": f"task:{t}"}), 401)
        return {"events": len(ev), "actions": acts}
    s.check("office", "audit đầy đủ + khách bị chặn", audit)

    # ---- 6. Worker (chỉ ghi nhận — không tuyên bố 24/24)
    def worker():
        return expect(guest.get("/api/worker/status"), 200)
    s.check("worker", "trạng thái (thông tin)", worker)
    return finish(s, base, tag)


def finish(s: Smoke, base: str, tag: str) -> dict:
    gating = [r for r in s.results if r["group"] != "worker"]
    return {"base": base, "run": tag, "at": datetime.now(timezone.utc).isoformat(),
            "build": s.ctx.get("build"), "storage": s.ctx.get("storage"), "task_id": s.ctx.get("task"), "post_id": s.ctx.get("post"),
            "passed": sum(r["ok"] for r in gating), "failed": sum(not r["ok"] for r in gating),
            "result": "PASS" if gating and all(r["ok"] for r in gating) else "FAIL",
            "rate_limited_retries": RespectRateLimit.throttled, "mode": "SANDBOX PRACTICE • PRODUCTION NO GO", "checks": s.results}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", default="smoke-live.json")
    ap.add_argument("--allow-http", action="store_true", help="chỉ cho server local")
    ap.add_argument("--public-only", action="store_true", help="chỉ kiểm tra không cần tài khoản (không ghi dữ liệu)")
    a = ap.parse_args()
    rep = run(a.base, a.allow_http, a.public_only)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(f"SMOKE_LIVE={rep['result']} passed={rep['passed']} failed={rep['failed']} build={rep['build']}")
    sys.exit(0 if rep["result"] == "PASS" else 1)
