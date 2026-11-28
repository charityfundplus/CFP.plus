"""Danh tính theo quyền thực tế: mỗi AI một bearer token, một danh sách ID được đại diện.

Định dạng `SQZ_CLIENTS_JSON` tương thích `CFP_MCP_CLIENTS_JSON` của cfp-gateway
(list hoặc {"clients": [...]}), bổ sung:
  - `act_as`: các ID Số mà token này được hành động thay (bắt buộc để submit hoặc review);
  - `token_sha256`: lưu băm thay cho token gốc (khuyến nghị cho Cloud).
Scope: read • submit • review • operate • admin.

Biến cũ `SQZ_API_TOKEN` / `SQZ_ADMIN_TOKEN` vẫn chạy (principal LEGACY) nhưng LEGACY
không bao giờ được review: review cần danh tính cụ thể.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import dataclass, field

from .ids import InvalidID, classify

SCOPES = {"read", "submit", "review", "operate", "admin"}
ANY = "*"


@dataclass(frozen=True)
class Principal:
    ai_id: str
    name: str
    scopes: frozenset[str]
    act_as: frozenset[str] = field(default_factory=frozenset)

    def can(self, scope: str) -> bool:
        return scope in self.scopes or "admin" in self.scopes and scope != "review"

    def may_act_as(self, cfp_id: str) -> bool:
        return cfp_id in self.act_as or ANY in self.act_as

    def public(self) -> dict:
        return {"ai_id": self.ai_id, "name": self.name, "scopes": sorted(self.scopes),
                "act_as": sorted(self.act_as)}


class AuthError(PermissionError):
    pass


def _sha(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def load_clients(env: dict | None = None) -> list[tuple[str, Principal]]:
    env = os.environ if env is None else env
    out: list[tuple[str, Principal]] = []
    raw = (env.get("SQZ_CLIENTS_JSON") or "").strip()
    if raw:
        parsed = json.loads(raw)
        items = parsed.get("clients", []) if isinstance(parsed, dict) else parsed
        for item in items:
            ai_id = str(item.get("ai_id", "")).strip()
            digest = (item.get("token_sha256") or "").strip().lower() or (
                _sha(str(item["token"]).strip()) if item.get("token") else "")
            if not ai_id or len(digest) != 64:
                raise ValueError(f"Client thiếu ai_id hoặc token: {ai_id!r}")
            scopes = {str(s).lower() for s in item.get("scopes", ["read"])} & SCOPES or {"read"}
            act_as = set()
            for cid in item.get("act_as", []):
                classify(str(cid))  # ID Số hợp lệ, không cấp mới
                act_as.add(str(cid))
            out.append((digest, Principal(ai_id, str(item.get("name") or ai_id), frozenset(scopes),
                                          frozenset(act_as))))
    if env.get("SQZ_API_TOKEN"):
        out.append((_sha(env["SQZ_API_TOKEN"]), Principal("LEGACY_API", "legacy api token",
                                                          frozenset({"read", "submit"}), frozenset({ANY}))))
    if env.get("SQZ_ADMIN_TOKEN"):
        out.append((_sha(env["SQZ_ADMIN_TOKEN"]), Principal("LEGACY_ADMIN", "legacy admin token",
                                                            frozenset({"admin", "operate", "read"}))))
    digests = [d for d, _ in out]
    if len(digests) != len(set(digests)):
        raise ValueError("Hai danh tính dùng chung một token: không cho phép")
    return out


def authenticate(authorization: str, env: dict | None = None) -> Principal:
    supplied = authorization.removeprefix("Bearer ").strip()
    if not supplied:
        raise AuthError("Thiếu bearer token")
    digest = _sha(supplied)
    for d, principal in load_clients(env):
        if hmac.compare_digest(d, digest):
            return principal
    raise AuthError("Token không hợp lệ")


def require_act_as(principal: Principal, cfp_id: str, scope: str) -> None:
    try:
        classify(cfp_id)
    except InvalidID as exc:
        raise ValueError(str(exc)) from exc
    if not principal.can(scope):
        raise AuthError(f"{principal.ai_id} thiếu scope {scope}")
    if scope == "review":
        if ANY in principal.act_as or cfp_id not in principal.act_as:
            raise AuthError(f"{principal.ai_id} không được review thay {cfp_id}")
    elif not principal.may_act_as(cfp_id):
        raise AuthError(f"{principal.ai_id} không được hành động thay {cfp_id}")
