# CFP+ Core Coordination Engine — Backend Technical Specification

Status: DESIGN / SANDBOX ONLY. No production authorization. Related: Issue #227.

## Scope and invariants
- One verified entity = one immutable Canonical numeric ID; membership in many teams does not mint new IDs.
- Parent/child genealogy is distinct from team membership and runtime process spawning.
- An agent instance is a runtime worker, not necessarily a new registered entity.
- New official child IDs and DID transitions require Registry review and Human Governance approval.
- No fixed architectural cap on teams or descendants; enforce operational quotas, concurrency, budgets, depth and kill switches.
- Permission scopes are explicit, short-lived, least privilege; never automatically inherited.
- Each execution records input reference, actor, policy decision, model/skill version, outcome, reviewer and evidence.
- No autonomous production publishing, payments, credential grants, identity creation or merges.

## Suggested components
1. Registry service: canonical entities, parentage, DID versions, provenance and conflict review.
2. Team service: team catalog, many-to-many membership, role grants and revocation.
3. Skills service: source URL, upstream commit, license, hashes, risk review, test status and CFP+ adaptations.
4. Orchestrator: task DAG, queue, retries, idempotency, lease, heartbeats, timeouts, circuit breaker, cancellation.
5. Governance: policy engine, scoped capabilities, approval requests, human signoff and emergency stop.
6. Evidence: append-only audit events, artifacts, reviewer attestations and reports.

## Proposed relational schema (PostgreSQL)
```sql
CREATE TABLE entities (
  canonical_id text PRIMARY KEY CHECK (canonical_id ~ '^[0-9]+$'),
  display_name text NOT NULL,
  state text NOT NULL CHECK (state IN ('PROPOSED','VERIFIED','HOLD','RETIRED')),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE entity_relations (
  parent_id text NOT NULL REFERENCES entities(canonical_id),
  child_id text NOT NULL REFERENCES entities(canonical_id),
  relation_type text NOT NULL CHECK (relation_type IN ('GENEALOGY')),
  approved_at timestamptz NOT NULL,
  PRIMARY KEY(parent_id, child_id),
  CHECK(parent_id <> child_id)
);
CREATE TABLE teams (
  team_id uuid PRIMARY KEY,
  name text NOT NULL,
  state text NOT NULL DEFAULT 'ACTIVE'
);
CREATE TABLE team_memberships (
  team_id uuid NOT NULL REFERENCES teams(team_id),
  canonical_id text NOT NULL REFERENCES entities(canonical_id),
  role text NOT NULL,
  status text NOT NULL CHECK (status IN ('PENDING','ACTIVE','REVOKED')),
  PRIMARY KEY(team_id, canonical_id, role)
);
CREATE TABLE agents (
  agent_id uuid PRIMARY KEY,
  canonical_id text NOT NULL REFERENCES entities(canonical_id),
  parent_agent_id uuid REFERENCES agents(agent_id),
  state text NOT NULL CHECK (state IN ('PROVISIONED','RUNNING','PAUSED','STOPPED')),
  max_children integer NOT NULL DEFAULT 0 CHECK(max_children >= 0)
);
CREATE TABLE skills (
  skill_id uuid PRIMARY KEY,
  name text NOT NULL,
  source_url text,
  source_commit text,
  license text,
  review_state text NOT NULL DEFAULT 'CANDIDATE'
);
CREATE TABLE agent_skills (
  agent_id uuid NOT NULL REFERENCES agents(agent_id),
  skill_id uuid NOT NULL REFERENCES skills(skill_id),
  PRIMARY KEY(agent_id, skill_id)
);
CREATE TABLE tasks (
  task_id uuid PRIMARY KEY,
  team_id uuid NOT NULL REFERENCES teams(team_id),
  parent_task_id uuid REFERENCES tasks(task_id),
  title text NOT NULL,
  state text NOT NULL CHECK (state IN ('PENDING','READY','RUNNING','REVIEW','DONE','FAILED','CANCELLED')),
  idempotency_key text UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE task_runs (
  run_id uuid PRIMARY KEY,
  task_id uuid NOT NULL REFERENCES tasks(task_id),
  agent_id uuid NOT NULL REFERENCES agents(agent_id),
  state text NOT NULL,
  started_at timestamptz,
  finished_at timestamptz,
  evidence_uri text
);
CREATE TABLE approval_requests (
  approval_id uuid PRIMARY KEY,
  action_type text NOT NULL,
  target_id text NOT NULL,
  state text NOT NULL CHECK (state IN ('PENDING','APPROVED','REJECTED','EXPIRED')),
  approver_id text,
  approved_at timestamptz
);
CREATE TABLE audit_events (
  event_id uuid PRIMARY KEY,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  actor_id text NOT NULL,
  action text NOT NULL,
  target_id text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb
);
```
Production schema requires migrations, RLS, indexes, cycle prevention, immutable audit storage, retention rules and security review. These DDL statements are a design starting point, not deployment-ready.

## Proposed API (versioned)
- GET /api/v1/entities/{canonical_id}
- GET /api/v1/entities/{canonical_id}/descendants
- POST /api/v1/teams/{team_id}/memberships
- POST /api/v1/tasks
- POST /api/v1/tasks/{task_id}/claim
- POST /api/v1/tasks/{task_id}/runs
- POST /api/v1/agents/{agent_id}/spawn-requests
- POST /api/v1/agents/{agent_id}/stop
- POST /api/v1/approvals
- GET /api/v1/tasks/{task_id}/evidence

## Enforcement
- Identity issuance: proposal → conflict scan → lineage verification → human approval → registry commit.
- Task run: authenticate → authorize scoped capability → quota check → lease task → sandbox execution → append audit → reviewer.
- Spawn: approval policy → max-depth/concurrency/budget check → runtime instance with no inherited secrets.
- Cross-team work: separate membership and permission checks for each team.
- Kill switch: revoke capabilities, stop queued and running jobs, preserve evidence.

## Acceptance tests
1. Same canonical entity joins three teams without new ID.
2. Membership revoked in one team does not alter unrelated memberships.
3. Parent agent cannot pass its production credentials to child.
4. Spawn beyond quota is denied and audited.
5. Parentage cycle is rejected.
6. Duplicate idempotency key does not duplicate execution.
7. Concurrent workers cannot claim the same lease.
8. Kill switch cancels jobs and preserves audit trail.
9. Unapproved ID issuance and production publication are denied.
10. Reviewer can reconstruct the task from evidence and source commit.

## Implementation sequence
P0: inspect existing CFP+ Core API, Registry, migrations, auth and tests; prepare compatibility map.
P1: additive schema + migration and policy tests in sandbox.
P2: task scheduler, leases, scoped runtime and evidence.
P3: multi-team agent tests and review PR.
P4: Human Governance decision; production remains HOLD until approved.

No claim is made that these services, tables or endpoints currently exist. Do not overwrite existing canonical structures.
