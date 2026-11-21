# Office sandbox overlay and scoped task readback

Base PR195 commit 287ce647aff410af912a85aea695e89ceb2fe868. Hash-pinned ephemeral-only fixtures, source/work_order_code retained in existing events, authenticated SUPER_SOFTWARE record filtering, and normalization of optional fields for old idempotency audit records.

Windows verification: 52 passed, 13 PostgreSQL tests skipped. Dispatcher integration and the three-SBD pilot use companion branch codex/hub69-windows-sandbox-20261121. SI_AI has no independent persisted record in this schema and returns 404 in the scoped endpoint. Canonical resolver conflict remains for separate review.

Rollback: stop the sandbox server and revert this commit or return to the base commit. Keep SQLite state and logs for audit. No schema migration or Registry file change.

Publication status: LOCAL REVIEW COMMIT ONLY. Automatic approval rejected a remote commit because prior instructions prohibit push. GitHub publication and independent Claude retest are pending user approval. Local commit metadata uses Codex Sandbox <codex-sandbox@localhost>; no global Git settings changed.
