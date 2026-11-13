#!/usr/bin/env bash
# Chạy tests/forum/smoke_live.py với server uvicorn thật trên Postgres (4 schema/role + 003) — cùng script
# mà đầu mối Render dùng với URL HTTPS sandbox. Tài khoản/mật khẩu sinh ngẫu nhiên cho từng lượt, không lưu.
# Cần: database đã dựng bằng tests/forum/setup_pg.sh <DB>.
set -euo pipefail
DB=${1:-cfp_ci}; PORT=${SMOKE_PORT:-8765}; OUT=${SMOKE_OUT:-smoke-live.json}
cd "$(dirname "$0")/../.."
H=${PGHOST:-localhost}; PP=${PGPORT:-5432}
case "$H" in /*) U="postgresql+psycopg://%s@/$DB?host=$H&port=$PP";; *) U="postgresql+psycopg://%s@$H:$PP/$DB";; esac
export CFP_FORUM_AUTH_DB=$(printf "$U" cfp_forum_auth_rw) CFP_FORUM_DB_SIEU_BO_DOI=$(printf "$U" cfp_forum_sbd_rw) \
  CFP_FORUM_DB_SI_AI_HSTDN=$(printf "$U" cfp_forum_hstdn_rw) CFP_OFFICE_DB=$(printf "$U" office_app) \
  CFP_OFFICE_ADMIN_DB=$(printf "$U" cfp_migrator) CFP_FORUM_COOKIE_SECURE=auto \
  CFP_WORKER_DB=$(printf "$U" worker_app) CFP_WORKER_ADMIN_DB=$(printf "$U" cfp_migrator) \
  CFP_WORKER_INPROCESS=1 CFP_WORKER_INTERVAL=5
# http local → cookie không Secure (HTTPS vẫn Secure). Worker chạy trong tiến trình như Render Free;
# kill switch HTTP dùng cfp_migrator (được SET ROLE worker_governance, xem setup_pg.sh).
B=http://127.0.0.1:$PORT
python -m uvicorn services.forum.asgi:app --host 127.0.0.1 --port "$PORT" --workers 1 > smoke-server.log 2>&1 &
SRV=$!; trap 'kill $SRV 2>/dev/null || true' EXIT
for _ in $(seq 30); do curl -sf "$B/api/health" >/dev/null && break; sleep 1; done
RUN=$(date -u +%Y%m%d%H%M%S)
export SMOKE_PASSWORD=$(python -c 'import secrets; print(secrets.token_urlsafe(18))')
export SMOKE_GOV_EMAIL="smoke-gov-$RUN@example.org" SMOKE_REVIEWER_EMAIL="smoke-rev-$RUN@example.org"
for e in "$SMOKE_GOV_EMAIL" "$SMOKE_REVIEWER_EMAIL"; do
  curl -sf -o /dev/null -X POST "$B/api/auth/register" -H 'Content-Type: application/json' -H 'X-CFP-Forum: 1' \
    -H "Origin: $B" -d "{\"email\":\"$e\",\"password\":\"$SMOKE_PASSWORD\",\"name\":\"Smoke ${e%%@*}\"}"
done
python -m services.forum.admin grant-office-role governance "$SMOKE_GOV_EMAIL"
python -m services.forum.admin grant-office-role reviewer "$SMOKE_REVIEWER_EMAIL"
python -m services.forum.admin grant-admin si-ai-hstdn "$SMOKE_GOV_EMAIL"   # duyệt thành viên HSTDN
sleep 61  # tách khỏi cửa sổ rate limit của bước đăng ký (cùng IP)
python -m tests.forum.smoke_live --base "$B" --allow-http --out "$OUT"
