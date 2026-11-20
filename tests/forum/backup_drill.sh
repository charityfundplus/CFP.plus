#!/usr/bin/env bash
# Diễn tập SAO LƯU → KHÔI PHỤC cho dữ liệu Diễn Đàn + Văn Phòng (+ Worker nếu có) — mọi schema cfp_*, không phụ thuộc gói Supabase.
# Supabase gói Free không có bản sao lưu tải về / PITR, nên quy trình này là bản sao lưu logic (pg_dump dữ liệu).
#
#   PGHOST=... PGPORT=... PGUSER=<superuser> tests/forum/backup_drill.sh <db nguồn> <db đích mới>
# 1) pg_dump --data-only 4 schema của <db nguồn> (định dạng custom, kèm sha256)
# 2) dựng <db đích> từ cấu trúc của nguồn (pg_dump --schema-only: bảng, RLS, quyền)
# 3) pg_restore dữ liệu (tắt trigger trong phiên khôi phục), đặt lại sequence
# 4) so khớp từng bảng: số dòng + md5 toàn bộ nội dung (sắp theo khóa chính) → BACKUP_DRILL=PASS|FAIL
# Tệp sao lưu chứa email + mã băm mật khẩu: KHÔNG commit, KHÔNG đưa lên artifact công khai.
set -euo pipefail
SRC=${1:?db nguồn}; DST=${2:?db đích}
OUT=${BACKUP_DIR:-$(mktemp -d)}; mkdir -p "$OUT"; chmod 700 "$OUT"
DUMP="$OUT/cfp-$SRC-$(date -u +%Y%m%dT%H%M%SZ).dump"
mapfile -t SCHEMAS < <(psql -qtA -d "$SRC" -c "select nspname from pg_namespace where nspname like 'cfp\_%' order by 1")
args=(); for s in "${SCHEMAS[@]}"; do args+=(-n "$s"); done

t0=$(date +%s%3N)
pg_dump -d "$SRC" --data-only -Fc "${args[@]}" -f "$DUMP"
echo "dump=$(basename "$DUMP") bytes=$(stat -c %s "$DUMP") sha256=$(sha256sum "$DUMP" | cut -c1-16) ms=$(( $(date +%s%3N) - t0 ))"

# Đích: database mới, cấu trúc lấy từ chính nguồn (schema, bảng, policy RLS, quyền) — vai trò đã có trong cụm.
psql -q -d postgres -c "DROP DATABASE IF EXISTS $DST" -c "CREATE DATABASE $DST OWNER cfp_migrator" >/dev/null
pg_dump -d "$SRC" --schema-only "${args[@]}" -f "$OUT/schema.sql"
psql -q -v ON_ERROR_STOP=1 -d "$DST" -f "$OUT/schema.sql" >/dev/null

t1=$(date +%s%3N)
pg_restore -d "$DST" --data-only --disable-triggers --single-transaction "$DUMP"
# đặt lại sequence theo giá trị lớn nhất để id mới không trùng
psql -qtA -d "$DST" <<'SQL' >/dev/null
DO $$ DECLARE r record; BEGIN
  FOR r IN SELECT s.relname seq, n.nspname sch, t.relname tbl, a.attname col
           FROM pg_class s JOIN pg_depend d ON d.objid = s.oid JOIN pg_class t ON t.oid = d.refobjid
           JOIN pg_namespace n ON n.oid = t.relnamespace JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
           WHERE s.relkind = 'S' AND n.nspname LIKE 'cfp_%' LOOP
    EXECUTE format('SELECT setval(%L, COALESCE((SELECT max(%I) FROM %I.%I), 0) + 1, false)', r.sch || '.' || r.seq, r.col, r.sch, r.tbl);
  END LOOP; END $$;
SQL
echo "restore_ms=$(( $(date +%s%3N) - t1 ))"

fingerprint() {  # mỗi bảng: tên | số dòng | md5 nội dung sắp theo toàn dòng
  psql -qtA -d "$1" -c "
    select string_agg(format('%s.%s', schemaname, tablename), ' ' order by schemaname, tablename)
    from pg_tables where schemaname like 'cfp_%'" | tr ' ' '\n' | while read -r t; do
      [ -n "$t" ] || continue
      psql -qtA -d "$1" -c "select '$t', count(*), md5(coalesce(string_agg(x::text, '|' order by x::text), '')) from $t x"
  done
}
fingerprint "$SRC" >"$OUT/src.txt"; fingerprint "$DST" >"$OUT/dst.txt"
rows=$(awk -F'|' '{s+=$2} END {print s+0}' "$OUT/src.txt")
echo "tables=$(wc -l <"$OUT/src.txt") rows=$rows"
pol() { psql -qtA -d "$1" -c "select count(*) || ' policies, ' || (select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname like 'cfp\_%' and c.relforcerowsecurity) || ' force_rls' from pg_policies where schemaname like 'cfp\_%'"; }
echo "schemas=${SCHEMAS[*]} • nguồn: $(pol "$SRC") • đích: $(pol "$DST")"
[ "$(pol "$SRC")" = "$(pol "$DST")" ] || { echo "RLS khác nhau"; echo "BACKUP_DRILL=FAIL"; exit 1; }
if diff "$OUT/src.txt" "$OUT/dst.txt" >"$OUT/diff.txt"; then echo "BACKUP_DRILL=PASS"; else cat "$OUT/diff.txt"; echo "BACKUP_DRILL=FAIL"; exit 1; fi
