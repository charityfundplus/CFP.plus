#!/usr/bin/env bash
# SEC-P0-195-03b • Kiểm tra nâng cấp 002 → 003 khi đã có nhiệm vụ dở dang (đúng tình huống Supabase sandbox).
# Database TẠM riêng (mặc định cfp_upgrade, xoá khi xong) → không đụng cfp_ci hay dữ liệu pytest.
#   1. setup_pg.sh <db> --no-003   (002, đúng trạng thái Supabase hiện tại)
#   2. rls_upgrade_seed.sql         (nhiệm vụ IN_REVIEW / CHANGES_REQUESTED / ACCEPTED + Review cũ)
#   3. 003_office_rls.sql ×2 bằng cfp_migrator (lần 2 không được đánh số lại vòng)
#   4. rls_upgrade_in_review.sql    (in dòng SEC195_03B_UPGRADE pass=… fail=…)
# Cần cluster KHÔNG có database CFP khác (role dùng chung toàn cluster; setup_pg.sh xoá/tạo lại role) —
# CI: cluster postgres002 (cổng 5433), chạy TRƯỚC bước "chỉ 002".
# Dùng: PGHOST=... PGPORT=... PGUSER=<superuser> tests/forum/rls_upgrade_check.sh [dbname]
set -euo pipefail
DB=${1:-cfp_upgrade}
HERE=$(cd "$(dirname "$0")" && pwd)
SQL="$HERE/../../services/forum/sql"
cleanup() { psql -q -d postgres -c "DROP DATABASE IF EXISTS $DB" >/dev/null 2>&1 || true; }
trap cleanup EXIT
"$HERE/setup_pg.sh" "$DB" --no-003 >/dev/null
psql -v ON_ERROR_STOP=1 -q -d "$DB" -f "$HERE/rls_upgrade_seed.sql"
for run in 1 2; do
  if ! out=$(psql -v ON_ERROR_STOP=1 -q -U cfp_migrator -d "$DB" -f "$SQL/003_office_rls.sql" 2>&1); then
    echo "$out" | grep -v NOTICE; echo "FAILED 003_office_rls.sql (run$run)"; exit 1
  fi
  echo "applied 003_office_rls.sql (run$run, có dữ liệu dở dang) as cfp_migrator"
done
psql -v ON_ERROR_STOP=1 -d "$DB" -f "$HERE/rls_upgrade_in_review.sql"
