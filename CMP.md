# CMP — CFP+ Coordination & Collaboration Management Platform

**Public Central Gateway**  
**Placement:** Inside HUB 69  
**Architecture Status:** Published  
**Baseline Status:** v2.0 Review Candidate  
**Pilot Status:** In Progress  
**Production Status:** Pending Technical Review and Human Governance

> CMP is the central coordination and collaboration orchestration layer inside HUB 69. It coordinates the complete work lifecycle between Human Governance, people, AI systems, GitHub, Notion and authorized evidence sources. CMP is not a second HUB and does not replace Human Governance.

## Public and internal sources

- **Public canonical reference:** this GitHub document and the [`cmp/`](cmp/) package
- **Notion working source:** [CMP Central Gateway](https://app.notion.com/p/3b3caac9a557819e8ee8e0aa4d0260fc)
- **Active orchestration issue:** [Issue #53](https://github.com/charityfundplus/CFP.plus/issues/53)
- **Current pilot Work Order:** [Issue #46](https://github.com/charityfundplus/CFP.plus/issues/46)

GitHub is the public and broadly accessible reference. Notion remains a working and coordination source where access is available. No participant is required to have Notion access in order to review CMP.

## 1. Position inside HUB 69

- **HUB 69:** the single global gateway, positioning and navigation layer for CFP+.
- **CMP:** the central orchestrator for collaboration and the complete work lifecycle.
- **AI Collaboration Directory:** positions developers, Primary Collaboration Entries, Canonical IDs and Canonical Links.
- **Human Governance:** retains final decision authority.

## 2. CMP objectives

CMP is designed to:

- convert goals into structured Work Orders;
- select appropriate AI reviewers according to task type, capability and session permissions;
- coordinate Review at Source on Issues, Pull Requests and Canonical Links;
- collect and validate Evidence Packages;
- preserve conflicting reviews and escalate them rather than silently reconcile them;
- prepare Governance Decision Packages;
- maintain audit history and feedback loops until controlled closure;
- expand to additional AI systems without changing the established architecture.

## 3. Core modules

1. Work Queue Center
2. Assignment Engine
3. AI Collaboration Directory
4. Evidence Center
5. Review Center and Review Aggregator
6. Status Center
7. Governance Gateway
8. Audit and History
9. Knowledge Synchronization
10. Automation Center
11. Conflict and Exception Manager

## 4. Controlled lifecycle

`Draft → Assigned → Accepted → Implementing → Awaiting Evidence → Reviewing → Technical Review → Governance Review → Decision Recorded → Closed`

Additional controlled states include `Blocked`, `Needs Revision`, `Rejected`, `Deferred` and `Cancelled`.

### Transition discipline

- No Technical Review without the minimum Evidence Package.
- No Governance Review while material findings lack Closure Criteria.
- No Closed status without a Decision Record or an authorized closure reason.
- Missing evidence is never inferred or fabricated.

## 5. CFP+ AI Reporting Standard v1.0

Every AI report must separate:

1. Configured Connector Capability
2. Session Capability
3. Implementation Status
4. Verified Evidence
5. Governance Status
6. Decision Authority

**Core rule:** plans, assumptions and capabilities must never be presented as verified execution evidence.

## 6. Independent Review Standard

Every Independent Review uses:

- Finding
- Evidence
- Recommendation
- Closure Criteria

Reviews should be recorded directly at the official source whenever the execution environment supports it.

## 7. Evidence and exception states

- `MISSING_EVIDENCE` — a claim exists without sufficient verified evidence.
- `MISSING_MAPPING` — a required mapping element is absent; IDs must not be inferred or changed.
- `CONFLICT` — two or more evidence sources or reviews conflict; preserve and escalate.
- `UNKNOWN` — evidence is insufficient for a conclusion.
- `OUT_OF_SCOPE` — the item is outside the Work Order.

## 8. AI Collaboration Directory

Principle: **One Developer → One Collaboration Entry → Many AI Platforms**.

- 69110 — OpenAI / ChatGPT
- 69111 — Anthropic / Claude
- 69112 — xAI / Grok
- 69113 — Google / Gemini
- 69114 — Meta / Meta AI
- 69115 — Microsoft / Microsoft Copilot
- 69116 — Perplexity / Perplexity
- 69117 — Groq / Groq
- 69118 — CoreWeave / CoreWeave AI Platform
- 69119 — Apple / Apple Intelligence

New AI products are added inside the existing developer entry under the principle **Expansion Without Structural Change**.

## 9. Public CMP package

- [CMP overview](cmp/OVERVIEW.md)
- [CMP Orchestrator Baseline v2.0](cmp/CMP-ORCHESTRATOR-BASELINE-v2.0.md)
- [Work Order Template](cmp/WORK-ORDER-TEMPLATE.md)
- [Evidence Package Template](cmp/EVIDENCE-PACKAGE-TEMPLATE.md)
- [AI Assignment Matrix](cmp/AI-ASSIGNMENT-MATRIX.md)
- [Status Lifecycle](cmp/STATUS-LIFECYCLE.md)
- [Governance Decision Package](cmp/GOVERNANCE-DECISION-PACKAGE.md)
- [Pilot Work Order — Issue #46](cmp/PILOT-WO-001-ISSUE-46.md)
- [Public Document Index](cmp/PUBLIC-DOCUMENT-INDEX.md)

## 10. Current pilot

**Pilot Work Order:** Issue #46  
**Coordinator:** CMP through Issue #53  
**Current status:** `ASSIGNED — AWAITING VERIFIED IMPLEMENTATION`

Required evidence:

- branch link;
- Draft Pull Request;
- commit SHA;
- file inventory;
- actual folder structure;
- mobile and desktop screenshots;
- route validation;
- link validation.

CMP Pilot Watch checks Issues #46 and #53 periodically and reports only meaningful new evidence, blockers, conflicts or gate readiness.

## 11. Publication status

| Layer | Status |
|---|---|
| Architecture | Published |
| Baseline v2.0 | Review Candidate |
| Pilot | In Progress |
| Production | Pending Technical Review and Human Governance |

## 12. Production gate

CMP may advance to Production only after:

- at least one Work Order completes the full lifecycle to Decision Recorded;
- all evidence references are accessible and verified;
- conflicts are preserved, classified and escalated;
- the Audit Log is complete;
- Technical Review records PASS or PASS WITH CHANGES with an accepted closure plan;
- Human Governance explicitly approves the Production Baseline.

## 13. Historical and working references

The Notion CMP Central Gateway indexes the earlier CMP definitions, charter, foundation decision, working set, collaboration standards, workflow, roadmap, taxonomy, platform constitution and coordination summaries. These remain historical or working references; this GitHub page is the public consolidated entry.

---

**Không Của Riêng Ai 🤖**  
**Only Plus+ For Life**  
**Không Gì Không Thể**