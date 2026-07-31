# CFP+

**Only Plus+ For Life**

## GitHub Hub

[CFP+ GitHub Hub • Điểm truy cập trung tâm](GITHUB_HUB.md)

## Trạng thái

Baseline Candidate

## Ngôn ngữ chuẩn

Tiếng Việt là Canonical Language của CFP+.

## Mục đích của repository

Repository công khai dành cho tài liệu, review độc lập, evidence, governance decision và lịch sử thay đổi.

## Điểm truy cập AI

[AI_INDEX • Chỉ mục AI và Canonical Link công khai](AI_INDEX.md)

## Tài liệu nền tảng

[69 • CFP+ Global AI Country Hub Registry](registry/AI_CANONICAL_ID_REGISTRY.md)

[6911 • United States AI Hub](registry/6911.md)

[6984 • Vietnam AI Hub](registry/6984.md)

[Website Master Map](website/WEBSITE_MASTER_MAP_VI.md)

[Public ID Registry 00 đến 99](website/PUBLIC_ID_REGISTRY_00_99_VI.md)

[Locked Documents Registry](governance/LOCKED_DOCUMENTS_REGISTRY_VI.md)

[Open Review Workflow](governance/OPEN_REVIEW_WORKFLOW_VI.md)

## OpenAI Registry Review Workflow

Repository now includes a GitHub Actions workflow at `.github/workflows/openai-registry-review.yml` and a validator at `scripts/validate_registry.py` to review `registry/` records, generate JSON/Markdown reports, and optionally comment on pull requests.

### Required secret

Configure `OPENAI_API_KEY` in **Settings → Secrets and variables → Actions → New repository secret** before enabling OpenAI-assisted review.

### Governance guardrails

- Review and reporting only; no automatic Canonical ID rewrites.
- No automatic merge or pull request mutation.
- Human Governance must approve any follow-up change.

