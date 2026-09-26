# OpenAI 2026 Integration for CFP+

Status: P0 implementation candidate
Date: 2026-09-26

## New OpenAI capabilities selected for immediate CFP+ use

### 1. Agents API
Use as the execution backbone for long-running CFP+ agents and subagents.

Initial CFP+ lanes:
- Global AI Directory agent
- Public Web publishing agent
- CTTTC daily-page agent
- Evidence verification agent
- Registry validator agent

Execution rule:
- Agent output is not treated as completed work until it returns an artifact, source, commit, page, or other Evidence.
- Stable IDs are never invented by an agent.
- Existing IDs and links are preserved.

### 2. Plugins
Use plugins as the external-system access layer instead of building custom integrations for every service.

Initial connected surfaces:
- GitHub
- Google Drive
- Vercel
- Notion where available through workspace tooling

CFP+ policy:
- Keep permissions least-privilege.
- Read and write capabilities must be recorded separately.
- External actions must retain audit evidence.

### 3. Voice with plugins
Use Voice for command and review workflows where supported.

CFP+ use:
- quick work-order creation
- status review
- evidence triage
- public-page review

Voice does not replace canonical written evidence.

### 4. ChatGPT Work
Use Work for long-running multi-step CFP+ jobs that need browser, files, apps, and artifact production.

Priority jobs:
- close PUBLIC WEB v0.1
- close GLOBAL AI DIRECTORY v1
- close CTTTC DAILY STANDARD v1

### 5. Data agent
Use for analytics after the public web and registry have measurable data.

CFP+ use:
- website traffic and conversion
- registry coverage
- missing Evidence counts
- country/developer/AI coverage
- TTTC, TMTC, TCTC reporting

### 6. GPT-6 Astra
Adopt only when available to the CFP+ workspace and only for tasks where the added capability materially improves execution.

Candidate tasks:
- repository-scale code and content review
- website reconstruction
- cross-file registry reconciliation
- complex multi-step publishing

## Immediate architecture

OpenAI/ChatGPT = coordinator
Agents API = execution runtime
Plugins = external-system access
Notion = Source of Truth
GitHub = canonical registry and change evidence
Vercel = deployable public web surface
CFP.plus = stable public gateway

## P0 Definition of Done

1. One Global AI Directory Public Index
2. One deployable CFP+ Public Web v0.1
3. One CTTTC MASTER DAY 20260820
4. Every automated job leaves Evidence
5. No parallel canonical architecture
