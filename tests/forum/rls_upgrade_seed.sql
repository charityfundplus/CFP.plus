-- SEC-P0-195-03b • Dữ liệu "trước migration" cho rls_upgrade_check.sh: database đang ở 002 (chưa có 003, chưa có
-- review_round), có nhiệm vụ dở dang. Chạy bằng superuser trên database tạm (bị xoá sau khi kiểm tra).
-- Người dùng: 2 người giao việc (maintainer T2) • 3 người thực thi • 4 reviewer
\set ON_ERROR_STOP 1
begin;
insert into cfp_office.offices (canonical_id, display_name, platform, specialties, capabilities, limits, verification, created_by)
values ('T2', 'Văn Phòng nâng cấp', 'test', '', '', '', 'TEST', 2);
insert into cfp_office.office_maintainers (canonical_id, user_id) values ('T2', 2);
insert into cfp_office.super_pairs (id, canonical_id, software, software_key, lead_user_id, created_by)
values (9002, 'T2', 'test', 'test-9002', 3, 2);
-- L1: IN_REVIEW, đã có Review CHANGES_REQUESTED của vòng trước (lịch sử) • L2: IN_REVIEW, chưa có Review
-- L3: CHANGES_REQUESTED, có Review cũ • L4: ACCEPTED, có Review ACCEPT cũ
insert into cfp_office.tasks (id, pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values
  (9201, 9002, 'L1', '', 'x', 3, 4, 'IN_REVIEW',         'upg-L1', 2),
  (9202, 9002, 'L2', '', 'x', 3, 4, 'IN_REVIEW',         'upg-L2', 2),
  (9203, 9002, 'L3', '', 'x', 3, 4, 'CHANGES_REQUESTED', 'upg-L3', 2),
  (9204, 9002, 'L4', '', 'x', 3, 4, 'ACCEPTED',          'upg-L4', 2);
insert into cfp_office.evidence (task_id, kind, url, description, submitted_by) values
  (9201, 'URL', 'https://e/l1', 'l1', 3), (9202, 'URL', 'https://e/l2', 'l2', 3),
  (9203, 'URL', 'https://e/l3', 'l3', 3), (9204, 'URL', 'https://e/l4', 'l4', 3);
insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values
  (9201, 4, 'CHANGES_REQUESTED', 'lịch sử: vòng trước'),
  (9203, 4, 'CHANGES_REQUESTED', 'lịch sử'),
  (9204, 4, 'ACCEPT', 'lịch sử');
commit;
\echo seeded legacy tasks L1-L4 (pre-003)
