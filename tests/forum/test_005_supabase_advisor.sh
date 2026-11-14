#!/usr/bin/env bash
# Kiểm chứng 005_supabase_advisor.sql trên Postgres thật, dựng lại đúng hàm + event trigger như Supabase sandbox.
#   1. Trước 005: anon/authenticated có EXECUTE (đúng cảnh báo advisor 0028/0029).
#   2. Sau 005 (chạy 2 lần): mất EXECUTE; anon gọi trực tiếp bị "permission denied".
#   3. Event trigger ensure_rls VẪN tự bật RLS cho bảng mới do role thường tạo.
#   4. Down → quyền trở lại; up lại → mất quyền. Database không có hàm → 005 bỏ qua, không lỗi.
# Dùng: PGHOST=... PGPORT=... PGUSER=<superuser> tests/forum/test_005_supabase_advisor.sh [dbname]
set -euo pipefail
DB=${1:-cfp_005}
HERE=$(cd "$(dirname "$0")" && pwd)
SQL="$HERE/../../services/forum/sql"
fail() { echo "FAIL: $*"; echo "ADVISOR_005=FAIL"; exit 1; }
q() { psql -v ON_ERROR_STOP=1 -tA -d "$DB" "$@"; }

psql -v ON_ERROR_STOP=1 -q -d postgres <<SQL
DROP DATABASE IF EXISTS $DB;
DROP DATABASE IF EXISTS ${DB}_plain;
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='anon') THEN CREATE ROLE anon NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cfp_005_app') THEN CREATE ROLE cfp_005_app LOGIN; END IF;
END \$\$;
CREATE DATABASE $DB;
CREATE DATABASE ${DB}_plain;
SQL

# Dựng lại hàm + event trigger như trên cfp-plus-forum-sandbox (pg_get_functiondef, 14/11/2026).
q -q <<'SQL'
GRANT CREATE ON SCHEMA public TO cfp_005_app;
GRANT anon, authenticated TO current_user;
CREATE OR REPLACE FUNCTION public.rls_auto_enable()
 RETURNS event_trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
DECLARE
  cmd record;
  tbl name;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        SELECT c.relname INTO tbl FROM pg_catalog.pg_class c WHERE c.oid = cmd.objid;
        EXECUTE format('alter table if exists %I.%I enable row level security', cmd.schema_name, tbl);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$function$;
CREATE EVENT TRIGGER ensure_rls ON ddl_command_end
  WHEN TAG IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
  EXECUTE FUNCTION public.rls_auto_enable();
SQL

priv() { q -c "select has_function_privilege('$1', 'public.rls_auto_enable()', 'EXECUTE')"; }
rls_of_new_table() {  # role thường tạo bảng mới → event trigger phải bật RLS
  psql -v ON_ERROR_STOP=1 -q -U cfp_005_app -d "$DB" -c "CREATE TABLE public.$1 (id int)" >/dev/null
  q -c "select relrowsecurity from pg_class where oid = 'public.$1'::regclass"
}
apply() {  # apply <file> <db>: lỗi SQL → FAIL (không nuốt lỗi)
  local out
  out=$(psql -v ON_ERROR_STOP=1 -q -d "$2" -f "$SQL/$1" 2>&1) || fail "$1 trên $2: $out"
  echo "applied $1 on $2"
}

echo "before_anon_execute=$(priv anon)";          [ "$(priv anon)" = t ] || fail "dựng lại sai: anon phải có EXECUTE trước 005"
echo "before_new_table_rls=$(rls_of_new_table t_before)"

apply 005_supabase_advisor.sql "$DB"; apply 005_supabase_advisor.sql "$DB"   # idempotent
for r in anon authenticated; do
  v=$(priv $r); echo "after_${r}_execute=$v"; [ "$v" = f ] || fail "$r vẫn có EXECUTE sau 005"
done
if out=$(psql -q -d "$DB" -c "SET ROLE anon; SELECT public.rls_auto_enable()" 2>&1); then fail "anon gọi được hàm: $out"; fi
echo "$out" | grep -q "permission denied" || fail "anon gọi hàm phải bị permission denied: $out"
echo "anon_direct_call=permission_denied"
v=$(rls_of_new_table t_after); echo "after_new_table_rls=$v"; [ "$v" = t ] || fail "event trigger không còn bật RLS"
v=$(q -c "select evtenabled from pg_event_trigger where evtname='ensure_rls'"); echo "event_trigger_enabled=$v"; [ "$v" = O ] || fail "event trigger bị tắt"

apply 005_supabase_advisor_down.sql "$DB"
v=$(priv anon); echo "down_anon_execute=$v"; [ "$v" = t ] || fail "down không khôi phục quyền"
apply 005_supabase_advisor.sql "$DB"
v=$(priv anon); echo "reapply_anon_execute=$v"; [ "$v" = f ] || fail "up lại không thu hồi quyền"

apply 005_supabase_advisor.sql "${DB}_plain"; apply 005_supabase_advisor_down.sql "${DB}_plain"
echo "plain_postgres_noop=ok"
echo "ADVISOR_005=PASS"
