-- SEC-P0-195-03c • Test hồi quy tầng PostgreSQL: bất biến GHI (links, tasks, task_events, Closure) trong 003_office_rls.sql.
-- Bỏ qua FastAPI: mọi thao tác chạy bằng role office_app + set_config('cfp.user_id', …, true) như backend.
-- Chạy (superuser, sau setup_pg.sh): psql -v ON_ERROR_STOP=1 -d cfp_ci -f tests/forum/rls_write_invariants.sql
--
-- Cô lập: fixture + mọi ca chạy trong MỘT giao dịch và ROLLBACK ở cuối (kể cả vai trò governance của user 1).
-- Sequence (không rollback được) được chụp trước và đặt lại sau. Sau rollback, script so dấu vân tay toàn bộ
-- schema cfp_office với ảnh chụp trước khi chạy; lệch → lỗi.
--
-- Kết quả mong đợi của từng ca (cột want):
--   ok        câu lệnh thành công và tác động ĐÚNG 1 hàng
--   zero_rows không lỗi, 0 hàng — RLS ẩn hàng với người này (tách riêng với lỗi quyền)
--   priv      SQLSTATE 42501 "permission denied…"           — quyền theo cột (office_app chỉ UPDATE status, updated_at)
--   rls       SQLSTATE 42501 "…row-level security policy…"  — WITH CHECK của policy INSERT
--   actor     SQLSTATE 42501 "SEC-195-03b: …"               — trigger: sai người cho bước chuyển này
--   state     SQLSTATE 23514 "SEC-195-03b: …"               — trigger: sai trạng thái / thiếu Evidence / thiếu Review đúng vòng
-- Mọi kết quả khác ghi là other:<SQLSTATE> hoặc ok:<số hàng> và tính FAIL.
--
-- Người dùng: 1 governance • 2 người giao việc (maintainer T9) • 3 lead/người thực thi • 4 reviewer • 6 người ngoài
-- Tái hiện phát hiện C1, C1b, C2, G3, G4, G5 (phản biện RLS 003 @ a801627, PR #195) + đối chứng hợp lệ K1–K8
-- + D1–D7: task_events chỉ ghi khi có bước chuyển thật, mỗi bước đúng một lần (SEC-195-03d, token nội bộ).
-- Thứ tự: WITH CHECK của policy (task_event_ok) chạy trước → sự kiện giả báo 'rls'; token (AFTER INSERT) bắt ghi trùng → 'state'.
\set QUIET 1
\pset footer off
set client_min_messages = warning;

-- ---------- ảnh chụp trước khi chạy (ngoài giao dịch test)
create temp table cfp_test_seq_snapshot as
  select format('%I.%I', schemaname, sequencename) as seq, last_value, last_value is not null as called
  from pg_sequences where schemaname = 'cfp_office';
create temp view cfp_test_fingerprint as
  select md5(string_agg(tbl || '=' || digest, ',' order by tbl)) as fp from (
    select 'office_roles' as tbl, md5(coalesce(string_agg(t::text, '|' order by t::text), '')) as digest from cfp_office.office_roles t
    union all select 'offices',            md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.offices t
    union all select 'office_maintainers', md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.office_maintainers t
    union all select 'super_pairs',        md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.super_pairs t
    union all select 'tasks',              md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.tasks t
    union all select 'evidence',           md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.evidence t
    union all select 'reviews',            md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.reviews t
    union all select 'task_events',        md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.task_events t
    union all select 'audit_log',          md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.audit_log t
    union all select 'links',              md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.links t
    union all select 'datasets',           md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.datasets t
    union all select 'research_topics',    md5(coalesce(string_agg(t::text, '|' order by t::text), '')) from cfp_office.research_topics t
    union all select 'sequences', md5(coalesce(string_agg(format('%s:%s', sequencename, last_value), '|' order by sequencename), ''))
      from pg_sequences where schemaname = 'cfp_office'
    union all select 'schemas', md5(coalesce(string_agg(nspname, '|' order by nspname), ''))
      from pg_namespace where nspname like 'cfp_test%'
  ) x;
select fp as fp_before from cfp_test_fingerprint \gset

-- ================================================================ GIAO DỊCH TEST
begin;

\ir rls_test_lib.sql

-- ---------- fixture (superuser, bỏ qua RLS) — nằm trong giao dịch, bị rollback
insert into cfp_office.office_roles (user_id, role) values (1, 'governance'), (4, 'reviewer') on conflict do nothing;
insert into cfp_office.offices (canonical_id, display_name, platform, specialties, capabilities, limits, verification, created_by)
values ('T9', 'Văn Phòng 003c', 'test', '', '', '', 'TEST', 1);
insert into cfp_office.office_maintainers (canonical_id, user_id) values ('T9', 2);
insert into cfp_office.super_pairs (id, canonical_id, software, software_key, lead_user_id, created_by)
values (9901, 'T9', 'test', 'test-9901', 3, 2);
insert into cfp_office.tasks (id, pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values
  (9911, 9901, 'đang làm',               '', 'x', 3, 4, 'IN_PROGRESS', 'c3-9911', 2),
  (9916, 9901, 'chờ duyệt (luồng chuẩn)', '', 'x', 3, 4, 'IN_REVIEW',   'c3-9916', 2),
  (9917, 9901, 'ACCEPTED không Review',   '', 'x', 3, 4, 'ACCEPTED',    'c3-9917', 2),
  (9918, 9901, 'reviewer = thực thi',     '', 'x', 3, 3, 'ACCEPTED',    'c3-9918', 2);
insert into cfp_office.tasks (id, pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by, review_round)
values (9919, 9901, 'ACCEPT vòng cũ', '', 'x', 3, 4, 'ACCEPTED', 'c3-9919', 2, 2);
insert into cfp_office.evidence (task_id, kind, url, description, submitted_by) values (9916, 'URL', 'https://e/9916', 'e', 3);
insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9918, 3, 'ACCEPT', 'tự duyệt'), (9919, 4, 'ACCEPT', 'cũ');
update cfp_office.reviews set review_round = 1 where task_id = 9919;  -- Review thuộc vòng 1, nhiệm vụ đang vòng 2
insert into cfp_office.datasets (id, title, kind, url, author, version, source_url, access, chapter, created_by) values
  (9921, 'Tài liệu nội bộ của 6', 'document', 'https://e/noi-bo-6', 'x', 'v1', 'https://e/x', 'members', '6', 6),
  (9922, 'Tài liệu của 3',        'document', 'https://e/cua-3',    'x', 'v1', 'https://e/y', 'members', '6', 3),
  (9923, 'Tài liệu 6 cài vào',    'document', 'https://e/cai-vao',  'x', 'v1', 'https://e/z', 'members', '6', 6),
  (9924, 'Tài liệu công khai 6',  'document', 'https://e/cong-khai','x', 'v1', 'https://e/w', 'public',  '6', 6);
insert into cfp_office.research_topics (id, title, title_key, chapter, field, summary, created_by)
values (9931, 'Bài học của reviewer', 'c3-bai-hoc-4', '6', 'lesson', '', 4);

set local role office_app;
\o /dev/null

-- ---------- C1 / C1b: links INSERT phải kiểm cả hai đầu nhìn thấy được + quyền trên mục nguồn
select cfp_test.expect(3, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('task:9911', 'dataset:9921', 'uses', 3)$q$, 'rls', 'C1 người thực thi gắn tài liệu members của người khác vào nhiệm vụ mình');
select cfp_test.expect(3, $q$select 1 from cfp_office.datasets where id = 9921$q$, 'zero_rows', 'C1 hệ quả: người thực thi vẫn không đọc được tài liệu đó');
select cfp_test.expect(6, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('task:9911', 'dataset:9923', 'uses', 6)$q$, 'rls', 'C1b người ngoài cài tài liệu vào nhiệm vụ không thấy');
select cfp_test.expect(6, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('dataset:9923', 'task:9911', 'uses', 6)$q$, 'rls', 'C1c người ngoài nối tài liệu mình tới nhiệm vụ không thấy');
select cfp_test.expect(6, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('pair:9901', 'office:T9', 'works_in', 6)$q$, 'rls', 'C1d người ngoài tạo link từ Siêu Bộ Đôi không duy trì');
select cfp_test.expect(3, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('dataset:9921', 'office:T9', 'uses', 3)$q$, 'rls', 'C1e tạo link từ tài liệu của người khác');

-- ---------- C2 / G3 / G5: tasks INSERT phải đúng bất biến của create_task
select cfp_test.expect(2, $q$insert into cfp_office.tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values (9901, 'C2', '', 'x', 3, 3, 'ACCEPTED', 'c3-c2a', 2)$q$, 'rls', 'C2a tạo thẳng ACCEPTED, reviewer = người thực thi');
select cfp_test.expect(2, $q$insert into cfp_office.tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values (9901, 'C2', '', 'x', 3, 4, 'ACCEPTED', 'c3-c2b', 2)$q$, 'rls', 'C2b tạo thẳng ACCEPTED (reviewer hợp lệ)');
select cfp_test.expect(2, $q$insert into cfp_office.tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values (9901, 'C2', '', 'x', 3, 3, 'QUEUED', 'c3-c2c', 2)$q$, 'rls', 'C2c tạo QUEUED với reviewer = người thực thi');
select cfp_test.expect(2, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9917$q$, 'state', 'C2d Closure khi không có Review ACCEPT');
select cfp_test.expect(2, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9918$q$, 'state', 'C2e Closure khi reviewer = người thực thi');
select cfp_test.expect(2, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9919$q$, 'state', 'C2f Closure chỉ có Review ACCEPT của vòng cũ');
select cfp_test.expect(2, $q$insert into cfp_office.tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values (9901, 'G3', '', 'x', 6, 4, 'QUEUED', 'c3-g3', 2)$q$, 'rls', 'G3 giao cho người không phải lead của Siêu Bộ Đôi');
select cfp_test.expect(2, $q$insert into cfp_office.tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values (9901, 'G3b', '', 'x', 3, 6, 'QUEUED', 'c3-g3b', 2)$q$, 'rls', 'G3b reviewer không có vai trò reviewer/governance');
select cfp_test.expect(2, $q$insert into cfp_office.tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by, review_round) values (9901, 'G5', '', 'x', 3, 4, 'QUEUED', 'c3-g5', 2, 5)$q$, 'rls', 'G5 tự đặt review_round khi tạo');
select cfp_test.expect(6, $q$insert into cfp_office.tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values (9901, 'x', '', 'x', 3, 4, 'QUEUED', 'c3-out', 6)$q$, 'rls', 'G3c người ngoài giao việc');

-- ---------- G4: task_events INSERT phải khớp trạng thái thật
select cfp_test.expect(3, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 3, 'IN_REVIEW', 'ACCEPTED', 'giả')$q$, 'rls', 'G4 lịch sử giả IN_REVIEW → ACCEPTED khi đang IN_PROGRESS');
select cfp_test.expect(3, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 3, 'IN_PROGRESS', 'IN_REVIEW', 'giả')$q$, 'rls', 'G4b sự kiện chuyển chưa xảy ra');
select cfp_test.expect(4, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 4, 'ACKED', 'IN_PROGRESS', 'giả')$q$, 'rls', 'G4c reviewer ghi bước của người thực thi');
select cfp_test.expect(3, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 3, 'QUEUED', 'COMMENT', 'x')$q$, 'rls', 'G4d bình luận với trạng thái sai');
select cfp_test.expect(6, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 6, 'IN_PROGRESS', 'COMMENT', 'x')$q$, 'rls', 'G4e người ngoài bình luận');
select cfp_test.expect(3, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 3, null, 'QUEUED', 'x')$q$, 'rls', 'G4f sự kiện tạo giả khi nhiệm vụ không ở QUEUED');

-- ---------- đối chứng hợp lệ: các luồng app thật phải giữ nguyên
select cfp_test.expect(2, $q$insert into cfp_office.tasks (id, pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values (9915, 9901, 'K1', '', 'x', 3, 4, 'QUEUED', 'c3-k1', 2)$q$, 'ok', 'K1 maintainer tạo nhiệm vụ đúng chuẩn');
select cfp_test.expect(2, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9915, 2, null, 'QUEUED', '')$q$, 'ok', 'K1b sự kiện tạo QUEUED');
select cfp_test.expect(2, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9915, 2, null, 'QUEUED', '')$q$, 'state', 'D1 ghi trùng sự kiện tạo QUEUED');
select cfp_test.expect(2, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('task:9915', 'pair:9901', 'assigned_to', 2)$q$, 'ok', 'K1c link task → pair (assigned_to)');
select cfp_test.expect(1, $q$insert into cfp_office.tasks (pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values (9901, 'K1d', '', 'x', 3, 1, 'QUEUED', 'c3-k1d', 1)$q$, 'ok', 'K1d governance giao việc, reviewer governance');
select cfp_test.expect(3, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('task:9911', 'dataset:9922', 'uses', 3)$q$, 'ok', 'K2 gắn tài liệu của chính mình');
select cfp_test.expect(3, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('task:9911', 'dataset:9924', 'uses', 3)$q$, 'ok', 'K2b gắn tài liệu công khai');
select cfp_test.expect(1, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('task:9911', 'dataset:9921', 'uses', 1)$q$, 'ok', 'K2c governance gắn tài liệu members');
select cfp_test.expect(2, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('pair:9901', 'office:T9', 'works_in', 2)$q$, 'ok', 'K2d maintainer link pair → office');
select cfp_test.expect(3, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 3, 'IN_PROGRESS', 'COMMENT', 'x')$q$, 'ok', 'K3 người thực thi bình luận');
select cfp_test.expect(4, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 4, 'IN_PROGRESS', 'COMMENT', 'x')$q$, 'ok', 'K3b reviewer bình luận');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'ACKED' where id = 9915$q$, 'ok', 'K4 ACK');
select cfp_test.expect(3, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9915, 3, 'QUEUED', 'ACKED', '')$q$, 'ok', 'K5 sự kiện QUEUED → ACKED khớp thực tế');
select cfp_test.expect(3, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9915, 3, 'QUEUED', 'ACKED', '')$q$, 'state', 'D2 ghi trùng sự kiện QUEUED → ACKED');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9916, 4, 'ACCEPT', 'ok')$q$, 'ok', 'K6a reviewer ghi Review ACCEPT');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9916$q$, 'ok', 'K6b reviewer chuyển ACCEPTED');
select cfp_test.expect(4, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9916, 4, 'IN_REVIEW', 'ACCEPTED', '')$q$, 'ok', 'K6c sự kiện IN_REVIEW → ACCEPTED');
select cfp_test.expect(4, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9916, 4, 'IN_REVIEW', 'ACCEPTED', '')$q$, 'state', 'D3 ghi trùng sự kiện nghiệm thu');
select cfp_test.expect(2, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9916$q$, 'ok', 'K6d người giao việc Closure sau Review ACCEPT');
select cfp_test.expect(2, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9916, 2, 'ACCEPTED', 'CLOSED', '')$q$, 'ok', 'K6e sự kiện ACCEPTED → CLOSED');
select cfp_test.expect(2, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9916, 2, 'ACCEPTED', 'CLOSED', '')$q$, 'state', 'D4 ghi trùng sự kiện Closure');
select cfp_test.expect(3, $q$select cfp_office.issue_transition_token()$q$, 'priv', 'D5 office_app tự phát token (gọi hàm trigger)');
select cfp_test.expect(3, $q$insert into cfp_office.task_transition_tokens (task_id, from_status, to_status, actor_id) values (9911, 'IN_PROGRESS', 'IN_REVIEW', 3)$q$, 'priv', 'D6 office_app ghi thẳng bảng token');
select cfp_test.expect(3, $q$select 1 from cfp_office.task_transition_tokens limit 1$q$, 'priv', 'D7 office_app đọc bảng token');
select cfp_test.expect(3, $q$insert into cfp_office.task_events (task_id, actor_id, from_status, to_status, note) values (9911, 3, 'IN_PROGRESS', 'COMMENT', 'lần 2')$q$, 'ok', 'K3c bình luận lặp vẫn được (COMMENT không dùng token)');
select cfp_test.expect(4, $q$insert into cfp_office.links (from_ref, to_ref, relation, created_by) values ('task:9916', 'topic:9931', 'lesson', 4)$q$, 'ok', 'K7 reviewer ghi bài học (task → topic)');
select cfp_test.expect(3, $q$select 1 from cfp_office.datasets where id = 9922$q$, 'ok', 'K8 người thực thi đọc tài liệu của mình');
reset role;

\o
\unset QUIET
select n, case when want = got then 'PASS' else 'FAIL' end as kq, label, want, got,
       coalesce(sqlstate, '') as sqlstate, left(detail, 72) as detail
from cfp_test.results order by n;
\set QUIET 1
select count(*) filter (where want = got) as pass_count, count(*) filter (where want <> got) as fail_count
from cfp_test.results \gset

rollback;
-- ================================================================ HẾT GIAO DỊCH TEST

do $$ declare r record; begin  -- sequence không rollback → đặt lại như ảnh chụp
  for r in select * from cfp_test_seq_snapshot loop
    if r.called then perform setval(r.seq, r.last_value, true);
    else perform setval(r.seq, (select start_value from pg_sequences
                                where format('%I.%I', schemaname, sequencename) = r.seq), false);
    end if;
  end loop;
end $$;
select fp as fp_after from cfp_test_fingerprint \gset
select (:'fp_before' = :'fp_after') as rollback_clean \gset

\echo SEC195_03C pass=:pass_count fail=:fail_count rollback_clean=:rollback_clean
select set_config('cfp_test.fail', :'fail_count', false) as _f, set_config('cfp_test.clean', :'rollback_clean', false) as _c \gset
do $$ begin
  if current_setting('cfp_test.fail')::int > 0 then
    raise exception 'SEC-195-03c: % ca FAIL', current_setting('cfp_test.fail');
  end if;
  if not current_setting('cfp_test.clean')::boolean then
    raise exception 'SEC-195-03c: dữ liệu test còn sót sau rollback (dấu vân tay cfp_office lệch)';
  end if;
end $$;
