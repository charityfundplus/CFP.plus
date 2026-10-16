# Codex 1 → Codex 2 • Core API delta

Runtime: `62e0e5f3b4156eab44e02f065f0bb62061905518`. Existing `P2Sandbox` + `createP2HTTP`, same login/session/SQLite/audit. No second API service or Master Registry.

All routes below require the existing `cfp_p2` HttpOnly cookie. POST requires exact Origin + JSON. Viewer may read public Registry references; this does not grant access to office/customer data or operations.

| Route | Input | Output |
|---|---|---|
| `GET /api/core/registry` | Optional `query` ≤160 chars, `type`, `chapter` string 0–9, integer `limit` 1–100 (default 30), `offset` 0–10000 | `records`, `total`, `offset`, `limit`, `provenance` |
| `GET /api/core/registry/<id>` | Exact numeric string, preserving all zeros; no query fields | `record`, direct `children`, flat recursive `descendants` with `depth`, `provenance` |
| `GET /api/core/registry-validation` | No fields | Counts, duplicate/Parent/cycle/lineage/hold findings, explicit missing roster/bindings |
| `GET /api/core/hstdn-openai` | No fields | Source-derived Country/AI Country/Developer/AI, unallocated HSTDN reference, learning, sources, 6-vault readiness, blockers |
| `POST /api/core/chatgpt-project` | `{"id":"691181"}` only | Existing `id`, `parent`, `canonicalLink`, manual `instructions`, ChatGPT entry/docs URL. `projectID=null`, `allocatedID=false`, `externalProjectCreated=false` |

`type` supports `country`, `ai-country`, `developer`, `ai`, `si`, `super-pair`, `hstdn`. Current source contains no SI, pair or HSTDN binding. Empty results mean missing source records, not permission to create an ID. Duplicate names return multiple records; exact numeric lookup never resolves by guessed identity. Group is display metadata from Chapter: 000/135/246/789. V stays governance, not a numeric ID. Parent is taken from explicit source references, never derived by trimming digits.

All responses carry `hub=https://cfp.plus/69`, `readOnly=true`, `registryWrites=0`, `activationAllowed=false`. Each returned record has unverified identity/authority/route flags; source byte verification is separate. The existing US governance hold propagates into OpenAI/ChatGPT references and manual planning instructions; it is not overridden by HTTP 200.

Status: 401 missing/expired/revoked session; 403 wrong Origin/Host; 400 malformed ID/query or extra/duplicate fields; 404 unknown ID; 409 duplicate ID; 503 missing/modified/invalid source. Do not show 503/404 as an active profile. Source paths are fixed by server code; no client-provided source path, revision, Parent, DID, grant or visibility setting is accepted.

`registry-office.js` mounts a read/search/OpenAI panel into existing `/p2` and attaches the ChatGPT action to pair cards. A synthetic pair with no bound numeric ID keeps the action disabled. Existing source IDs can generate a manual packet through the registry panel. The packet contains only public reference fields and does not send data to ChatGPT automatically. Browser execution remains unverified in this environment; see `HANDOFF_VI.md`.

## Local data functions

```js
import {createRecoveryPoint, replicateRecoveryPoint, restoreRecoveryPoint}
  from './scripts/hub69-data.mjs';

// Existing service + authorized maintainer token, quiescent state, caller-owned paths/keys.
const receipt = createRecoveryPoint({service, token, destination: newPrivatePoint, publicKey});
const readback = replicateRecoveryPoint(newPrivatePoint, newReplicaDirectory);
const restored = restoreRecoveryPoint({source: newReplicaDirectory, destination: newDatabase, privateKey});
// restored.service is a NEW database generation; old sessions are revoked.
// Caller closes it when verification is complete. No application pointer is switched.
restored.service.close();
```

Destination directories/DB must not exist; no overwrite/prune. Receipt metadata is also inside the authenticated encrypted payload, so changing the cleartext receipt cannot forge Registry provenance or activation status. Full DB backup requires existing maintainer authority and `pairs=['*']`. Filesystem points use private permissions, fsync and byte/hash readback. Replica readback alone has `contentAuthenticated=false`; decryption/authentication occurs on restore. This is a local sandbox replica, not remote synchronization, WORM, independent custody or production recovery certification.

Code/tests and examples are pinned in this directory's evidence manifest and TAP log. ReviewSI/GrokSI should review this exact delta; no independent acceptance is implied.
