-- SEC-P0-195-03b • Test hồi quy tầng PostgreSQL: máy trạng thái nhiệm vụ + vòng duyệt trong 003_office_rls.sql.
-- Bỏ qua FastAPI: mọi thao tác chạy bằng role office_app + set_config('cfp.user_id', …, true) như backend.
-- Chạy (superuser, sau setup_pg.sh): psql -v ON_ERROR_STOP=1 -d cfp_ci -f tests/forum/rls_task_transitions.sql
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
-- Người dùng: 1 governance • 2 người giao việc (maintainer T1) • 3 người thực thi • 4 reviewer • 5 người ngoài
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
    union all select 'sequences', md5(coalesce(string_agg(format('%s:%s', sequencename, last_value), '|' order by sequencename), ''))
      from pg_sequences where schemaname = 'cfp_office'
    union all select 'schemas', md5(coalesce(string_agg(nspname, '|' order by nspname), ''))
      from pg_namespace where nspname like 'cfp_test%'
  ) x;
select fp as fp_before from cfp_test_fingerprint \gset

-- ================================================================ GIAO DỊCH TEST
begin;

create schema cfp_test;
create table cfp_test.results (n serial, label text, want text, got text, sqlstate text, detail text);
grant usage on schema cfp_test to office_app;
grant insert, select on cfp_test.results to office_app;
grant usage on sequence cfp_test.results_n_seq to office_app;
grant usage on schema cfp_test to cfp_migrator;  -- E1 ghi kết quả dưới role cfp_migrator
grant insert, select on cfp_test.results to cfp_migrator;
grant usage on sequence cfp_test.results_n_seq to cfp_migrator;

create function cfp_test.classify(st text, msg text) returns text language sql immutable as $$
  select case
    when st = '42501' and msg like 'permission denied%' then 'priv'
    when st = '42501' and msg like '%row-level security policy%' then 'rls'
    when st = '42501' and msg like 'SEC-195-03b:%' then 'actor'
    when st = '23514' and msg like 'SEC-195-03b:%' then 'state'
    else 'other:' || st end
$$;

-- expect(uid, sql, want, label): chạy câu lệnh trong khối con. Không phải 'ok' với đúng 1 hàng → hoàn tác khối con.
create function cfp_test.expect(uid integer, stmt text, want text, label text) returns void
language plpgsql security invoker as $$
declare n bigint; got text; st text; msg text := '';
begin
  perform set_config('cfp.user_id', coalesce(uid::text, ''), true);
  begin
    execute stmt;
    get diagnostics n = row_count;
    got := case when n = 0 then 'zero_rows' when n = 1 then 'ok' else 'ok:' || n end;
    if got <> 'ok' or want <> 'ok' then  -- không giữ tác động của ca âm / ca lệch
      raise exception using errcode = 'P0001', message = 'CFP_TEST_UNDO:' || got;
    end if;
  exception when others then
    if sqlerrm like 'CFP_TEST_UNDO:%' then
      got := substr(sqlerrm, 15);
    else
      st := sqlstate; msg := sqlerrm; got := cfp_test.classify(st, msg);
    end if;
  end;
  insert into cfp_test.results (label, want, got, sqlstate, detail) values (label, want, got, st, msg);
end $$;
grant execute on function cfp_test.expect(integer, text, text, text) to office_app;

-- ---------- fixture (superuser, bỏ qua RLS) — nằm trong giao dịch, bị rollback
insert into cfp_office.office_roles (user_id, role) values (1, 'governance') on conflict do nothing;
insert into cfp_office.offices (canonical_id, display_name, platform, specialties, capabilities, limits, verification, created_by)
values ('T1', 'Văn Phòng test', 'test', '', '', '', 'TEST', 1);
insert into cfp_office.office_maintainers (canonical_id, user_id) values ('T1', 2);
insert into cfp_office.super_pairs (id, canonical_id, software, software_key, lead_user_id, created_by)
values (9001, 'T1', 'test', 'test-9001', 3, 2);
-- A: luồng ACCEPT • B: nhiều vòng CHANGES_REQUESTED • C: reviewer = người thực thi (dữ liệu lỗi) • D: governance đóng
insert into cfp_office.tasks (id, pair_id, title, description, acceptance, assignee_id, reviewer_id, status, idempotency_key, created_by) values
  (9101, 9001, 'A', '', 'x', 3, 4, 'QUEUED',    'sec03b-A', 2),
  (9102, 9001, 'B', '', 'x', 3, 4, 'QUEUED',    'sec03b-B', 2),
  (9103, 9001, 'C', '', 'x', 3, 3, 'IN_REVIEW', 'sec03b-C', 2),
  (9104, 9001, 'D', '', 'x', 3, 4, 'ACCEPTED',  'sec03b-D', 2);
insert into cfp_office.evidence (task_id, kind, url, description, submitted_by) values (9103, 'URL', 'https://e/c', 'c', 3);
insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9104, 4, 'ACCEPT', 'd');

set local role office_app;
\o /dev/null

-- ---------- tấn công của người thực thi (3) lên nhiệm vụ A
select cfp_test.expect(3, $q$update cfp_office.tasks set reviewer_id = 3 where id = 9101$q$, 'priv', 'A1 người thực thi tự đặt mình làm reviewer');
select cfp_test.expect(3, $q$update cfp_office.tasks set assignee_id = 5 where id = 9101$q$, 'priv', 'A2 người thực thi đổi assignee');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9101$q$, 'state', 'A3 người thực thi nhảy QUEUED → ACCEPTED');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_REVIEW' where id = 9101$q$, 'state', 'A4 người thực thi bỏ bước QUEUED → IN_REVIEW');
select cfp_test.expect(3, $q$update cfp_office.tasks set title = 'đã sửa' where id = 9101$q$, 'priv', 'A5 người thực thi sửa tiêu đề/tiêu chí');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'ACCEPTED', reviewer_id = 3 where id = 9101$q$, 'priv', 'A6 đổi reviewer + ACCEPTED cùng lúc');
select cfp_test.expect(5, $q$update cfp_office.tasks set status = 'ACKED' where id = 9101$q$, 'zero_rows', 'A7 người ngoài ACK hộ (RLS ẩn hàng)');
select cfp_test.expect(null, $q$update cfp_office.tasks set status = 'ACKED' where id = 9101$q$, 'zero_rows', 'A8 không danh tính (RLS ẩn hàng)');
select cfp_test.expect(3, $q$update cfp_office.tasks set review_round = 7 where id = 9101$q$, 'priv', 'A8b người thực thi tự đặt số vòng duyệt');

-- ---------- luồng hợp lệ A: ACK → bắt đầu → Evidence → Review → ACCEPT → Closure
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACKED' where id = 9101$q$, 'actor', 'A9 reviewer ACK thay người thực thi');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'ACKED', updated_at = now() where id = 9101$q$, 'ok', 'A10 người thực thi ACK');
select cfp_test.expect(3, $q$update cfp_office.tasks set updated_at = now() where id = 9101$q$, 'ok', 'A11 chỉ chạm updated_at');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_PROGRESS', updated_at = now() where id = 9101$q$, 'ok', 'A12 người thực thi bắt đầu');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_REVIEW' where id = 9101$q$, 'state', 'A13 chuyển Review khi chưa có Evidence');
select cfp_test.expect(4, $q$insert into cfp_office.evidence (task_id, kind, url, description, submitted_by) values (9101, 'URL', 'https://e/r', 'r', 4)$q$, 'rls', 'A14 reviewer nộp Evidence');
select cfp_test.expect(3, $q$insert into cfp_office.evidence (task_id, kind, url, description, submitted_by) values (9101, 'URL', 'https://e/a', 'a', 3)$q$, 'ok', 'A15 người thực thi nộp Evidence');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9101, 4, 'ACCEPT', 'sớm')$q$, 'rls', 'A16 reviewer chấm khi chưa IN_REVIEW');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_REVIEW', updated_at = now() where id = 9101$q$, 'ok', 'A17 người thực thi gửi Review');
select cfp_test.expect(3, $q$insert into cfp_office.evidence (task_id, kind, url, description, submitted_by) values (9101, 'URL', 'https://e/b', 'b', 3)$q$, 'rls', 'A18 nộp thêm Evidence khi đang IN_REVIEW');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9101$q$, 'actor', 'A19 người thực thi tự nghiệm thu');
select cfp_test.expect(3, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9101, 3, 'ACCEPT', 'tự')$q$, 'rls', 'A20 người thực thi tự ghi Review');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9101$q$, 'state', 'A21 reviewer ACCEPTED khi chưa ghi Review');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9101, 4, 'ACCEPT', 'đạt')$q$, 'ok', 'A22 reviewer ghi Review ACCEPT');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED', updated_at = now() where id = 9101$q$, 'ok', 'A23 reviewer chuyển ACCEPTED');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9101$q$, 'actor', 'A24 người thực thi tự Closure');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9101$q$, 'actor', 'A25 reviewer Closure (không phải người giao việc)');
select cfp_test.expect(5, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9101$q$, 'zero_rows', 'A26 người ngoài Closure (RLS ẩn hàng)');
select cfp_test.expect(2, $q$update cfp_office.tasks set status = 'CLOSED', updated_at = now() where id = 9101$q$, 'ok', 'A27 người giao việc Closure');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'IN_PROGRESS' where id = 9101$q$, 'state', 'A28 mở lại nhiệm vụ đã CLOSED');

-- ---------- B: nhiều vòng duyệt — mỗi quyết định chỉ có hiệu lực cho đúng vòng của nó
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'ACKED' where id = 9102$q$, 'ok', 'B1 ACK');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_PROGRESS' where id = 9102$q$, 'ok', 'B2 bắt đầu');
select cfp_test.expect(3, $q$insert into cfp_office.evidence (task_id, kind, url, description, submitted_by) values (9102, 'URL', 'https://e/b1', 'b1', 3)$q$, 'ok', 'B3 Evidence');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_REVIEW' where id = 9102$q$, 'ok', 'B4 gửi Review (mở vòng 1)');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9102, 4, 'CHANGES_REQUESTED', 'sửa v1')$q$, 'ok', 'B5 reviewer yêu cầu sửa (vòng 1)');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9102$q$, 'state', 'B6 ACCEPTED trái với Review CHANGES_REQUESTED');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CHANGES_REQUESTED' where id = 9102$q$, 'ok', 'B7 chuyển CHANGES_REQUESTED (vòng 1)');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_PROGRESS' where id = 9102$q$, 'ok', 'B8 người thực thi làm lại');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_REVIEW' where id = 9102$q$, 'ok', 'B9 gửi Review lần 2 (mở vòng 2)');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9102$q$, 'state', 'B10 ACCEPTED dựa trên Review cũ (CHANGES_REQUESTED vòng 1)');
-- Ca hồi quy mới: CHANGES_REQUESTED cũng phải là quyết định MỚI của đúng vòng
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CHANGES_REQUESTED' where id = 9102$q$, 'state', 'R1 vòng 2: CHANGES_REQUESTED dùng lại Review vòng 1');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9102, 4, 'CHANGES_REQUESTED', 'sửa v2')$q$, 'ok', 'R2 reviewer ghi CHANGES_REQUESTED cho vòng 2');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CHANGES_REQUESTED' where id = 9102$q$, 'ok', 'R3 vòng 2: CHANGES_REQUESTED với quyết định đúng vòng');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_PROGRESS' where id = 9102$q$, 'ok', 'R4 người thực thi làm lại lần 2');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_REVIEW' where id = 9102$q$, 'ok', 'R5 gửi Review lần 3 (mở vòng 3)');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CHANGES_REQUESTED' where id = 9102$q$, 'state', 'R6 vòng 3: CHANGES_REQUESTED dùng lại Review vòng 2');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes, review_round) values (9102, 4, 'ACCEPT', 'ghi lùi', 1)$q$, 'ok', 'R7 Review tự khai vòng 1 → bị đóng dấu vòng hiện tại (3)');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9102, 4, 'CHANGES_REQUESTED', 'sửa v3')$q$, 'ok', 'R8 reviewer đổi ý: CHANGES_REQUESTED vòng 3 (mới nhất)');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9102$q$, 'state', 'R9 ACCEPTED khi quyết định mới nhất của vòng 3 là CHANGES_REQUESTED');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9102, 4, 'ACCEPT', 'đạt')$q$, 'ok', 'B11 Review ACCEPT mới (vòng 3)');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9102$q$, 'ok', 'B12 ACCEPTED');

-- ---------- C: dữ liệu lỗi reviewer = người thực thi → vẫn không tự nghiệm thu được
select cfp_test.expect(3, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9103, 3, 'ACCEPT', 'tự')$q$, 'rls', 'C1 reviewer trùng người thực thi ghi Review');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9103$q$, 'actor', 'C2 reviewer trùng người thực thi ACCEPTED');

-- ---------- D: governance đóng nhiệm vụ đã ACCEPTED
select cfp_test.expect(1, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9104$q$, 'ok', 'D1 governance Closure');

reset role;

-- ---------- kiểm tra trạng thái sau luồng (superuser)
insert into cfp_test.results (label, want, got)
select 'V1 tasks B: review_round = 3', 'ok', case when review_round = 3 then 'ok' else 'round=' || review_round end
from cfp_office.tasks where id = 9102;
insert into cfp_test.results (label, want, got)
select 'V2 reviews B theo vòng: 1 CR • 2 CR • 3 ACCEPT(R7) CR ACCEPT', 'ok',
       case when s = '1:CHANGES_REQUESTED,2:CHANGES_REQUESTED,3:ACCEPT,3:CHANGES_REQUESTED,3:ACCEPT' then 'ok' else s end
from (select string_agg(review_round || ':' || decision, ',' order by id) as s from cfp_office.reviews where task_id = 9102) x;

-- ---------- E1: role BYPASSRLS (người chạy migration, không superuser) sửa khẩn cấp — phải cập nhật ĐÚNG 1 hàng
set local role cfp_migrator;
do $$ declare n bigint; v integer; begin
  update cfp_office.tasks set reviewer_id = 4 where id = 9103;
  get diagnostics n = row_count;
  select reviewer_id into v from cfp_office.tasks where id = 9103;
  insert into cfp_test.results (label, want, got, detail)
  values ('E1 role BYPASSRLS sửa reviewer khẩn cấp (đúng 1 hàng, giá trị mới = 4)', 'ok',
          case when n = 1 and v = 4 then 'ok' else format('rows=%s reviewer=%s', n, v) end, '');
exception when others then
  insert into cfp_test.results (label, want, got, sqlstate, detail)
  values ('E1 role BYPASSRLS sửa reviewer khẩn cấp (đúng 1 hàng, giá trị mới = 4)', 'ok', cfp_test.classify(sqlstate, sqlerrm), sqlstate, sqlerrm);
end $$;
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

\echo SEC195_03B pass=:pass_count fail=:fail_count rollback_clean=:rollback_clean
select set_config('cfp_test.fail', :'fail_count', false) as _f, set_config('cfp_test.clean', :'rollback_clean', false) as _c \gset
do $$ begin
  if current_setting('cfp_test.fail')::int > 0 then
    raise exception 'SEC-195-03b: % ca FAIL', current_setting('cfp_test.fail');
  end if;
  if not current_setting('cfp_test.clean')::boolean then
    raise exception 'SEC-195-03b: dữ liệu test còn sót sau rollback (dấu vân tay cfp_office lệch)';
  end if;
end $$;
