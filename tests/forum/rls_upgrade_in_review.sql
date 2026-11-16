-- SEC-P0-195-03b • Nhiệm vụ đang dở dang TRƯỚC migration 003 vẫn nhận Review hợp lệ SAU migration,
-- và Review cũ (trước migration) không dùng lại được cho vòng đang mở.
-- Chạy qua tests/forum/rls_upgrade_check.sh (database tạm: 002 → dữ liệu dở dang → 003 ×2 → script này).
-- Nhóm kết quả: xem rls_test_lib.sql. Giao dịch ROLLBACK ở cuối; database tạm bị xoá sau đó.
\set QUIET 1
\pset footer off
set client_min_messages = warning;
begin;
\ir rls_test_lib.sql

-- ---------- U0: khởi tạo review_round sau khi áp 003 HAI lần (lần 2 không được đánh số lại)
insert into cfp_test.results (label, want, got)
select 'U0a tasks: L1=1 L2=1 (IN_REVIEW) • L3=0 • L4=0', 'ok',
       case when s = '9201:1,9202:1,9203:0,9204:0' then 'ok' else s end
from (select string_agg(id || ':' || review_round, ',' order by id) as s from cfp_office.tasks where id between 9201 and 9204) x;
insert into cfp_test.results (label, want, got)
select 'U0b reviews cũ: đều vòng 0', 'ok', case when n = 3 and bad = 0 then 'ok' else format('n=%s khác0=%s', n, bad) end
from (select count(*) as n, count(*) filter (where review_round <> 0) as bad
      from cfp_office.reviews where task_id between 9201 and 9204) x;

set local role office_app;
\o /dev/null
-- ---------- L1: IN_REVIEW + Review CHANGES_REQUESTED cũ
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CHANGES_REQUESTED' where id = 9201$q$, 'state', 'U1 L1: CHANGES_REQUESTED dùng lại Review trước migration');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9201$q$, 'state', 'U2 L1: ACCEPTED khi chưa có Review mới');
select cfp_test.expect(3, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9201, 3, 'ACCEPT', 'tự')$q$, 'rls', 'U3 L1: người thực thi tự ghi Review');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9201, 4, 'ACCEPT', 'đạt sau migration')$q$, 'ok', 'U4 L1: reviewer ghi Review ACCEPT sau migration');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9201$q$, 'ok', 'U5 L1: reviewer chuyển ACCEPTED');
-- ---------- L2: IN_REVIEW, chưa có Review → yêu cầu sửa rồi làm lại
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9202, 4, 'CHANGES_REQUESTED', 'sửa')$q$, 'ok', 'U6 L2: reviewer ghi CHANGES_REQUESTED sau migration');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CHANGES_REQUESTED' where id = 9202$q$, 'ok', 'U7 L2: chuyển CHANGES_REQUESTED');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_PROGRESS' where id = 9202$q$, 'ok', 'U8 L2: người thực thi làm lại');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_REVIEW' where id = 9202$q$, 'ok', 'U9 L2: gửi Review (mở vòng 2)');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CHANGES_REQUESTED' where id = 9202$q$, 'state', 'U10 L2: vòng 2 dùng lại Review vòng 1');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9202, 4, 'ACCEPT', 'đạt')$q$, 'ok', 'U11 L2: Review ACCEPT vòng 2');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9202$q$, 'ok', 'U12 L2: ACCEPTED');
-- ---------- L3: CHANGES_REQUESTED trước migration → làm lại → vòng 1
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_PROGRESS' where id = 9203$q$, 'ok', 'U13 L3: người thực thi làm lại');
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'IN_REVIEW' where id = 9203$q$, 'ok', 'U14 L3: gửi Review (mở vòng 1)');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'CHANGES_REQUESTED' where id = 9203$q$, 'state', 'U15 L3: dùng lại Review trước migration');
select cfp_test.expect(4, $q$insert into cfp_office.reviews (task_id, reviewer_id, decision, notes) values (9203, 4, 'ACCEPT', 'đạt')$q$, 'ok', 'U16 L3: Review ACCEPT vòng 1');
select cfp_test.expect(4, $q$update cfp_office.tasks set status = 'ACCEPTED' where id = 9203$q$, 'ok', 'U17 L3: ACCEPTED');
-- ---------- L4: ACCEPTED trước migration → Closure vẫn làm được
select cfp_test.expect(3, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9204$q$, 'actor', 'U18 L4: người thực thi tự Closure');
select cfp_test.expect(2, $q$update cfp_office.tasks set status = 'CLOSED' where id = 9204$q$, 'ok', 'U19 L4: người giao việc Closure');
\o
reset role;

-- ---------- V: số vòng sau luồng
insert into cfp_test.results (label, want, got)
select 'V1 tasks: L1=1 L2=2 L3=1 L4=0', 'ok', case when s = '9201:1,9202:2,9203:1,9204:0' then 'ok' else s end
from (select string_agg(id || ':' || review_round, ',' order by id) as s from cfp_office.tasks where id between 9201 and 9204) x;
insert into cfp_test.results (label, want, got)
select 'V2 reviews theo vòng (cũ = 0)', 'ok',
       case when s = '9201:0:CHANGES_REQUESTED,9201:1:ACCEPT,9202:1:CHANGES_REQUESTED,9202:2:ACCEPT,'
                     '9203:0:CHANGES_REQUESTED,9203:1:ACCEPT,9204:0:ACCEPT' then 'ok' else s end
from (select string_agg(task_id || ':' || review_round || ':' || decision, ',' order by task_id, id) as s
      from cfp_office.reviews where task_id between 9201 and 9204) x;

\unset QUIET
select n, case when want = got then 'PASS' else 'FAIL' end as kq, label, want, got,
       coalesce(sqlstate, '') as sqlstate, left(detail, 72) as detail
from cfp_test.results order by n;
\set QUIET 1
select count(*) filter (where want = got) as pass_count, count(*) filter (where want <> got) as fail_count
from cfp_test.results \gset
rollback;

\echo SEC195_03B_UPGRADE pass=:pass_count fail=:fail_count
select set_config('cfp_test.fail', :'fail_count', false) as _f \gset
do $$ begin
  if current_setting('cfp_test.fail')::int > 0 then
    raise exception 'SEC-195-03b upgrade: % ca FAIL', current_setting('cfp_test.fail');
  end if;
end $$;
