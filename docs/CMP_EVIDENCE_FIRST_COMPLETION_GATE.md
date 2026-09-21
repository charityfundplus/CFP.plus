# CMP Evidence-First Completion Gate • P0

Status: REVIEW CANDIDATE • EFFECTIVE IMMEDIATELY FOR CMP OPERATIONS

## Core rule

No CFP+ task is counted as COMPLETE unless there is verifiable execution evidence.

Statements such as "received", "working", "done", "sent", "published", or "updated" are not sufficient by themselves.

## Required evidence by work type

### Email
COMPLETE only when there is real outbound/inbound evidence as applicable, such as:
- Sent record
- Gmail Message ID or equivalent provider evidence
- Recipient
- Subject
- Send timestamp
- Reply thread / response evidence when the task includes follow-up

### GitHub
COMPLETE only when there is a concrete repository artifact, such as:
- Commit SHA
- Pull Request
- Issue update
- File path and changed content
- CI/workflow evidence where required

### Website
COMPLETE only when there is public execution evidence, such as:
- Published route
- Public URL
- HTTP/public access verification
- Correct routing to the intended canonical page

A planned route, registry entry, or local artifact is not equivalent to a live website route.

### Registry / Canonical ID
COMPLETE only when there is a concrete record with the required fields and governance status.

For Canonical ID work:
- ID and Canonical Link may exist before content.
- Empty ID slots are valid where the architecture authorizes them.
- Entity content must not cause renumbering of an already allocated ID.
- No AI may self-create a Canonical ID outside an authorized numeric skeleton.
- Canonical Lock remains a Human Governance decision.

### AI Research / Review
COMPLETE only when the AI returns a usable artifact, dataset, table, review record, evidence package, or other inspectable output.

A message saying that the task was understood or accepted is ASSIGNED / ACKNOWLEDGED, not COMPLETE.

## Standard execution states

Use these states consistently:

- ASSIGNED
- ACKNOWLEDGED
- IN PROGRESS
- OUTPUT RECEIVED
- EVIDENCE VERIFIED
- COMPLETE
- BLOCKED
- REVIEW REQUIRED
- NOT VERIFIED

`COMPLETE` requires `EVIDENCE VERIFIED` unless an explicit Human Governance exception is recorded.

## Multi-AI operating rule

Each AI may research, review, draft, classify, or propose within its assigned scope, but CMP must distinguish between:

1. AI-produced content or recommendation; and
2. real-world execution.

Examples:
- Gemini drafting an email is not evidence that the email was sent.
- A proposed `cfp.plus/<ID>` URL is not evidence that the route is live.
- A claimed registry change is not evidence unless the file/record exists.

## Email operations rule

Until an AI has verified Gmail/API execution capability, it must not be labeled as an active outbound email operator.

Preferred execution chain when available:

`CHECK HISTORY → DUPLICATE CHECK → DRAFT/REVIEW → CMP VALIDATE → SEND → MESSAGE ID → EVIDENCE LOG → WAIT RESPONSE`

## Governance boundary

Evidence verification does not itself grant Governance Approval or Canonical Lock.

Human Governance retains authority over:
- Canonical ID allocation where reserved
- Canonical Lock
- exceptional external commitments
- changes that exceed established delegated scope

## Effective rule

From this record forward, CFP+/CMP reports must distinguish clearly between:

- planned
- assigned
- acknowledged
- output produced
- executed
- evidence verified
- complete

The objective is to eliminate false completion and reduce repeated manual checking by the Founder.
