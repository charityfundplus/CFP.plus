# P2 sandbox steps

1. Use Node24+ with node:sqlite support. Read P2_STATUS.md limits before starting. Keep all data synthetic and loopback-only.
2. Run npm run demo:p2. The executable creates a temporary database, synthetic users, task/run/separate review, consistent backup and isolated restore; it removes temporary state afterward. Passwords/tokens are never printed.
3. For retained local tests, import P2Sandbox from sandbox/p2-service.mjs and create a database under an access-controlled local directory. Provision synthetic accounts locally with id/password/role/workspace/maintainer. Do not accept provision fields from anonymous HTTP requests.
4. login returns a token. execute(token, command, args, {idempotencyKey}) supports existing Core snapshot/instantiate/createTask/runTask/reviewTask/stop/recover/retry/upgrade/rollback. The createTask key is required and bound to subject/workspace/request digest. Never send role/workspace as request authority.
5. Use separate subjects to review; reviewer does not automatically have maintainer permission. Use revoke to invalidate a session. Tokens expire in 15 minutes. Pair mission/resource permissions remain Core-controlled.
6. verify returns local audit sequence/digest. Record checkpoint externally through an authorized custodian before claiming independent audit continuity. Audit contains action/result/digests, not passwords/tokens. State and audit commits are transactional; a failed write must not be presented as successful work.
7. Backup: authenticated maintainer calls backup(token,newPath); existing targets are refused. SQLite VACUUM INTO captures a consistent snapshot including committed WAL state. Retain the adjacent JSON digest/version/checkpoint metadata.
8. Restore: trusted local admin calls P2Sandbox.restore(backup,newDestination). Existing destinations, bad digest/version/checkpoint are rejected. Sessions are removed and a restore-generation event is appended. Reauthenticate and inspect interrupted tasks; reviewer recover, then explicit retry creates a new task. Never roll back history in place.
9. Five adapters remain disabled/mock with unknown owner/URL/scope; no connect method. Do not activate real reads without separate approval.
10. Only run npm run test:p2 after material P2 changes; broaden regression if shared Core changes. Submit new evidence and exceptions to review. No production deployment or Canonical/DID allocation.

Original P1 anchors: PR124; Drive https://drive.google.com/drive/folders/1b2ebHt2WIK6Ys5SuYsBGNZScZ6fi4IHO ; Notion https://app.notion.com/p/3f8caac9a55781f794dcc175b857057c . Extend these records; do not create a replacement HUB/Core.

## Authenticated HTTP/UI extension

Create a private synthetic state directory. Set CFP_P2_DB to its database path. Pipe a local JSON array of synthetic accounts to npm run provision:p2 (never commit the account/password file). Each account: id, password (12+ chars), role, workspace, optional maintainer, pairs (array of allowed config keys or ["*"]). No account creation or role selection is offered over HTTP.

Run npm run start:p2 with CFP_P2_DB and optional CFP_P2_PORT (default4174); open http://127.0.0.1:4174/p2. Sign in as editor, create a synthetic task, run it; logout and sign in as a separate reviewer to acknowledge it. Workspace and pair grants come from SQLite, not request fields. Use VI/EN and mobile layout. Cookies are HttpOnly/SameSite Strict for loopback HTTP; real-network transport remains forbidden and would require TLS/Secure plus review.

## Bounded executable release/rollback (trusted local administration)

Stop HTTP before maintenance. Import packRelease and SandboxReleaseControl from sandbox/release-control.mjs. packRelease(source,newBundleDirectory) copies runtime source and returns a release manifest digest. Keep bundles immutable and verify the digest before activation. Provision a synthetic maintainer with full workspace pair scope locally.

control.activate({service,token,release,digest}) executes selected bundle health, refuses pending tasks, makes a consistent checkpoint and sets active pointer atomically. Activate the next compatible bundle only after its health passes. control.rollback({service,token}) verifies/executes the previous bundle, preserves current database/audit in a retained backup, restores the previous checkpoint into a new database, invalidates sessions, and sets pointer to previous source/new database. Never restore over the current DB.

Start with CFP_P2_RELEASE_DIR and CFP_P2_DB using node scripts/p2-release-serve.mjs; after rollback the pointer's restored database wins. Reauthenticate. Inspect release events, retained backup and restored audit generation. Migrations beyond matching compatibility remain blocked. This is sandbox release control, not autonomous production deployment.
