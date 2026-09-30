# CMP Orchestrator P0 Setup

## Purpose

This workflow lets CFP+ place a work item in the Notion CMP Work Queue and have GitHub Actions ask OpenAI to process it. The operational result and evidence are written back to the same Notion item for independent review and Human Governance.

## Security boundary

- Never store `OPENAI_API_KEY` or `NOTION_TOKEN` in a Notion page or database.
- Keep API credentials in GitHub Repository Secrets.
- Share only the required Notion pages and data sources with the Notion Integration.
- The orchestrator does not approve, lock, merge, or publish. Completed AI output moves to `Waiting for Review`.

## Required GitHub Repository Secrets

Already present:

- `NOTION_TOKEN`
- `OPENAI_API_KEY`

Add:

- `NOTION_WORK_QUEUE_ID`: the Notion **data source ID** for the CMP Work Queue. Use the data source ID, not a public page URL.

## Required Notion connection access

In Notion, open the CMP Work Queue database and choose:

`Share` → `Connections` → select the Integration associated with `NOTION_TOKEN`.

Grant read, insert, and update content capabilities. Also share related databases if relation properties are used.

Recommended scope:

1. CMP Foundation Working Set
2. CMP Implementation Blueprint P0
3. CMP Work Queue
4. AI Registry
5. Evidence Registry
6. Review Gate Log

## Minimum CMP Work Queue schema

Create or align these properties:

| Property | Type | Purpose |
| --- | --- | --- |
| `Name` | Title | Work Order name |
| `Status` | Status | Lifecycle state |
| `Prompt` | Rich text | Complete execution instruction |
| `Result` | Rich text | AI operational summary |
| `Evidence` | Rich text | Response ID, model, timestamp, execution source |

Required status options:

- `Assigned`
- `In Progress`
- `Waiting for Review`
- `Blocked`

If the existing database uses different names, configure GitHub Repository Variables instead of renaming the database:

- `CMP_TITLE_PROPERTY`
- `CMP_STATUS_PROPERTY`
- `CMP_PROMPT_PROPERTY`
- `CMP_RESULT_PROPERTY`
- `CMP_EVIDENCE_PROPERTY`
- `CMP_ASSIGNED_STATUS`
- `CMP_IN_PROGRESS_STATUS`
- `CMP_DONE_STATUS`
- `CMP_ERROR_STATUS`
- `OPENAI_MODEL`

## Activation

1. Merge the pull request containing this workflow.
2. Add `NOTION_WORK_QUEUE_ID` as a Repository Secret.
3. Confirm the Notion Integration has access to the CMP Work Queue.
4. Create one test Work Order with Status `Assigned`.
5. Run `CMP Orchestrator P0` manually with `dry_run=true`.
6. Run again with `dry_run=false` after the preflight succeeds.

After activation, the workflow checks the queue hourly and processes up to three assigned items per run.

## Governance behavior

The workflow enforces the following P0 boundary:

`Assigned → In Progress → Waiting for Review`

Errors move the item to `Blocked`. Human Governance remains responsible for decisions, Canonical Lock, publication, and exceptions.
