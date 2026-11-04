#!/usr/bin/env bash
# Dựng database giống Supabase cfp-plus-forum-sandbox cho test:
#   nền tảng diễn đàn = schemas_up.sql (#193, đã áp trên Supabase) → Văn Phòng = 002_office.sql.
# Migration chạy bằng role KHÔNG phải superuser (CREATEROLE + chủ database), có anon/authenticated.
# Kiểm tra: chạy 2 lần (idempotent) và vòng khôi phục down → up cho cả hai phần.
# Dùng: PGHOST=... PGPORT=... PGUSER=<superuser> tests/forum/setup_pg.sh <dbname> [--no-003]
#   --no-003: dừng ở 002 (đúng trạng thái Supabase hiện tại) để kiểm tra tương thích ngược.
set -euo pipefail
DB=${1:-cfp_ci}
WITH_003=1; [ "${2:-}" = "--no-003" ] && WITH_003=0
HERE=$(cd "$(dirname "$0")" && pwd)
SQL="$HERE/../../services/forum/sql"
psql -v ON_ERROR_STOP=1 -q -d postgres <<SQL
DROP DATABASE IF EXISTS $DB;
DO \$\$ BEGIN
  -- Giống postgres trên Supabase: không superuser, có CREATEROLE + BYPASSRLS (đã đối chiếu pg_roles).
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cfp_migrator') THEN CREATE ROLE cfp_migrator LOGIN CREATEROLE BYPASSRLS; END IF;
  ALTER ROLE cfp_migrator BYPASSRLS;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
END \$\$;
CREATE DATABASE $DB OWNER cfp_migrator;
SQL
psql -q -d "$DB" -c "REVOKE CREATE ON SCHEMA public FROM PUBLIC" >/dev/null

apply() {  # apply <file> <nhãn>
  if ! out=$(psql -v ON_ERROR_STOP=1 -q -U cfp_migrator -d "$DB" -f "$SQL/$1" 2>&1); then
    echo "$out" | grep -v NOTICE; echo "FAILED $1 ($2)"; exit 1
  fi
  echo "applied $1 ($2) as cfp_migrator"
}
apply schemas_up.sql run1; apply schemas_up.sql run2
apply 002_office.sql run1; apply 002_office.sql run2
apply 002_office_down.sql rollback; apply 002_office.sql reapply
apply schemas_down.sql rollback-forum; apply schemas_up.sql reapply-forum
apply 002_office.sql run-after-forum-reapply
if [ "$WITH_003" = 1 ]; then
  apply 003_office_rls.sql run1; apply 003_office_rls.sql run2
  apply 003_office_rls_down.sql rollback-003; apply 003_office_rls.sql reapply-003
fi

# Sandbox test: người chạy test đóng vai Human Governance (membership office_governance, SET)
# và được SET ROLE sang anon/authenticated như SQL Editor Supabase. Bật LOGIN cho office_app.
psql -v ON_ERROR_STOP=1 -q -U cfp_migrator -d "$DB" -c "ALTER ROLE office_app LOGIN"
psql -v ON_ERROR_STOP=1 -q -d "$DB" -c "GRANT office_governance TO cfp_migrator WITH SET TRUE" \
  -c "GRANT anon, authenticated TO cfp_migrator WITH SET TRUE"
q() { psql -tA -U cfp_migrator -d "$DB" -c "$1"; }
q "select 'forum_schemas=' || string_agg(nspname || ':' || pg_get_userbyid(nspowner), ',' order by nspname) from pg_namespace where nspname like 'cfp_forum_%'"
q "select 'office_tables=' || count(*) from pg_tables where schemaname = 'cfp_office'"
q "select 'office_rls_forced=' || count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where c.relkind='r' and n.nspname='cfp_office' and c.relrowsecurity and c.relforcerowsecurity"
q "select 'rls_user_policies=' || count(*) from pg_policies where schemaname='cfp_office' and policyname like 'rls_%'"
q "select 'anon_usage=' || count(*) from pg_namespace where nspname in ('cfp_office','cfp_forum_auth','cfp_forum_sbd','cfp_forum_hstdn') and (has_schema_privilege('anon', oid, 'USAGE') or has_schema_privilege('authenticated', oid, 'USAGE'))"
