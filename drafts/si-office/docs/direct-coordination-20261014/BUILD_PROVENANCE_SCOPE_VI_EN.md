# Build → new task → export provenance / Scope for OpenSI

Owner: Codex build/evidence implementer. Existing PR124 only; b75b780 assessment baseline remains immutable. Development changes require independent human review.

The helper obtains Git HEAD and checks every tracked runtime file against Git object bytes. It emits a sorted SHA-256 Build Manifest. Untracked source, missing bytes, symlinks, changed source, missing Git or caller revision mismatch stay unverified. HTTP snapshots compare startup/current source; the preview launcher refuses arbitrary caller SHA. A packed release without the required Git object checkout cannot use this verification route; an approved release attestation route remains future work.

New P2 task runs capture startup/before/after source, actual taskKey, pairKey, subject/workspace, time and output hash into intent/completed checkpoints. Historical tasks are untouched. Injected adapter factories or source drift stay unverified. SQLite reopening and backup/restore retain receipts.

The UI export carries authenticated workspace, exact source manifest and retained task receipts. Worksheet independently reads Git source bytes, rejects forged task/subject/workspace/output bindings, and distinguishes three claims: sourceRevisionVerified (source bytes), taskReceiptBindingsVerified (structural/source/output linkage), taskExecutionRevisionVerified (false without independent authenticated execution-state attestation). Export checksum verifies payload bytes, not caller truth, identity or assessor authority. Local source-pinned flow receipt supplies actual synthetic handler execution and service audit readback for independent inspection; it is unsigned and not an external execution attestation.

No competency PASS, real grants or authority follow from these flags. The manifest excludes docs/tests and does not attest OS/Node binaries, external dependencies, loaded memory, hosting configuration or deployment. E1 separates baseline, mutable development head, execution SHA, manifest SHA, export payload SHA, unknown Standard v0.2 SHA and unknown authorized deployed Preview SHA. E3 assessor identity/grant/independence remains pending; E4 operational roster/grants remain pending.

VI: Giữ ba loại đối chiếu riêng: bytes nguồn; liên kết receipt/task/output; xác nhận thực thi độc lập. Không đổi nhãn checksum thành bằng chứng quyền, danh tính hoặc năng lực. Không nâng task lịch sử thành execution có provenance khi chưa có receipt thực.
