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


def worker_ok(c: httpx.Client) -> dict:
    """Worker phải chạy thật: đã cấu hình, có heartbeat còn mới, không bị dừng."""
    w = expect(c.get("/api/worker/status"), 200)
    assert w.get("configured"), "worker chưa cấu hình (CFP_WORKER_DB / CFP_SANDBOX_EPHEMERAL)"
    assert w.get("alive"), f"không có heartbeat mới: {w.get('heartbeats')}"
    assert not w.get("paused"), "worker đang bị dừng (kill switch)"
    hb = w["heartbeats"][0]
    return {"worker_id": hb["worker_id"], "age_seconds": hb["age_seconds"], "ticks": hb["ticks"],
            "jobs": w.get("jobs"), "alerts_24h": w.get("alerts_24h"),
            "last_done": (w.get("last_done") or {}).get("summary")}


def run(base: str, allow_http: bool, public_only: bool = False, user_only: bool = False) -> dict:
    s = Smoke(base)
    gov_email, rev_email = os.environ.get("SMOKE_GOV_EMAIL"), os.environ.get("SMOKE_REVIEWER_EMAIL")
    pw = os.environ.get("SMOKE_PASSWORD")
    if not (public_only or user_only) and not (gov_email and rev_email and pw):
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
    s.check("platform", "URL dạng https:// (TLS được chứng minh khi /api/health trả lời)", https)

    def health():
        h = expect(guest.get("/api/health"), 200)
        x["build"], x["storage"] = h.get("build"), h.get("storage")
        assert h["status"] == "ok" and h.get("office"), "office chưa cấu hình"
        assert set(h["forums"]) == {"sieu-bo-doi", "si-ai-hstdn"}, h["forums"]
        return {"build": h.get("build"), "storage": h.get("storage"), "auth_db": h["auth_db"], "office_db": h["office"]["db"],
                "forums": {k: v["db"] for k, v in h["forums"].items()}, "registry": h["registry"]}
    if not s.check("platform", "/api/health", health):
        return finish(s, base, tag)  # server không trả lời/không sẵn sàng → dừng, không gọi tiếp cho hết giờ

    def website():
        out = {}
        for path in ("/", f"/{CID}/"):
            r = guest.get(path)
            assert r.status_code == 200 and 'data-testid="sandbox-entry"' in r.text, f"{path} → {r.status_code}"
            out[path] = 200
        assert f'href="/_internal/office/{CID}/"' in guest.get(f"/{CID}/").text, "thiếu lối vào Văn Phòng"
        return out
    s.check("platform", "website sandbox: lối vào Siêu Bộ Đôi / Văn Phòng", website)

    def ephemeral_label():
        if not str(x.get("storage", "")).startswith("ephemeral"):
            return "kho thật — không cần nhãn"
        for path in ("/_internal/forum/sieu-bo-doi/", "/_internal/forum/si-ai-hstdn/", "/_internal/office/691121/", "/"):
            r = guest.get(path)
            assert r.status_code == 200 and 'data-testid="ephemeral-banner"' in r.text, f"{path} thiếu cảnh báo dữ liệu thử nghiệm"
        return "4 trang có cảnh báo DỮ LIỆU THỬ NGHIỆM"
    s.check("platform", "chế độ tạm → mọi trang có cảnh báo dữ liệu thử nghiệm", ephemeral_label)

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

    def catalog():
        j = expect(guest.get("/api/catalog", params={"q": "8682"}), 200)
        assert j["total"] >= 150 and j["items"][0]["canonical_id"] == "8682", j["items"][:1]
        it = expect(guest.get("/api/catalog/691121"), 200)
        assert it["canonical_url"] == "https://cfp.plus/691121/" and it["parent_id"] == "69112", it
        r = guest.get("/api/catalog/99999999")
        assert r.status_code == 404, f"ID lạ → {r.status_code}"
        m = expect(guest.get("/api/catalog/meta"), 200)
        assert len(m["modules"]) == 10 and all(p["canonical_id"] is None for p in m["pending"])
        assert guest.get("/_internal/catalog/").status_code == 200
        return {"total": j["total"], "8682": j["items"][0]["version"], "691121_parent": it["parent_id"], "unknown_id": 404}
    s.check("catalog", "danh mục Link Mẫu: chỉ ID đã xuất bản, parent từ Registry, ID lạ 404", catalog)

    if public_only or user_only:
        s.check("worker", "worker chạy thật (heartbeat mới, không bị dừng)", lambda: worker_ok(guest))
    if user_only:
        user_flow(s, base, tag, guest)
    if public_only or user_only:
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

    # ---- 4b. Diễn Đàn SI AI • HSTDN (chỉ thành viên đã duyệt): xin tham gia → admin duyệt → mở thảo luận
    #      có trường HSTDN → reviewer phản hồi → khách bị chặn, bài không lọt sang Siêu Bộ Đôi
    HST = "si-ai-hstdn"

    def hstdn_discussion():
        assert expect(lead.post(f"/api/forums/{HST}/join", headers=H), 200, 201)["status"] == "pending"
        expect(lead.post(f"/api/office/tasks/{t}/discussions", headers=H, json={
            "forum": HST, "title": "chưa duyệt", "body": "x", "hstdn": "Anthropic PBC"}), 403)
        expect(gov.post(f"/api/forums/{HST}/members/{x['lead']}/approve", headers=H), 200)
        d = expect(lead.post(f"/api/office/tasks/{t}/discussions", headers=H, json={
            "forum": HST, "title": f"{prefix}HSTDN nhiệm vụ #{t}", "body": "Dữ liệu doanh nghiệp công khai (smoke).",
            "hstdn": "Anthropic PBC", "country_id": "911"}), 201)
        x["post_hstdn"] = d["post_id"]
        return {"forum": d["forum"], "post_id": d["post_id"], "trước khi duyệt": 403}
    hst_ok = s.check("forum", "HSTDN: xin tham gia → duyệt → mở thảo luận (trước duyệt 403)", hstdn_discussion)

    def hstdn_reply():
        j = rev.post(f"/api/forums/{HST}/join", headers=H)
        if j.status_code in (200, 201) and j.json().get("status") == "pending":
            expect(gov.post(f"/api/forums/{HST}/members/{x['rev']}/approve", headers=H), 200)
        expect(rev.post(f"/api/forums/{HST}/posts/{x['post_hstdn']}/comments", headers=H,
                        json={"body": "Reviewer phản hồi trong SI AI • HSTDN (smoke)."}), 201)
        posts = expect(rev.get(f"/api/forums/{HST}/posts"), 200)
        posts = posts.get("posts", posts) if isinstance(posts, dict) else posts
        p = next(p for p in posts if p["id"] == x["post_hstdn"])
        assert len(p["comments"]) >= 1 and p.get("hstdn") == "Anthropic PBC", p
        assert guest.get(f"/api/forums/{HST}/posts").status_code in (401, 403), "khách đọc được HSTDN"
        sbd = expect(guest.get(f"/api/forums/{FORUM}/posts"), 200)
        sbd = sbd.get("posts", sbd) if isinstance(sbd, dict) else sbd
        assert not any(q["title"] == f"{prefix}HSTDN nhiệm vụ #{t}" for q in sbd), "bài HSTDN lọt sang Siêu Bộ Đôi"
        links = expect(lead.get("/api/office/forum-links", params={"forum": HST}), 200)["links"]
        assert any(l["post_id"] == x["post_hstdn"] and l["task_id"] == t for l in links), links
        return "phản hồi OK • khách bị chặn • không lọt sang Siêu Bộ Đôi • liên kết nhiệm vụ OK"
    if hst_ok:
        s.check("forum", "HSTDN: phản hồi + cách ly hai Diễn Đàn", hstdn_reply)

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

    def closed_loop():
        les = expect(lead.post(f"/api/office/tasks/{t}/lessons", headers=H, json={
            "title": f"{prefix}Bài học smoke", "chapter": "6", "summary": "Bài học ghi sau nghiệm thu (smoke)."}), 201)
        nxt = expect(lead.post("/api/office/tasks", headers=H, json={
            "pair_id": x["pair"], "title": f"{prefix}Nhiệm vụ tiếp theo", "acceptance": "dựa trên bài học",
            "reviewer_id": x["rev"], "idempotency_key": f"smoke-{tag}-next", "refs": [f"task:{t}", les["ref"]]}), 201)["id"]
        loop = expect(gov.get(f"/api/office/tasks/{t}/loop"), 200)
        missing = [st_["key"] for st_ in loop["stages"] if not st_["done"]]
        assert loop["closed_loop"] and not missing, f"vòng chưa kín: {missing}"
        return {"stages": len(loop["stages"]), "lesson": les["ref"], "next_task": nxt}
    s.check("office", "vòng khép kín: bài học → nhiệm vụ tiếp theo → 12/12 bước", closed_loop)

    def audit():
        ev = expect(gov.get("/api/office/audit", params={"ref": f"task:{t}"}), 200)["events"]
        acts = [e["action"] for e in ev]
        need = ["task.create", "task.acked", "task.in_progress", "task.comment", "evidence.create",
                "task.in_review", "task.accepted", "task.closed"] + (["task.discussion"] if disc_ok else [])
        assert acts.count("task.discussion") == int(disc_ok) + int(hst_ok), acts  # một thảo luận mỗi Diễn Đàn
        missing = [a for a in need if a not in acts]
        assert not missing, f"thiếu {missing}; có {acts}"
        expect(guest.get("/api/office/audit", params={"ref": f"task:{t}"}), 401)
        return {"events": len(ev), "actions": acts}
    s.check("office", "audit đầy đủ + khách bị chặn", audit)

    # ---- 6. Worker (chỉ ghi nhận — không tuyên bố 24/24)
    worker_up = s.check("worker", "worker chạy thật (heartbeat mới, không bị dừng)", lambda: worker_ok(guest))

    def kill_switch():
        """Dừng an toàn có quan sát: giữ trạng thái dừng qua ≥1 nhịp worker, số việc không đổi trong lúc dừng,
        chạy lại → worker báo running ở nhịp mới. Luôn khôi phục trạng thái ban đầu (finally).
        (Xử lý đúng một lần sau khi chạy lại: tests/forum/test_forum_api.py::test_worker_kill_switch_http_governance_only.)"""
        assert worker_up, "worker không chạy → không kiểm được dừng an toàn"
        wait = float(os.environ.get("SMOKE_WORKER_WAIT", "120"))

        def st():
            return expect(guest.get("/api/worker/status"), 200)

        def until(pred, what):
            t_end = time.monotonic() + wait
            while time.monotonic() < t_end:
                w = st()
                if pred(w):
                    return w
                time.sleep(2)
            raise AssertionError(f"quá {int(wait)} s chưa thấy: {what}")

        expect(lead.post("/api/worker/control", json={"paused": True, "reason": "smoke"}, headers=H), 403)
        before = st()
        was_paused = before["paused"]
        jobs0, ticks0 = before["jobs"], before["heartbeats"][0]["ticks"]
        paused_set = False
        try:
            assert expect(gov.post("/api/worker/control", json={"paused": True, "reason": f"smoke {tag}: dừng an toàn"},
                                   headers=H), 200)["paused"] is True
            paused_set = True
            w = until(lambda w: w["heartbeats"][0]["state"] == "paused" and w["heartbeats"][0]["ticks"] > ticks0,
                      "worker ghi heartbeat 'paused' ở nhịp mới")
            t_pause = w["heartbeats"][0]["ticks"]
            w = until(lambda w: w["heartbeats"][0]["ticks"] > t_pause, "thêm một nhịp khi đang dừng")
            assert w["heartbeats"][0]["state"] == "paused", w["heartbeats"][0]
            assert w["jobs"] == jobs0, f"số việc đổi trong lúc dừng: {jobs0} → {w['jobs']}"
            held = w["heartbeats"][0]["ticks"] - ticks0
        finally:
            if paused_set and not was_paused:
                gov.post("/api/worker/control", json={"paused": False, "reason": f"smoke {tag}: chạy lại"}, headers=H)
        w = until(lambda w: not w["paused"] and w["heartbeats"][0]["state"] == "running", "worker chạy lại")
        return {"held_ticks": held, "jobs_during_pause": jobs0, "after_resume": w["heartbeats"][0]["state"],
                "kill_switch_events": sum(1 for r in w.get("recent", []) if r["event"] == "kill_switch")}
    s.check("worker", "kill switch: dừng giữ qua ≥2 nhịp, số việc không đổi, chạy lại (governance)", kill_switch)
    return finish(s, base, tag)


def user_flow(s: Smoke, base: str, tag: str, guest: httpx.Client) -> None:
    """Có đăng nhập, KHÔNG cần secrets: tài khoản thử nghiệm mới (example.org, dữ liệu sandbox tạm).
    Chứng minh đăng ký/đăng nhập/phiên, ghi+đọc Diễn Đàn, và các ranh giới quyền (403/401) trên HTTPS thật.
    Luồng giao việc → ACK → Evidence → Review → Closure cần governance/reviewer → vẫn cần SMOKE_* (không giả lập)."""
    u = s.client()
    x = s.ctx
    title = f"[smoke-{tag}] Bài thử nghiệm sandbox"

    def account():
        r = u.post("/api/auth/register", headers=H, json={
            "email": f"smoke-{tag}-user@example.org", "password": f"smoke-{tag}-pw-u", "name": f"Smoke User {tag}"})
        x["user"] = expect(r, 200, 201)["id"]
        cookie = r.headers.get("set-cookie", "").lower()
        flags = {f: f in cookie for f in ("httponly", "samesite=strict", "secure")}
        assert flags["httponly"] and flags["samesite=strict"], flags
        if base.startswith("https://"):
            assert flags["secure"], "cookie thiếu Secure trên HTTPS"
        assert (expect(u.get("/api/auth/me"), 200).get("user") or {}).get("id") == x["user"], "phiên không được giữ"
        return {"user_id": x["user"], "cookie": flags}
    if not s.check("auth", "đăng ký tài khoản thử nghiệm → phiên đăng nhập (cookie)", account):
        return

    def sbd():
        expect(u.post(f"/api/forums/{FORUM}/join", headers=H), 200, 201)
        pid = expect(u.post(f"/api/forums/{FORUM}/posts", headers=H, json={"title": title, "body": "Ghi thật qua HTTPS."}), 201)["id"]
        expect(u.post(f"/api/forums/{FORUM}/posts/{pid}/comments", headers=H, json={"body": "Bình luận thử nghiệm."}), 201)
        posts = expect(guest.get(f"/api/forums/{FORUM}/posts"), 200)
        posts = posts.get("posts", posts) if isinstance(posts, dict) else posts
        p = next(p for p in posts if p["id"] == pid)
        assert p["title"] == title and len(p["comments"]) >= 1, p
        return {"post_id": pid, "comments": len(p["comments"]), "đọc lại bởi khách": True}
    s.check("forum", "Siêu Bộ Đôi: tham gia → đăng bài → bình luận → khách đọc lại", sbd)

    def hstdn():
        st_ = expect(u.post("/api/forums/si-ai-hstdn/join", headers=H), 200, 201)["status"]
        assert st_ == "pending", st_
        r = u.post("/api/forums/si-ai-hstdn/posts", headers=H, json={"title": "x", "body": "x", "hstdn": "x"})
        assert r.status_code == 403, f"chưa duyệt mà đăng được: {r.status_code}"
        assert u.get("/api/forums/si-ai-hstdn/posts").status_code == 403
        return {"join": st_, "đăng khi chưa duyệt": 403, "đọc khi chưa duyệt": 403}
    s.check("forum", "SI AI • HSTDN: xin tham gia = pending; chưa duyệt không đọc/đăng được", hstdn)

    def least_privilege():
        expect(u.post("/api/office/tasks", headers=H, json={
            "pair_id": 1, "title": "không được giao", "acceptance": "abc", "reviewer_id": 1,
            "idempotency_key": f"smoke-{tag}-deny"}), 403, 404, 422)
        b = expect(u.get("/api/office/board"), 200)
        assert b["viewer"] == "participant" and b["tasks"] == [], b
        expect(u.post("/api/worker/control", headers=H, json={"paused": True, "reason": "smoke"}), 403)
        expect(u.post(f"/api/forums/{FORUM}/members/{x['user']}/approve", headers=H), 403)
        return "giao việc bị chặn • board rỗng • kill switch 403 • tự duyệt 403"
    s.check("security", "người thường: không giao việc, không thấy nhiệm vụ, không kill switch", least_privilege)

    def answer_guard():
        """Siêu Phần Mềm giám sát tư vấn: bản nháp sai bị chặn, không bao giờ tự gửi (AUTO REPLY HOLD)."""
        bad = expect(u.post("/api/office/answer-check", headers=H, json={
            "agent": "smoke", "draft": "App CFP+ đã hoạt động. Gửi mật khẩu để đăng ký. https://cfp.plus/69115/"}), 200)
        codes = {f["code"] for f in bad["findings"]}
        assert bad["verdict"] == "block" and bad["auto_reply"] == "HOLD", bad
        assert {"claim_unverified", "sensitive_request", "hold_id"} <= codes, codes
        good = expect(u.post("/api/office/answer-check", headers=H, json={
            "agent": "smoke", "draft": "CFP+ tổ chức theo 5 Nhóm, 10 Chương. Xem https://cfp.plus/69/"}), 200)
        assert good["verdict"] == "ready_for_human_review" and good["auto_reply"] == "HOLD", good
        return {"sai": sorted(codes), "đúng": good["verdict"], "auto_reply": "HOLD"}
    s.check("agent", "giám sát câu trả lời tư vấn: chặn ID HOLD/tuyên bố chưa kiểm chứng/hỏi mật khẩu • AUTO REPLY HOLD",
            answer_guard)

    def logout():
        expect(u.post("/api/auth/logout", headers=H), 200)
        assert (expect(u.get("/api/auth/me"), 200).get("user")) is None
        r = u.post(f"/api/forums/{FORUM}/posts", headers=H, json={"title": "x", "body": "x"})
        assert r.status_code == 401, r.status_code
        return "đăng xuất → me=null → ghi 401"
    s.check("auth", "đăng xuất → phiên hết → ghi bị 401", logout)


def finish(s: Smoke, base: str, tag: str) -> dict:
    gating = s.results  # worker + kill switch cũng là điều kiện P0
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
    ap.add_argument("--user-only", action="store_true",
                    help="public + tài khoản thử nghiệm tự đăng ký (không cần secrets; chưa gồm giao việc/review)")
    a = ap.parse_args()
    rep = run(a.base, a.allow_http, a.public_only, a.user_only)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(f"SMOKE_LIVE={rep['result']} passed={rep['passed']} failed={rep['failed']} build={rep['build']}")
    sys.exit(0 if rep["result"] == "PASS" else 1)
