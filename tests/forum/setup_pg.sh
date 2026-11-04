#!/usr/bin/env bash
# Dựng database sandbox giống Supabase cho test: migration chạy bằng role KHÔNG phải superuser
# (chỉ CREATEROLE + chủ database), có sẵn role API anon/authenticated như Supabase.
# Dùng: PGHOST=... PGPORT=... PGUSER=<superuser> tests/forum/setup_pg.sh <dbname>
# Không chứa mật khẩu; xác thực dựa vào cấu hình máy chủ test (trust/peer).
set -euo pipefail
DB=${1:-cfp_forum}
HERE=$(cd "$(dirname "$0")" && pwd)
SQL="$HERE/../../services/forum/sql"
psql -v ON_ERROR_STOP=1 -q -d postgres <<SQL
DROP DATABASE IF EXISTS $DB;
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cfp_migrator') THEN CREATE ROLE cfp_migrator LOGIN CREATEROLE; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
END \$\$;
CREATE DATABASE $DB OWNER cfp_migrator;
SQL
psql -q -d "$DB" -c "REVOKE CREATE ON SCHEMA public FROM PUBLIC" >/dev/null
for f in 001_isolation.sql 002_office.sql; do
  for run in 1 2; do  # chạy 2 lần: kiểm tra idempotent
    if ! out=$(psql -v ON_ERROR_STOP=1 -q -U cfp_migrator -d "$DB" -f "$SQL/$f" 2>&1); then
      echo "$out" | grep -v NOTICE; echo "FAILED $f (run $run)"; exit 1
    fi
    echo "applied $f (run $run) as cfp_migrator"
  done
done
# Sandbox test: người chạy test đóng vai Human Governance (membership office_governance) và
# được SET ROLE sang anon/authenticated để kiểm tra chặn API công khai (giống SQL Editor Supabase).
psql -v ON_ERROR_STOP=1 -q -d "$DB" -c "GRANT office_governance TO cfp_migrator WITH SET TRUE" -c "GRANT anon, authenticated TO cfp_migrator WITH SET TRUE"
# Sandbox test: bật LOGIN cho role ứng dụng (môi trường thật: người vận hành đặt mật khẩu riêng).
psql -v ON_ERROR_STOP=1 -q -U cfp_migrator -d "$DB" -c \
  "ALTER ROLE forum_auth_app LOGIN; ALTER ROLE forum_sbd_app LOGIN; ALTER ROLE forum_hstdn_app LOGIN; ALTER ROLE office_app LOGIN;"
psql -tA -U cfp_migrator -d "$DB" -c "select 'tables=' || count(*) from pg_tables where schemaname in ('forum_auth','forum_sbd','forum_hstdn','cfp_office')"
psql -tA -U cfp_migrator -d "$DB" -c "select 'rls_forced=' || count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relkind='r' and n.nspname in ('forum_auth','forum_sbd','forum_hstdn','cfp_office') and c.relrowsecurity and c.relforcerowsecurity"
