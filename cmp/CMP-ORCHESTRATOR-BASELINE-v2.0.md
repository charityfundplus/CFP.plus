# CFP+ CMP Orchestrator Baseline v2.0

**Status:** Review Candidate  
**Placement:** Inside HUB 69  
**Decision Authority:** Human Governance

## Canonical definition

CMP is the central collaboration and orchestration layer inside HUB 69. It coordinates the complete work lifecycle between people, AI systems and authorized platforms.

## Core modules

1. Work Queue Center
2. Assignment Engine
3. AI Coordination Center
4. Platform Coordination Center
5. Evidence Center
6. Review Aggregator
7. Status and Escalation Center
8. Governance Gateway
9. Audit and Traceability Center
10. Knowledge Synchronization Center
11. Automation Center

## Controlled lifecycle

Draft → Assigned → Accepted → In Progress → Awaiting Evidence → Independent Review → Technical Review → Governance Review → Decision Recorded → Closed

Additional states: Blocked, Needs Revision, Rejected, Deferred, Cancelled.

## Reporting standard

Every actor reports:

1. Configured Connector Capability
2. Session Capability
3. Implementation Status
4. Verified Evidence
5. Governance Status
6. Decision Authority

## Review format

Finding → Evidence → Recommendation → Closure Criteria

## Validation outcomes

PASS, PASS WITH CHANGES, FAIL, MISSING MAPPING, UNKNOWN, CONFLICT, OUT OF SCOPE.

Validators must not infer or alter Canonical IDs.

## Automation boundary

CMP may automate routing, reminders, completeness checks, evidence indexing, status synchronization and report generation.

CMP may not automatically approve governance gates, change locked architecture, alter Canonical IDs, declare Canonical Lock, fabricate evidence or merge protected changes without authorization.

## Minimum operational release

- Unified Work Queue
- Work Order template and schema
- Evidence Package template and schema
- AI Assignment Matrix
- Controlled lifecycle
- Review at Source references
- Governance Decision Package
- Audit Log
- One end-to-end pilot Work Order

## Acceptance gates

The baseline advances only after a complete pilot, verified evidence handling, conflict handling, Technical Review and an explicit Human Governance decision.
