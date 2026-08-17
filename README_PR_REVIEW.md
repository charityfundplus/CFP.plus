# Claude Independent PR Review

The workflow `.github/workflows/claude_pr_review.yml` runs `scripts/pr_review.py` for same-repository pull requests. It retrieves the PR diff through the GitHub REST API, filters governance-relevant files, sends bounded chunks to Claude, and creates or updates one PR comment.

## Required secret

- `ANTHROPIC_API_KEY`: Anthropic API key stored as a GitHub Actions repository secret.

`GITHUB_TOKEN` is provided automatically by GitHub Actions. The workflow requests read-only repository content access and permission to write PR comments. It does not merge, modify repository files, or approve governance.

## Optional environment settings

- `ANTHROPIC_MODEL`
- `PR_REVIEW_TIMEOUT_SECONDS`
- `PR_REVIEW_MAX_RETRIES`
- `PR_REVIEW_CHUNK_CHARS`
- `PR_REVIEW_MAX_TOTAL_CHARS`

## Local checks

```bash
python -m py_compile scripts/pr_review.py
python -m unittest discover -s tests -p 'test_*.py' -v
```
