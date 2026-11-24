#!/usr/bin/env python3
"""CFP+ • Bộ kiểm thử kết nối MCP + OAuth (chỉ đọc, không cần secret).

Kiểm tra theo thứ tự: endpoint MCP • 401 + WWW-Authenticate • Protected Resource Metadata
(RFC 9728) • Authorization Server Metadata (RFC 8414 / OIDC) • PKCE S256 • DCR (tuỳ chọn)
• MCP Streamable HTTP initialize (khi có Bearer token qua biến môi trường MCP_TOKEN).
Dùng lại cho mọi nền tảng: python3 probe.py --platform gemini
"""
import argparse, json, os, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def http(method, url, body=None, headers=None, timeout=20):
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(4096).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(4096).decode("utf-8", "replace")
    except Exception as e:  # mạng, DNS, TLS
        return 0, {}, f"{type(e).__name__}: {e}"


def jget(url):
    code, h, b = http("GET", url, headers={"Accept": "application/json"})
    try:
        return code, json.loads(b)
    except ValueError:
        return code, None


def run(mcp_url, platform):
    res, add = [], (lambda k, ok, d: res.append({"check": k, "result": "PASS" if ok else "FAIL", "detail": d}))
    u = urllib.parse.urlsplit(mcp_url)
    origin, path = f"{u.scheme}://{u.netloc}", u.path.rstrip("/")

    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "cfp-probe", "version": "1"}}}).encode()
    hdr = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    code, h, body = http("POST", mcp_url, init, hdr)
    hl = {k.lower(): v for k, v in h.items()}
    add("endpoint_reachable", code not in (0, 404, 502, 503), f"POST {mcp_url} → {code} {body[:160]}")
    www = hl.get("www-authenticate", "")
    add("unauth_401_www_authenticate", code == 401 and "resource_metadata" in www, f"{code} WWW-Authenticate={www[:200]!r}")

    prm_urls = [f"{origin}/.well-known/oauth-protected-resource{path}", f"{origin}/.well-known/oauth-protected-resource"]
    if "resource_metadata=" in www:
        prm_urls.insert(0, www.split("resource_metadata=")[1].split(",")[0].strip().strip('"'))
    prm = None
    for p in prm_urls:
        c, j = jget(p)
        if c == 200 and j and j.get("authorization_servers"):
            prm = j; break
    add("protected_resource_metadata", bool(prm), json.dumps(prm)[:300] if prm else f"không có tại {prm_urls}")

    issuer = (prm or {}).get("authorization_servers", [origin])[0].rstrip("/")
    iu = urllib.parse.urlsplit(issuer); ip = iu.path.rstrip("/")
    asm = None
    for p in [f"{iu.scheme}://{iu.netloc}/.well-known/oauth-authorization-server{ip}",
              f"{iu.scheme}://{iu.netloc}/.well-known/openid-configuration{ip}", f"{issuer}/.well-known/openid-configuration"]:
        c, j = jget(p)
        if c == 200 and j and j.get("token_endpoint"):
            asm = j; break
    add("authorization_server_metadata", bool(asm), (asm or {}).get("issuer") or f"không có cho issuer {issuer}")
    add("pkce_s256", "S256" in (asm or {}).get("code_challenge_methods_supported", []), str((asm or {}).get("code_challenge_methods_supported")))
    add("authorization_and_token_endpoints", bool(asm and asm.get("authorization_endpoint") and asm.get("token_endpoint")),
        f"{(asm or {}).get('authorization_endpoint')} • {(asm or {}).get('token_endpoint')}")
    res.append({"check": "dynamic_client_registration", "result": "INFO",
                "detail": (asm or {}).get("registration_endpoint") or "không công bố (Gemini dùng Client ID/Secret đăng ký sẵn)"})

    tok = os.environ.get("MCP_TOKEN")
    if tok:
        c, h2, b2 = http("POST", mcp_url, init, {**hdr, "Authorization": f"Bearer {tok}"})
        add("streamable_http_initialize", c == 200 and ("protocolVersion" in b2), f"{c} {b2[:200]}")
    else:
        res.append({"check": "streamable_http_initialize", "result": "NOT RUN", "detail": "cần token thật (MCP_TOKEN) sau Token Exchange"})
    res.append({"check": "token_exchange", "result": "NOT RUN", "detail": "cần đăng nhập người dùng trên nền tảng (Human)"})

    if platform:
        cfg = json.loads((HERE / "platforms.json").read_text("utf-8"))
        pf = next(x for x in cfg["platforms"] if x["key"] == platform)
        add(f"{platform}_client_registered", bool(pf.get("client_id")), pf.get("client_id_status"))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=json.loads((HERE / "platforms.json").read_text("utf-8"))["mcp_server_url"])
    ap.add_argument("--platform")
    a = ap.parse_args(argv)
    res = run(a.url, a.platform)
    print(json.dumps({"url": a.url, "platform": a.platform, "results": res}, ensure_ascii=False, indent=2))
    return 0 if all(r["result"] != "FAIL" for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
