# CFP+ Core • Backend V1 (prototype)
One local backend for CFP+ website, app and Siêu Bộ Đôi. Python 3.10+ standard library only.

## Run locally
```sh
export CFP_API_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
python3 services/cfp-core/app.py
curl http://127.0.0.1:8765/health
```
Private POST calls require `Authorization: Bearer <CFP_API_TOKEN>`. Never commit tokens. Service binds to loopback by default; do not expose directly to Internet. Put behind a reviewed TLS gateway, authentication, authorization, rate limiting, logging policy and backups before any deployment.

## API
- `GET /health`
- `GET /api/entities/{numeric_id}` — entity profile.
- `POST /api/entities` — provisional record, rejects duplicate IDs; DOES NOT mint canonical ID or DID/0.
- `POST /api/events` — consented advisory, official-link and feedback events; queues sync in outbox.
- `POST /api/tasks` — QUEUED task record only, not autonomous execution.

Example (authorized):
```sh
curl -X POST http://127.0.0.1:8765/api/events -H "Authorization: Bearer $CFP_API_TOKEN" -H "Content-Type: application/json" -d '{"entity_id":"69118","kind":"OFFICIAL_LINK_CLICK","consent":true,"payload":{"target":"https://openai.com/"}}'
```

## Storage synchronization
SQLite outbox is local only. `PENDING` means **not synced**. No Notion, GitHub, Google Drive, cloud storage or CFP+ MCP credentials are used. Implement reviewed adapters separately; each adapter must be explicitly authorized and use idempotency key `event_id`, write receipt, readback verification, retry/backoff and least-privilege scopes. No outbound transfer until approved.

## Scope and limitations
This is a foundation, not a production-ready payment system, deployed service, mobile app, task executor, AI integration or verified storage connector. CFP+ never receives payment details. Buyer transactions occur only on official provider channels. Do not claim transaction success without authorized evidence. Existing immutable IDs/Parents and Human Governance release gates remain authoritative.
