#!/usr/bin/env bash
# Bằng chứng runtime: chạy worker thật (tiến trình riêng, role worker_app) trong ~DUR giây,
# bật/tắt kill switch bằng role worker_governance, in trạng thái + nhật ký. Dùng cho CI và local.
# Cần: PGHOST, PGPORT, DB đã dựng bằng setup_pg.sh (có 004).
set -euo pipefail
DB=${1:-cfp_ci}; DUR=${DUR:-40}
cd "$(dirname "$0")/../.."
H=${PGHOST:-localhost}; PORT=${PGPORT:-5432}
case "$H" in /*) U="postgresql+psycopg://%s@/$DB?host=$H&port=$PORT";; *) U="postgresql+psycopg://%s@$H:$PORT/$DB";; esac
export CFP_WORKER_DB=$(printf "$U" worker_app) CFP_WORKER_ADMIN_DB=$(printf "$U" cfp_migrator)
export CFP_WORKER_INTERVAL=${CFP_WORKER_INTERVAL:-3} CFP_WORKER_REGISTRY_EVERY=${CFP_WORKER_REGISTRY_EVERY:-10}
psql -q -U cfp_migrator -d "$DB" -c "truncate cfp_worker.jobs, cfp_worker.logs, cfp_worker.heartbeats restart identity" \
  -c "set role worker_governance" -c "update cfp_worker.control set value='false' where key='paused'"
python -m services.forum.worker run > worker-runtime.log 2>&1 & PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT
sleep $((DUR / 2))
python -m services.forum.worker pause --by ci-governance
sleep 8
python -m services.forum.worker status > worker-paused.json
python -m services.forum.worker resume --by ci-governance
sleep $((DUR / 2))
python -m services.forum.worker status > worker-status.json
kill $PID; wait $PID 2>/dev/null || true
python - <<'PY'
import json
p, s = json.load(open("worker-paused.json")), json.load(open("worker-status.json"))
hb = s["heartbeats"][0]
print(f"worker_alive={s['alive']} ticks={hb['ticks']} jobs={s['jobs']} alerts_24h={s['alerts_24h']} paused_seen={p['paused']}")
print("last_done=", json.dumps(s["last_done"], ensure_ascii=False))
assert p["paused"] and p["heartbeats"][0]["state"] == "paused", "kill switch không có hiệu lực"
assert not s["paused"] and s["alive"] and hb["ticks"] >= 5, "worker không chạy liên tục"
assert s["jobs"].get("done", 0) >= 2 and not s["jobs"].get("dead"), s["jobs"]
assert s["last_done"]["summary"]["chain_691121"] == ["911", "6911", "69112", "691121"]
assert s["last_done"]["summary"]["drift"] is False and s["last_done"]["summary"]["problems"] == []
print("WORKER_RUNTIME=PASS")
PY
psql -q -U cfp_migrator -d "$DB" -Atc "select at, level, event, coalesce(job_id::text,'-'), left(message, 120) from cfp_worker.logs order by id" > worker-logs.txt
wc -l < worker-logs.txt | sed 's/^/worker_log_lines=/'
