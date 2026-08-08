# CFP+ AI Review Automation

**Status:** Review Candidate  
**Authority:** Human Governance  
**Canonical placement:** HUB 69 → CMP → GitHub Collaboration

## Purpose

This automation lets connected AI providers review GitHub Issues and post one consolidated evidence-first report back to the same Issue.

GitHub remains the public collaboration and audit layer. Notion remains the drafting and source-of-truth workspace where designated. Google Drive remains the working-file and evidence workspace.

## Trigger

The workflow runs when:

1. an Issue receives the label `ai-review`; or
2. a maintainer manually runs **CFP+ Multi-AI Review Orchestrator** and supplies an Issue number.

## Required secrets

Configure only the providers CFP+ intends to use:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `XAI_API_KEY`

A missing provider secret is reported as `SKIPPED`; it does not stop other reviewers.

Optional repository variables:

- `OPENAI_MODEL`
- `ANTHROPIC_MODEL`
- `GEMINI_MODEL`
- `XAI_MODEL`

## Review classifications

Every material finding must use exactly one classification:

- `VERIFIED`
- `EVIDENCE_REQUIRED`
- `BROKEN`
- `OUTDATED`

## Governance safeguards

- AI reviewers must not assign, invent, renumber, or modify Canonical IDs.
- AI responses are evidence input, not final authority.
- Merge, Canonical Lock, ID allocation, and final decisions require explicit Human Governance approval.
- The workflow has `contents: read` and `issues: write`; it cannot modify repository files or merge Pull Requests.
- Provider failures are isolated so one provider cannot block the others.

## Public link checking

The separate **CFP+ Public Link Check** workflow scans Markdown and HTML links:

- on Pull Requests;
- after changes reach `main`;
- every Monday;
- when manually requested.

When a scheduled or `main` run fails, the workflow opens or updates one GitHub Issue classified as `BROKEN`.

## Recommended operating sequence

1. Create the review Issue using the CFP+ AI Review template.
2. Include public links and an evidence package. Never place secrets in an Issue.
3. Apply the `ai-review` label.
4. Review the consolidated AI report.
5. Resolve conflicts using evidence.
6. Human Governance records the final decision.
7. Changes proceed through a Pull Request; no automated Canonical Lock is permitted.

## Current limitation

External AI APIs can analyze the Issue content and publicly accessible links only to the extent supported by each provider and its account configuration. Private Notion or Google Drive content must be exported, linked with appropriate access, or synchronized into GitHub through a separately authorized workflow.
