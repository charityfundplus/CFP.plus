# CMP Controlled Status Lifecycle

## Primary lifecycle

Draft → Assigned → Accepted → In Progress → Awaiting Evidence → Independent Review → Technical Review → Governance Review → Decision Recorded → Closed

## Additional controlled states

- Blocked
- Needs Revision
- Rejected
- Deferred
- Cancelled

## Transition controls

| From | To | Minimum requirement |
|---|---|---|
| Draft | Assigned | Scope, owner and acceptance criteria exist |
| Assigned | Accepted | Assignee acknowledges scope and session capability |
| Accepted | In Progress | Work begins at the assigned source |
| In Progress | Awaiting Evidence | Deliverables claimed and evidence requested |
| Awaiting Evidence | Independent Review | Evidence package passes completeness check |
| Independent Review | Technical Review | Findings and closure criteria are recorded |
| Technical Review | Governance Review | Technical gate result and unresolved risks are recorded |
| Governance Review | Decision Recorded | Decision authority records an explicit decision |
| Decision Recorded | Closed | Decision, artifacts and audit trail are linked |

## Re-entry loop

Any review gate may return the work to **Needs Revision**. CMP then:

1. records the reason;
2. assigns the corrective action;
3. preserves prior evidence;
4. requires new or updated evidence;
5. returns the work to the appropriate review gate.

## Automation constraints

CMP may automate routing, reminders, completeness checks, status synchronization and evidence indexing. CMP must not automatically:

- approve governance decisions;
- change locked Canonical IDs;
- declare Canonical Lock;
- merge protected work without Human Governance approval;
- fabricate missing evidence.
