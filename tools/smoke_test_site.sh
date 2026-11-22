#!/usr/bin/env bash
# Read-only smoke + exposure test for the CFP+ website.
# Usage: tools/smoke_test_site.sh http://localhost:8080      (CI / local image)
#        tools/smoke_test_site.sh https://cfp.plus           (production, read only)
# Exit code 0 = all checks pass. Only sends GET/HEAD requests.
set -u
BASE="${1:?base URL required}"
fail=0
code() { curl -s -o /dev/null --path-as-is -w '%{http_code}' "$BASE$1"; }
expect() { # expect <path> <allowed codes regex> <label>
  local c; c=$(code "$1")
  if [[ "$c" =~ ^($2)$ ]]; then echo "PASS $c $1 ($3)"; else echo "FAIL $c $1 ($3, expected $2)"; fail=1; fi
}

# Preflight: an unreachable site must never produce PASS results.
pre=$(code /)
if [ "$pre" = 000 ]; then echo "ABORT: $BASE unreachable (HTTP 000); no checks run"; exit 2; fi

echo "== Public pages must work"
for p in / /69/ /69 /000/ /0123456789/ /6/ /6911/ /6984/ /28882/ /267/ /12345678/ /styles.css /robots.txt /sitemap.xml; do
  expect "$p" 200 public
done

echo "== Internal files must NOT be served"
for p in /.git/config /.git/HEAD /.git/index /.git/FETCH_HEAD /.git/logs/HEAD /.git/ /.git \
         /%2egit/config /%2Egit/config //.git/config /./.git/config /69/../.git/config \
         /.github/workflows/website_content.yml /.github/PULL_REQUEST_TEMPLATE.md \
         /.gitignore /.dockerignore /.env /Dockerfile /deploy/nginx.conf \
         /tools/build_pages.py /tests/__init__.py /run_ctttc_v066_tests.py /patches/; do
  expect "$p" '404|403|400|301|302' internal
done

echo "== Headers"
hdr=$(curl -sI "$BASE/HUB69.md")
grep -qi '^content-type: text/plain; charset=utf-8' <<<"$hdr" && echo "PASS .md is text/plain utf-8" || { echo "FAIL .md content-type"; fail=1; }
hdr=$(curl -sI "$BASE/")
for h in 'x-content-type-options: nosniff' 'referrer-policy:'; do
  grep -qi "^$h" <<<"$hdr" && echo "PASS header $h" || { echo "FAIL header $h"; fail=1; }
done
grep -qiE '^server: nginx/[0-9]' <<<"$hdr" && { echo "FAIL server version disclosed"; fail=1; } || echo "PASS no nginx version in Server header"

# A redirect for a dot path is only safe if it does not land on the file.
c=$(curl -s -L -o /dev/null --path-as-is -w '%{http_code}' "$BASE/69/../.git/config")
[ "$c" = 200 ] && { echo "FAIL /69/../.git/config reachable after redirect"; fail=1; } || echo "PASS /69/../.git/config after redirect -> $c"

[ $fail = 0 ] && echo "RESULT: ALL PASS" || echo "RESULT: FAIL"
exit $fail
