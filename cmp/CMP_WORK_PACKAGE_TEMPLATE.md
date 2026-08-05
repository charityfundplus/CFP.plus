# CMP Work Package Template — Independent AI Review

**Version:** 1.0  
**Authority:** CFP+ Human Governance  
**Canonical Path:** HUB 69 → CMP  
**Coordination Issue:** [#43](https://github.com/charityfundplus/CFP.plus/issues/43)

## 1 • Canonical Inputs

Reviewers must use the current repository versions of these sources:

| Source | Location | Governance Status |
|---|---|---|
| HUB 69 | [HUB69.md](../HUB69.md) | Canonical Locked interpretation baseline |
| CMP | [CMP.md](../CMP.md) | Coordination layer reference |
| Global AI ID Baseline Candidate | [GLOBAL_AI_ID_BASELINE_CANDIDATE.md](../registry/GLOBAL_AI_ID_BASELINE_CANDIDATE.md) | Review Candidate |
| AI Canonical ID Registry | [AI_CANONICAL_ID_REGISTRY.md](../registry/AI_CANONICAL_ID_REGISTRY.md) | Registry reference |
| Full Country & AI Registry | [Notion working source](https://app.notion.com/p/bcaf748f4ad6413da64672277628c9ce?pvs=1) | Working / review source |

### Locked Interpretation Rules

1. HUB 69 is the only canonical gateway.
2. Country Canonical ID is the country identity basis; it does not itself imply a political or administrative parent-child relationship.
3. AI Country ID = prefix `6` + the complete Country Canonical ID.
4. Required path: HUB 69 → AI Country ID → Developer → AI Family → AI → Canonical Link.
5. One Entity = One Canonical ID = One Canonical Link.
6. No temporary IDs, silent changes, or reuse of an existing ID.
7. Every discrepancy must be recorded as a Finding with Evidence.
8. CFP+ Human Governance alone approves changes and Canonical Lock.

A reviewer may challenge a locked rule only through a documented governance escalation. The reviewer must not apply an alternative numbering architecture.

## 2 • Work Order

CMP completes this table before assignment.

| Field | Value |
|---|---|
| AI Canonical ID | [ID] |
| AI Name | [Name] |
| Work Order ID | [ID] |
| Canonical Profile | [Repository path] |
| Review Issue | [#33–#42 or approved replacement] |
| Primary Scope | [Scope] |
| Records or ranges assigned | [IDs / files / full candidate] |
| Input snapshot date or commit | [YYYY-MM-DD / SHA] |
| Submission target | [Issue comment / attached document] |
| Due date, if explicitly approved | [YYYY-MM-DD / None] |
| Escalation route | Issue #43 / Human Governance |

Do not invent a deadline. A date is binding only when CMP or Human Governance explicitly records it.

## 3 • Scope Catalogue

Assign one primary scope and any explicitly approved secondary scope.

- **Implementation & Completeness:** candidate coverage, missing records, count reconciliation.
- **Governance & Lineage:** Country → Developer → AI relationships and governance compliance.
- **Collision & Extensibility:** duplicate IDs, full-ID collisions, ambiguous allocation, future expansion risk.
- **Validation & Duplication:** reproducible uniqueness and consistency checks.
- **Reference Consolidation:** source quality, missing metadata, evidence traceability.
- **Independent Global Coverage:** broad independent sample or full-candidate review.
- **Repository & Link Integrity:** repository paths, Canonical Links, redirects, target-content relevance.
- **Evidence & Attribution:** primary-source verification, developer identity and country attribution.
- **Infrastructure Classification:** supported classification using an approved taxonomy; do not invent governance categories.
- **Regional Coverage:** deep review of an assigned region, country group, or community.

### Scope Boundary

A reviewer may report an out-of-scope critical issue, but must mark it **Referral / Escalation** rather than silently expanding the assignment.

## 4 • Required Deliverables

Submit one review result containing:

1. **Executive Summary** — records reviewed, method, limitations, and overall result.
2. **Findings** — one standardized entry per discrepancy.
3. **Evidence Summary** — sources, verification dates, and methods.
4. **Recommendations** — precise proposed actions.
5. **Missing Coverage** — records or evidence that could not be assessed.
6. **Closure Criteria** — objective conditions for resolution.
7. **Final Result** — PASS / PASS WITH CHANGES / FAIL.

A PASS means no material issue was found within the reviewed scope and evidence available. It does not grant Canonical Lock.

## 5 • Standard Finding Format

```markdown
### Finding [FINDING-ID]

- **Reviewer:** [AI Canonical ID — Name]
- **Work Order:** [ID]
- **Related Canonical ID(s):** [IDs]
- **Category:** [Duplicate / Missing Coverage / Collision / Metadata / Evidence / Link Integrity / Lineage / Governance / Other]
- **Severity:** [CRITICAL / HIGH / MEDIUM / LOW]
- **Confidence:** [HIGH / MEDIUM / LOW / UNVERIFIED]

#### Current Content
[Exact current value, file, section, row, or link.]

#### Problem
[Why the content is incorrect, incomplete, ambiguous, or unsupported.]

#### Proposed Correction
[Specific correction, documentation change, validation step, or governance escalation.]

#### Evidence
| Source | Reference | Verified Date | Method | Supports Which Claim |
|---|---|---|---|---|
| [Source] | [URL/path] | [YYYY-MM-DD] | [Method] | [Claim] |

#### Impact
- Data integrity: [None/Low/Medium/High]
- Canonical Lock impact: [Yes/No/Conditional]
- Locked-rule impact: [Rule number or None]

#### Closure Criteria
- [ ] [Objective condition]
- [ ] Evidence or decision record linked
- [ ] Approved remediation merged, when a repository change is required

#### Reviewer Notes
[Uncertainty, limitations, or alternative interpretation.]
```

### Finding ID Convention

Use a stable reviewer prefix and sequence, for example `GPT-001`, `CLA-001`, or `GEM-001`. Do not use a Work Order ID as a Finding ID and do not renumber a finding after submission.

## 6 • Severity Standard

- **CRITICAL:** corruption, duplicate full Canonical ID assigned to different entities, or a condition that makes safe interpretation impossible.
- **HIGH:** material lineage, governance, identity, or evidence failure that blocks approval unless dispositioned.
- **MEDIUM:** substantive data-quality problem that requires correction but does not independently invalidate the architecture.
- **LOW:** documentation, formatting, naming, or minor metadata problem with limited operational impact.

Severity is about impact, not reviewer confidence. Record confidence separately.

## 7 • Evidence Standard

Valid evidence should be:

- directly relevant to the claim;
- publicly accessible or preserved as an approved snapshot;
- traceable to a date, commit, document version, or retrieval date;
- authoritative, preferably an official primary source;
- reproducible by another reviewer where reasonably possible.

### Important Distinctions

Do not treat the following as equivalent:

- developer country or legal domicile;
- AI product availability;
- telecommunications calling code;
- product language coverage;
- hosting or infrastructure location;
- ownership, partnership, investment, or distribution relationship.

An HTTP response alone does not prove the content supports the claim. Redirects are not automatically failures; verify the final authoritative target and record the redirect when material.

### Evidence Confidence

- **HIGH:** authoritative source directly supports the claim, or multiple strong sources converge.
- **MEDIUM:** credible source supports the main claim but a material detail remains uncertain.
- **LOW:** limited or indirect evidence.
- **UNVERIFIED:** evidence could not be independently accessed or matched.

Locked governance rules are authority references, not an evidence-confidence level.

## 8 • Governance Boundary

### Reviewers May

- identify duplicates, omissions, metadata gaps, broken references, and lineage conflicts;
- verify evidence and document uncertainty;
- recommend remediation;
- request Human Governance clarification;
- propose validation rules without declaring them locked.

### Reviewers May Not

- declare Canonical Lock;
- silently reassign, reuse, or create temporary IDs;
- replace the HUB 69 architecture with another system;
- treat their own review as Human Governance approval;
- infer unsupported facts from names, prefixes, or product availability;
- mark another review complete without a submitted result or recorded disposition.

### Governance Escalation

When a finding requires policy interpretation or conflicts with a locked rule:

1. mark it **Governance Decision Required**;
2. provide competing interpretations and evidence;
3. state the operational impact of each option;
4. link the finding in Issue #43;
5. await a written Human Governance decision before remediation.

## 9 • Access Fallback

If a reviewer cannot access GitHub or Notion, CMP provides a dated Review Package containing:

- HUB 69 and CMP snapshots;
- the registry candidate snapshot;
- assigned profile files or record ranges;
- the Finding template;
- the source commit SHA or export date;
- instructions for returning the result.

The reviewer must state:

```text
Review conducted using CMP fallback package dated [YYYY-MM-DD], source [commit/export identifier].
```

If the reviewer cannot post directly, CMP may post the result on the reviewer’s behalf, clearly identifying the original reviewer, delivery method, and receipt date. Do not invent an email address or private contact channel.

## 10 • Conflict and Independence Rules

- Each reviewer performs an independent assessment within the assigned scope.
- Reviewers may read canonical inputs and earlier governance decisions.
- Reviewers should not copy another reviewer’s conclusion without independent verification.
- Conflicting conclusions must remain visible until resolved through evidence comparison and Human Governance disposition.
- The existence of disagreement does not automatically mean either reviewer failed.

## 11 • Submission Structure

```markdown
# [AI NAME] — [WORK ORDER] Review Result

**Reviewer:** [Canonical ID]
**Input version:** [commit SHA / snapshot date]
**Scope reviewed:** [scope]
**Limitations:** [none or list]
**Final Result:** PASS / PASS WITH CHANGES / FAIL

## Executive Summary
[Summary]

## Findings
[Standard findings]

## Findings Summary
| Finding ID | Category | Severity | Canonical ID(s) | Recommendation |
|---|---|---|---|---|

## Evidence Summary
[Sources and methods]

## Missing Coverage
[Unreviewed or unverifiable content]

## Recommendations
[Actions]

## Closure Criteria
- [ ] [Condition]

**Submitted:** [YYYY-MM-DD]
```

## 12 • Submission Checklist

- [ ] Assigned scope and input version are stated.
- [ ] Every finding has a stable Finding ID.
- [ ] Severity and confidence are recorded separately.
- [ ] Evidence supports the exact claim.
- [ ] Missing or inaccessible evidence is disclosed.
- [ ] Recommendations do not silently change locked rules.
- [ ] Governance escalations are clearly marked.
- [ ] Closure criteria are objective.
- [ ] Overall result is included.
- [ ] Reviewer Canonical ID and submission date are included.

## 13 • Process After Submission

1. CMP records the result in the assigned Issue.
2. Issue #43 tracks review status and consolidates findings.
3. Conflicts are compared and escalated when needed.
4. Approved remediation is implemented through a traceable Pull Request.
5. CFP+ Human Governance reviews the evidence and changes.
6. Merge and Canonical Lock remain separate decisions.
7. One Canonical Public Link is published only after Canonical Lock.

**Template Version:** 1.0  
**Effective Date:** 2026-08-05  
**Final Decision Authority:** CFP+ Human Governance

**Only Plus+ For Life**