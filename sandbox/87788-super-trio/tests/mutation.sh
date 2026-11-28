#!/usr/bin/env bash
# Kiểm thử đột biến: mỗi dòng tắt một lớp bảo vệ; bộ test phải FAIL (caught).
set -u
SRC="$(cd "$(dirname "$0")/.." && pwd)"; M="$(mktemp -d)"; survived=0
MUTS=(
'if rid in seen:|if False:'
'if k.lower() in FORBIDDEN_KEYS:|if False:'
'if identity_of(src) != ident:|if False:'
'if ov["identity_sha256"] != sha256_bytes(canon(ident)):|if False:'
'for r in open_runs:|for r in []:'
'if cur == data:|if False:'
'if not ID_RE.match(rid):|if False:'
'if existing.get("identity", {}).get("id") != item["id"]:|if False:'
'if t["capability_status"] != STATUS_NOT_VERIFIED and not t["evidence"]:|if False:'
'if HERE not in out.parents and out != HERE:|if False:'
'if os.environ.get("CFP_PRODUCTION"):|if False:'
'if src is None:|if False:'
)
for m in "${MUTS[@]}"; do
  rm -rf "$M/w"; mkdir -p "$M/w"; cp -r "$SRC/." "$M/w/"; rm -rf "$M/w/out"
  python3 - "$M/w/trio.py" "${m%%|*}" "${m#*|}" <<'EOF'
import sys; p,a,b=sys.argv[1:]; s=open(p).read(); assert a in s, a; open(p,'w').write(s.replace(a,b,1))
EOF
  if (cd "$M/w" && python3 -m unittest discover -s tests >/dev/null 2>&1); then echo "SURVIVED: ${m%%|*}"; survived=$((survived+1)); else echo "caught: ${m%%|*}"; fi
done
rm -rf "$M"; echo "mutants=${#MUTS[@]} survived=$survived"; exit $survived
