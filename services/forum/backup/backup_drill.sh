#!/usr/bin/env bash
# CFP+ • Sao lưu + DIỄN TẬP KHÔI PHỤC cho các kho Diễn Đàn / Văn Phòng / Worker (Postgres, Supabase).
#
# Mỗi lần chạy:
#   1. Kiểm tra phủ quyền: role sao lưu đọc được MỌI bảng trong các schema kho (thiếu → FAIL, không sao lưu thiếu).
#   2. pg_dump (định dạng custom) các schema kho; bỏ DỮ LIỆU phiên đăng nhập (cfp_forum_auth.sessions).
#   3. Chụp số dòng + md5 nội dung từng bảng ở nguồn (row_security=off: RLS lọc dòng → lỗi, không thiếu âm thầm).
#   4. Khôi phục vào một database TẠM MỚI trên máy chủ diễn tập, so sánh từng bảng → PASS/FAIL.
#   5. Ghi manifest.json (schema, số dòng, md5, sha256 bản dump, phiên bản) rồi xóa database tạm.
# Script KHÔNG mã hóa và KHÔNG tải lên đâu cả: bước đó do workflow làm SAU khi diễn tập PASS.
#
# Biến môi trường:
#   BACKUP_SOURCE_URL   conninfo/URL libpq của role CHỈ ĐỌC (006_backup_role.sql: cfp_backup_ro)
#   RESTORE_ADMIN_URL   conninfo/URL libpq (quyền CREATE DATABASE) của máy chủ diễn tập, KHÔNG phải nguồn
#   OUT_DIR             thư mục ghi dump + manifest (mặc định ./backup-out)
#   PG_BIN              thư mục pg_dump/pg_restore/psql cùng major với nguồn (mặc định theo PATH)
#   CFP_BACKUP_MIN_ROWS tổng số dòng tối thiểu mong đợi (mặc định 0; CI đặt >0 để chắc có dữ liệu thật)
set -euo pipefail
: "${BACKUP_SOURCE_URL:?thiếu BACKUP_SOURCE_URL}"
: "${RESTORE_ADMIN_URL:?thiếu RESTORE_ADMIN_URL}"
OUT_DIR=${OUT_DIR:-./backup-out}
BIN=${PG_BIN:+$PG_BIN/}
MIN_ROWS=${CFP_BACKUP_MIN_ROWS:-0}
SCHEMAS="cfp_forum_auth cfp_forum_sbd cfp_forum_hstdn cfp_office cfp_worker"
EXCLUDE_DATA="cfp_forum_auth.sessions"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
SCRATCH="cfp_restore_drill_$(date -u +%Y%m%d%H%M%S)_$$"
mkdir -p "$OUT_DIR"
DUMP="$OUT_DIR/cfp-backup-$STAMP.dump"
fail() { echo "FAIL: $*" >&2; echo "BACKUP_DRILL=FAIL"; exit 1; }
src() { PGOPTIONS="-c row_security=off" "${BIN}psql" -X -v ON_ERROR_STOP=1 -tA -d "$BACKUP_SOURCE_URL" "$@"; }
adm() { "${BIN}psql" -X -v ON_ERROR_STOP=1 -tA -d "$RESTORE_ADMIN_URL" "$@"; }
scratch_url() {  # cùng máy chủ diễn tập, database tạm
  if [[ "$RESTORE_ADMIN_URL" == postgres*://* ]]; then
    local base=${RESTORE_ADMIN_URL%%\?*} qs=""; [[ "$RESTORE_ADMIN_URL" == *\?* ]] && qs="?${RESTORE_ADMIN_URL#*\?}"
    echo "${base%/*}/$SCRATCH$qs"
  else
    echo "$RESTORE_ADMIN_URL dbname=$SCRATCH"
  fi
}
cleanup() { adm -q -c "DROP DATABASE IF EXISTS $SCRATCH" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# 0. Schema kho có thật ở nguồn
present=$(src -c "select string_agg(nspname, ' ' order by nspname) from pg_namespace
                  where nspname = any(string_to_array('$SCHEMAS', ' '))")
[ -n "$present" ] || fail "nguồn không có schema kho nào ($SCHEMAS)"
echo "schemas=$present"
in_list="string_to_array('$present', ' ')"

# 1. Phủ quyền: mọi bảng phải đọc được bằng role sao lưu
missing=$(src -c "select string_agg(format('%I.%I', schemaname, tablename), ',') from pg_tables
                  where schemaname = any($in_list)
                    and not has_table_privilege(current_user, format('%I.%I', schemaname, tablename), 'SELECT')")
[ -z "$missing" ] || fail "role sao lưu không đọc được: $missing (chạy lại 006_backup_role.sql)"
[ "$(src -c "select current_setting('transaction_read_only')")" = on ] \
  || echo "WARN: phiên sao lưu không ở chế độ read-only (kiểm tra 006_backup_role.sql)"
echo "coverage=ok role=$(src -c 'select current_user')"

# 2. Dump
args=(); for s in $present; do args+=(-n "$s"); done
"${BIN}pg_dump" -d "$BACKUP_SOURCE_URL" -Fc --no-owner --no-privileges "${args[@]}" \
  --exclude-table-data="$EXCLUDE_DATA" -f "$DUMP" || fail "pg_dump lỗi"
sha=$(sha256sum "$DUMP" | cut -d' ' -f1)
echo "dump=$(basename "$DUMP") bytes=$(stat -c %s "$DUMP") sha256=$sha"

# 3. Chụp số dòng + md5 từng bảng (trừ bảng chỉ lấy cấu trúc)
snapshot() {  # snapshot <hàm psql> → "schema.table|count|md5" mỗi dòng, sắp xếp
  local run=$1 tables t
  tables=$($run -c "select format('%I.%I', schemaname, tablename) from pg_tables
                    where schemaname = any($in_list) order by 1")
  for t in $tables; do
    [[ ",$EXCLUDE_DATA," == *",$t,"* ]] && continue
    $run -c "select '$t' || '|' || count(*) || '|' || md5(coalesce(string_agg(x::text, E'\n' order by x::text), ''))
             from $t x"
  done
}
snapshot src > "$OUT_DIR/source.snapshot"
total=$(awk -F'|' '{s+=$2} END {print s+0}' "$OUT_DIR/source.snapshot")
echo "tables=$(wc -l < "$OUT_DIR/source.snapshot") rows=$total"
[ "$total" -ge "$MIN_ROWS" ] || fail "tổng số dòng $total < CFP_BACKUP_MIN_ROWS=$MIN_ROWS"

# 4. Khôi phục vào database tạm mới
adm -q -c "CREATE DATABASE $SCRATCH" >/dev/null
# Policy RLS tham chiếu role theo tên: tạo role NOLOGIN còn thiếu trên máy chủ diễn tập (không quyền gì).
for r in $(src -c "select distinct unnest(roles) from pg_policies where schemaname = any($in_list)" | grep -vx public || true); do
  adm -q -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$r') THEN CREATE ROLE \"$r\" NOLOGIN; END IF; END \$\$" >/dev/null
done
"${BIN}pg_restore" -d "$(scratch_url)" --no-owner --no-privileges --exit-on-error "$DUMP" \
  || fail "pg_restore lỗi"
rst() { "${BIN}psql" -X -v ON_ERROR_STOP=1 -tA -d "$(scratch_url)" "$@"; }
snapshot rst > "$OUT_DIR/restore.snapshot"
if ! diff -u "$OUT_DIR/source.snapshot" "$OUT_DIR/restore.snapshot" > "$OUT_DIR/drill.diff"; then
  cat "$OUT_DIR/drill.diff" >&2; fail "dữ liệu khôi phục khác nguồn"
fi
rm -f "$OUT_DIR/drill.diff"
echo "restore=identical scratch=$SCRATCH"

# 5. Manifest (không chứa dữ liệu, chỉ số đếm và mã băm)
python3 - "$OUT_DIR" "$DUMP" "$sha" "$STAMP" "$present" "$EXCLUDE_DATA" \
  "$("${BIN}pg_dump" --version)" "$(src -c 'show server_version')" <<'PY'
import json, sys, pathlib
out, dump, sha, stamp, schemas, excl, pgd, srv = sys.argv[1:9]
rows = [l.split("|") for l in pathlib.Path(out, "source.snapshot").read_text().splitlines() if l]
json.dump({"created_utc": stamp, "dump": pathlib.Path(dump).name, "sha256": sha, "schemas": schemas.split(),
           "excluded_data": excl.split(","), "pg_dump": pgd, "source_server": srv,
           "tables": {t: {"rows": int(n), "md5": m} for t, n, m in rows},
           "restore_drill": "PASS"}, open(pathlib.Path(out, "manifest.json"), "w"), ensure_ascii=False, indent=1)
PY
echo "BACKUP_DRILL=PASS"
