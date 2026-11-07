#!/usr/bin/env bash
# Chạy toàn bộ test backend (SQLite + Postgres 4 schema/role + Playwright). Dùng cho CI và local.
# Cần: PGHOST, PGPORT; database đã dựng bằng tests/forum/setup_pg.sh <DB>.
set -uo pipefail
DB=${1:-cfp_ci}
cd "$(dirname "$0")/../.."
H=${PGHOST:-localhost}; PORT=${PGPORT:-5432}
case "$H" in /*) U="postgresql+psycopg://%s@/$DB?host=$H&port=$PORT";; *) U="postgresql+psycopg://%s@$H:$PORT/$DB";; esac
rc=0
echo "::group::pytest SQLite"; env -u CFP_FORUM_TEST_AUTH_DB python -m pytest tests/forum -q -p no:cacheprovider || rc=1; echo "::endgroup::"
export CFP_FORUM_TEST_AUTH_DB=$(printf "$U" cfp_forum_auth_rw) CFP_FORUM_TEST_DB_SIEU_BO_DOI=$(printf "$U" cfp_forum_sbd_rw) \
  CFP_FORUM_TEST_DB_SI_AI_HSTDN=$(printf "$U" cfp_forum_hstdn_rw) CFP_OFFICE_TEST_DB=$(printf "$U" office_app) \
  CFP_FORUM_TEST_ADMIN_DB=$(printf "$U" cfp_migrator) CFP_WORKER_TEST_DB=$(printf "$U" worker_app)
echo "::group::pytest Postgres (4 schema/role + RLS 003)"; CFP_REQUIRE_003=${CFP_REQUIRE_003:-1} python -m pytest tests/forum -v -p no:cacheprovider --junitxml=forum-pytest.xml || rc=1; echo "::endgroup::"
export CFP_FORUM_AUTH_DB=$CFP_FORUM_TEST_AUTH_DB CFP_FORUM_DB_SIEU_BO_DOI=$CFP_FORUM_TEST_DB_SIEU_BO_DOI \
  CFP_FORUM_DB_SI_AI_HSTDN=$CFP_FORUM_TEST_DB_SI_AI_HSTDN CFP_OFFICE_DB=$CFP_OFFICE_TEST_DB CFP_OFFICE_ADMIN_DB=$CFP_FORUM_TEST_ADMIN_DB
echo "::group::Playwright diễn đàn"; node tests/forum/forum_e2e.test.js || rc=1; echo "::endgroup::"
echo "::group::Playwright Văn Phòng SI AI (iPhone 13)"; node tests/forum/office_e2e.test.js || rc=1; echo "::endgroup::"
exit $rc
