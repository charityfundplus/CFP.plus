-- CFP+ • 003 • Văn Phòng SI AI: RLS theo từng người dùng (SEC-P0-195-03)
-- Áp SAU 002_office.sql. Idempotent. Không chứa mật khẩu. Khôi phục: 003_office_rls_down.sql.
-- CHƯA ÁP lên Supabase: cần thẩm định SecuritySI + phê duyệt Human Governance riêng.
--
-- Mô hình tin cậy
-- • Mỗi giao dịch, backend đặt danh tính người dùng: set_config('cfp.user_id', '<id>', true).
--   Thiếu danh tính → mọi dữ liệu nội bộ bị ẩn, mọi ghi bị từ chối (fail-closed).
-- • Quyền (governance, maintainer, người tham gia) được TÍNH TRONG DATABASE từ office_roles /
--   office_maintainers / tasks — không tin cờ do app gửi.
-- • Mục tiêu: lỗi IDOR/thiếu kiểm quyền ở tầng app không làm lộ hay ghi chéo dữ liệu người khác.
--   Không chống được kẻ đã chiếm credential office_app (có thể tự đặt cfp.user_id).
-- • Hàm kiểm quyền là SECURITY DEFINER (tránh đệ quy policy), chủ sở hữu là người chạy migration
--   và cần BYPASSRLS (Supabase: role postgres có sẵn).

begin;

do $$ begin
  if not (select rolbypassrls from pg_roles where rolname = current_user) then
    raise exception '003 cần người chạy migration có BYPASSRLS (Supabase: postgres). current_user=%', current_user;
  end if;
  if to_regclass('cfp_office.tasks') is null then
    raise exception '003 phải áp sau 002_office.sql';
  end if;
end $$;

-- ---------- hàm kiểm quyền (đọc danh tính từ GUC giao dịch)
create or replace function cfp_office.actor() returns integer
language sql stable set search_path = pg_catalog as $$
  select nullif(current_setting('cfp.user_id', true), '')::integer
$$;

create or replace function cfp_office.is_governance() returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select exists (select 1 from office_roles where user_id = cfp_office.actor() and role = 'governance')
$$;

create or replace function cfp_office.is_maintainer(p_office varchar) returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select exists (select 1 from office_maintainers where canonical_id = p_office and user_id = cfp_office.actor())
$$;

create or replace function cfp_office.can_see_task_row(p_pair integer, p_assignee integer, p_reviewer integer,
                                                       p_creator integer) returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select cfp_office.actor() is not null and (
    cfp_office.actor() in (p_assignee, p_reviewer, p_creator)
    or cfp_office.is_governance()
    or cfp_office.is_maintainer((select canonical_id from super_pairs where id = p_pair)))
$$;

create or replace function cfp_office.can_see_task(p_task integer) returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select coalesce((select cfp_office.can_see_task_row(pair_id, assignee_id, reviewer_id, created_by)
                   from tasks where id = p_task), false)
$$;

create or replace function cfp_office.can_see_dataset_row(p_id integer, p_access varchar, p_creator integer)
returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select p_access = 'public'
      or (cfp_office.actor() is not null and (
            p_creator = cfp_office.actor() or cfp_office.is_governance()
            or exists (select 1 from links l
                       where l.to_ref = 'dataset:' || p_id and l.from_ref like 'task:%'
                         and cfp_office.can_see_task(substr(l.from_ref, 6)::integer))))
$$;

create or replace function cfp_office.ref_visible(p_ref varchar) returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select case
    when p_ref ~ '^task:[0-9]+$' then cfp_office.can_see_task(substr(p_ref, 6)::integer)
    when p_ref ~ '^dataset:[0-9]+$' then coalesce((select cfp_office.can_see_dataset_row(id, access, created_by)
                                                   from datasets where id = substr(p_ref, 9)::integer), false)
    else true end
$$;

-- Giới hạn 5 việc song song là toàn cục: đếm qua hàm (không bị RLS theo người dùng thu hẹp).
create or replace function cfp_office.in_progress_count() returns bigint
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select count(*) from tasks where status = 'IN_PROGRESS'
$$;

-- ---------- SEC-P0-195-03c: hàm kiểm bất biến GHI (phản biện RLS 003 @ a801627: C1, C1b, C2, G3, G4, G5)
-- Có vai trò reviewer/governance (chỉ đọc office_roles; không phụ thuộc RLS của người gọi).
create or replace function cfp_office.has_review_role(p_user integer) returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select exists (select 1 from office_roles where user_id = p_user and role in ('reviewer', 'governance'))
$$;

-- Lead của Siêu Bộ Đôi: create_task luôn giao cho lead (office.py create_task).
create or replace function cfp_office.pair_lead(p_pair integer) returns integer
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select lead_user_id from super_pairs where id = p_pair
$$;

-- Quyền tạo liên kết TỪ một mục (tương đương can_link_from của app). Khác app ở một điểm có chủ đích:
-- nguồn task:<id> chỉ cần xem được nhiệm vụ, vì app tự ghi link task → topic (bài học) và task → forum
-- (thảo luận) cho mọi người tham gia, kể cả reviewer. Loại mục không biết → từ chối (fail-closed).
create or replace function cfp_office.can_link_from(p_ref varchar) returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select cfp_office.actor() is not null and coalesce(cfp_office.is_governance() or case
    when p_ref ~ '^office:.+$' then cfp_office.is_maintainer(substr(p_ref, 8))
    when p_ref ~ '^brand:[0-9]{1,9}$' then
      cfp_office.is_maintainer((select canonical_id from brand_items where id = substr(p_ref, 7)::integer))
    when p_ref ~ '^pair:[0-9]{1,9}$' then
      cfp_office.is_maintainer((select canonical_id from super_pairs where id = substr(p_ref, 6)::integer))
    when p_ref ~ '^enterprise:[0-9]{1,9}$' then
      (select created_by from enterprises where id = substr(p_ref, 12)::integer) = cfp_office.actor()
    when p_ref ~ '^topic:[0-9]{1,9}$' then
      (select created_by from research_topics where id = substr(p_ref, 7)::integer) = cfp_office.actor()
    when p_ref ~ '^dataset:[0-9]{1,9}$' then
      (select created_by from datasets where id = substr(p_ref, 9)::integer) = cfp_office.actor()
    when p_ref ~ '^task:[0-9]{1,9}$' then cfp_office.can_see_task(substr(p_ref, 6)::integer)
    else false end, false)
$$;

-- Sự kiện nhiệm vụ phải khớp trạng thái THẬT (đọc sau UPDATE trong cùng giao dịch, như move() ghi):
--   • COMMENT: from_status = trạng thái hiện tại (office.py comment()).
--   • tạo: NULL → QUEUED, nhiệm vụ đang QUEUED, người ghi là người giao việc (create_task).
--   • chuyển: to_status = trạng thái hiện tại, cặp nguồn → đích hợp lệ, đúng người cho bước đó (move()).
create or replace function cfp_office.task_event_ok(p_task integer, p_from varchar, p_to varchar) returns boolean
language sql stable security definer set search_path = cfp_office, pg_temp as $$
  select coalesce((select case
    when p_to = 'COMMENT' then p_from = t.status
    when p_from is null then p_to = 'QUEUED' and t.status = 'QUEUED' and cfp_office.actor() = t.created_by
    when p_to <> t.status then false
    when (p_from, p_to) in (('QUEUED', 'ACKED'), ('ACKED', 'IN_PROGRESS'), ('CHANGES_REQUESTED', 'IN_PROGRESS'),
                            ('IN_PROGRESS', 'IN_REVIEW')) then cfp_office.actor() = t.assignee_id
    when p_from = 'IN_REVIEW' and p_to in ('ACCEPTED', 'CHANGES_REQUESTED') then
      cfp_office.actor() = t.reviewer_id and t.reviewer_id <> t.assignee_id
    when p_from = 'ACCEPTED' and p_to = 'CLOSED' then
      cfp_office.actor() <> t.assignee_id and (cfp_office.actor() = t.created_by or cfp_office.is_governance())
    else false end
  from tasks t where t.id = p_task), false)
$$;

do $$ declare f text; begin
  foreach f in array array['actor()', 'is_governance()', 'is_maintainer(varchar)',
                           'has_review_role(integer)', 'pair_lead(integer)', 'can_link_from(varchar)',
                           'task_event_ok(integer,varchar,varchar)',
                           'can_see_task_row(integer,integer,integer,integer)', 'can_see_task(integer)',
                           'can_see_dataset_row(integer,varchar,integer)', 'ref_visible(varchar)',
                           'in_progress_count()'] loop
    execute format('revoke all on function cfp_office.%s from public', f);
    execute format('grant execute on function cfp_office.%s to office_app', f);
  end loop;
end $$;

-- ---------- thay policy "USING (true)" của 002 bằng policy theo người dùng
do $$ declare t text; begin
  foreach t in array array['offices','office_maintainers','brand_items','enterprises','research_topics',
                           'datasets','super_pairs','tasks','task_events','evidence','reviews','links','audit_log'] loop
    execute format('drop policy if exists office_app_all on cfp_office.%I', t);
    execute format('drop policy if exists rls_select on cfp_office.%I', t);
    execute format('drop policy if exists rls_insert on cfp_office.%I', t);
    execute format('drop policy if exists rls_update on cfp_office.%I', t);
  end loop;
end $$;
-- office_roles: giữ office_app_all (app chỉ có quyền SELECT; ghi chỉ qua office_governance).

-- Dữ liệu công khai: đọc tự do; ghi phải đúng danh tính.
create policy rls_select on cfp_office.offices for select to office_app using (true);
create policy rls_insert on cfp_office.offices for insert to office_app
  with check (created_by = cfp_office.actor() and cfp_office.is_governance());

create policy rls_select on cfp_office.office_maintainers for select to office_app using (true);
create policy rls_insert on cfp_office.office_maintainers for insert to office_app
  with check (cfp_office.is_governance());

create policy rls_select on cfp_office.brand_items for select to office_app using (true);
create policy rls_insert on cfp_office.brand_items for insert to office_app
  with check (created_by = cfp_office.actor()
              and (cfp_office.is_governance() or cfp_office.is_maintainer(canonical_id))
              and (source_type = 'CFP_PUBLIC_SOURCE' or cfp_office.is_governance()));

create policy rls_select on cfp_office.enterprises for select to office_app using (true);
create policy rls_insert on cfp_office.enterprises for insert to office_app
  with check (created_by = cfp_office.actor());

create policy rls_select on cfp_office.research_topics for select to office_app using (true);
create policy rls_insert on cfp_office.research_topics for insert to office_app
  with check (created_by = cfp_office.actor());

create policy rls_select on cfp_office.super_pairs for select to office_app using (true);
create policy rls_insert on cfp_office.super_pairs for insert to office_app
  with check (created_by = cfp_office.actor()
              and (cfp_office.is_governance() or cfp_office.is_maintainer(canonical_id)));

-- Tài liệu: công khai hoặc người tạo / governance / người xem được nhiệm vụ dùng tài liệu.
create policy rls_select on cfp_office.datasets for select to office_app
  using (cfp_office.can_see_dataset_row(id, access, created_by));
create policy rls_insert on cfp_office.datasets for insert to office_app
  with check (created_by = cfp_office.actor());

-- Nhiệm vụ: chỉ người tham gia / maintainer của đúng Văn Phòng / governance.
create policy rls_select on cfp_office.tasks for select to office_app
  using (cfp_office.can_see_task_row(pair_id, assignee_id, reviewer_id, created_by));
-- rls_insert của tasks tạo ở cuối tệp (SEC-195-03c), sau khi có cột review_round.
-- Cập nhật: người thực thi/reviewer theo luồng; Closure (ACCEPTED → CLOSED) chỉ governance hoặc người giao việc.
create policy rls_update on cfp_office.tasks for update to office_app
  using (cfp_office.actor() in (assignee_id, reviewer_id)
         or (status = 'ACCEPTED' and (cfp_office.actor() = created_by or cfp_office.is_governance())))
  with check ((cfp_office.actor() in (assignee_id, reviewer_id) and status <> 'CLOSED')
              or (status = 'CLOSED' and cfp_office.actor() <> assignee_id
                  and (cfp_office.actor() = created_by or cfp_office.is_governance())));

create policy rls_select on cfp_office.task_events for select to office_app using (cfp_office.can_see_task(task_id));
create policy rls_insert on cfp_office.task_events for insert to office_app
  with check (actor_id = cfp_office.actor() and cfp_office.can_see_task(task_id)
              and cfp_office.task_event_ok(task_id, from_status, to_status));  -- SEC-195-03c (G4)

create policy rls_select on cfp_office.evidence for select to office_app using (cfp_office.can_see_task(task_id));
create policy rls_insert on cfp_office.evidence for insert to office_app
  with check (submitted_by = cfp_office.actor()
              and exists (select 1 from cfp_office.tasks t where t.id = task_id
                          and t.assignee_id = submitted_by and t.status in ('ACKED', 'IN_PROGRESS')));

create policy rls_select on cfp_office.reviews for select to office_app using (cfp_office.can_see_task(task_id));
create policy rls_insert on cfp_office.reviews for insert to office_app
  with check (reviewer_id = cfp_office.actor()
              and decision in ('ACCEPT', 'CHANGES_REQUESTED')
              and exists (select 1 from cfp_office.tasks t where t.id = task_id
                          and t.reviewer_id = reviews.reviewer_id and t.assignee_id <> reviews.reviewer_id
                          and t.status = 'IN_REVIEW'));

create policy rls_select on cfp_office.links for select to office_app
  using (cfp_office.ref_visible(from_ref) and cfp_office.ref_visible(to_ref));
-- SEC-195-03c (C1, C1b): hai đầu phải xem được + có quyền trên mục nguồn (giống add_link() của app).
create policy rls_insert on cfp_office.links for insert to office_app
  with check (created_by = cfp_office.actor()
              and cfp_office.ref_visible(from_ref) and cfp_office.ref_visible(to_ref)
              and cfp_office.can_link_from(from_ref));

create policy rls_select on cfp_office.audit_log for select to office_app
  using (cfp_office.is_governance() or (ref ~ '^task:[0-9]+$' and cfp_office.ref_visible(ref)));
create policy rls_insert on cfp_office.audit_log for insert to office_app
  with check (actor_id = cfp_office.actor());

-- ---------- SEC-P0-195-03b: máy trạng thái nhiệm vụ ở tầng database
-- RLS chỉ lọc HÀNG; không chặn được người thực thi tự đổi reviewer_id/assignee_id hay nhảy thẳng sang ACCEPTED.
-- (1) Quyền theo cột: office_app chỉ được UPDATE status, updated_at (app chỉ cập nhật đúng 2 cột này, office.py move()).
revoke update on cfp_office.tasks from office_app;
grant update (status, updated_at) on cfp_office.tasks to office_app;

-- (1b) Vòng duyệt: mỗi lần vào IN_REVIEW, trigger tăng tasks.review_round; mỗi Review được đóng dấu vòng hiện tại
-- (trigger, app không tự đặt được). Quyết định chỉ có hiệu lực cho đúng vòng → Review cũ không dùng lại được.
-- App không đọc/ghi 2 cột này.
-- Khởi tạo (CHỈ lần đầu thêm cột — chạy lại 003 không đánh số lại):
--   • Review đã có → vòng 0 (lịch sử trước migration, không gán được vào vòng nào).
--   • Nhiệm vụ đang IN_REVIEW → vòng 1: reviewer phải ghi quyết định MỚI sau migration; Review cũ (vòng 0)
--     không dùng lại được. An toàn vì app ghi Review và chuyển trạng thái trong CÙNG giao dịch (office.py
--     review()), nên không có quyết định nào của vòng đang mở mà chưa được áp.
--   • Nhiệm vụ ở trạng thái khác → vòng 0; lần vào IN_REVIEW kế tiếp mở vòng 1.
do $$ begin
  if not exists (select 1 from information_schema.columns
                 where table_schema = 'cfp_office' and table_name = 'tasks' and column_name = 'review_round') then
    alter table cfp_office.tasks add column review_round integer not null default 0;
    update cfp_office.tasks set review_round = 1 where status = 'IN_REVIEW';
  end if;
end $$;
alter table cfp_office.reviews add column if not exists review_round integer not null default 0;

create or replace function cfp_office.stamp_review_round() returns trigger
language plpgsql security definer set search_path = cfp_office, pg_temp as $$
begin  -- DEFINER: đọc tasks không phụ thuộc RLS; chỉ đặt giá trị, không cấp thêm quyền ghi
  new.review_round := coalesce((select review_round from tasks where id = new.task_id), 0);
  return new;
end $$;
revoke all on function cfp_office.stamp_review_round() from public;
drop trigger if exists stamp_review_round on cfp_office.reviews;
create trigger stamp_review_round before insert on cfp_office.reviews
  for each row execute function cfp_office.stamp_review_round();

-- (2) Trigger: mỗi bước chuyển phải đúng nguồn → đích, đúng người, đủ điều kiện — giống TRANSITIONS/review/close
-- trong office.py. Kiểm tra áp cho mọi role không có BYPASSRLS (người chạy migration/sửa khẩn cấp vẫn làm được);
-- đánh số vòng duyệt áp cho MỌI role để review_round luôn nhất quán.
-- SQLSTATE: 42501 = sai người (không có thẩm quyền) • 23514 = sai trạng thái / thiếu điều kiện (Evidence, Review đúng vòng).
create or replace function cfp_office.enforce_task_transition() returns trigger
-- SECURITY INVOKER (cố ý): current_user phải là role gọi thật (office_app) để phân biệt với role BYPASSRLS.
language plpgsql security invoker set search_path = cfp_office, pg_temp as $$
declare
  a integer := cfp_office.actor();
  round_decision varchar;
begin
  if not (select rolbypassrls from pg_roles where rolname = current_user) then
    if (new.id, new.pair_id, new.title, new.description, new.acceptance, new.assignee_id, new.reviewer_id,
        new.idempotency_key, new.created_by, new.created_at, new.review_round)
       is distinct from
       (old.id, old.pair_id, old.title, old.description, old.acceptance, old.assignee_id, old.reviewer_id,
        old.idempotency_key, old.created_by, old.created_at, old.review_round) then
      raise exception 'SEC-195-03b: chỉ được đổi trạng thái nhiệm vụ' using errcode = '42501';
    end if;
    if new.status is distinct from old.status then
      if a is null then
        raise exception 'SEC-195-03b: thiếu danh tính' using errcode = '42501';
      end if;
      if (old.status, new.status) in (('QUEUED', 'ACKED'), ('ACKED', 'IN_PROGRESS'),
                                      ('CHANGES_REQUESTED', 'IN_PROGRESS'), ('IN_PROGRESS', 'IN_REVIEW')) then
        if a <> old.assignee_id then
          raise exception 'SEC-195-03b: chỉ người thực thi được % → %', old.status, new.status using errcode = '42501';
        end if;
        if new.status = 'IN_REVIEW' and not exists (select 1 from evidence where task_id = old.id) then
          raise exception 'SEC-195-03b: cần Evidence trước khi chuyển Review' using errcode = '23514';
        end if;
      elsif old.status = 'IN_REVIEW' and new.status in ('ACCEPTED', 'CHANGES_REQUESTED') then
        if a <> old.reviewer_id or a = old.assignee_id then
          raise exception 'SEC-195-03b: chỉ reviewer được chỉ định (khác người thực thi) được nghiệm thu'
            using errcode = '42501';
        end if;
        -- Quyết định mới nhất của reviewer được chỉ định TRONG ĐÚNG vòng hiện tại.
        select decision into round_decision from reviews
          where task_id = old.id and reviewer_id = old.reviewer_id and review_round = old.review_round
          order by id desc limit 1;
        if round_decision is distinct from
           (case new.status when 'ACCEPTED' then 'ACCEPT' else 'CHANGES_REQUESTED' end) then
          raise exception 'SEC-195-03b: thiếu Review % của vòng % (có: %)', new.status, old.review_round,
            coalesce(round_decision, 'không có') using errcode = '23514';
        end if;
      elsif old.status = 'ACCEPTED' and new.status = 'CLOSED' then
        if a = old.assignee_id or not (a = old.created_by or cfp_office.is_governance()) then
          raise exception 'SEC-195-03b: Closure chỉ governance hoặc người giao việc' using errcode = '42501';
        end if;
        -- SEC-195-03c (C2): Closure đòi Independent Review — ACCEPT của reviewer được chỉ định (khác người
        -- thực thi) trong ĐÚNG vòng hiện tại. Nhiệm vụ ACCEPTED trước 003: Review và nhiệm vụ cùng vòng 0.
        if old.reviewer_id = old.assignee_id or not exists (
             select 1 from reviews where task_id = old.id and reviewer_id = old.reviewer_id
               and decision = 'ACCEPT' and review_round = old.review_round) then
          raise exception 'SEC-195-03b: Closure cần Review ACCEPT độc lập của vòng %', old.review_round
            using errcode = '23514';
        end if;
      else
        raise exception 'SEC-195-03b: không cho phép % → %', old.status, new.status using errcode = '23514';
      end if;
    end if;
  end if;
  if new.status = 'IN_REVIEW' and old.status is distinct from 'IN_REVIEW' then
    new.review_round := old.review_round + 1;  -- mở vòng duyệt mới
  end if;
  return new;
end $$;
revoke all on function cfp_office.enforce_task_transition() from public;

drop trigger if exists enforce_task_transition on cfp_office.tasks;
create trigger enforce_task_transition before update on cfp_office.tasks
  for each row execute function cfp_office.enforce_task_transition();

-- ---------- SEC-P0-195-03c: tasks INSERT đúng bất biến của create_task (C2 nhánh tạo, G3, G5)
-- QUEUED • giao cho lead của Siêu Bộ Đôi • reviewer khác người thực thi và có vai trò reviewer/governance •
-- review_round bắt đầu từ 0 (chỉ trigger được tăng).
drop policy if exists rls_insert on cfp_office.tasks;
create policy rls_insert on cfp_office.tasks for insert to office_app
  with check (created_by = cfp_office.actor()
              and (cfp_office.is_governance()
                   or cfp_office.is_maintainer((select canonical_id from cfp_office.super_pairs where id = pair_id)))
              and status = 'QUEUED'
              and review_round = 0
              and assignee_id = cfp_office.pair_lead(pair_id)
              and reviewer_id <> assignee_id
              and cfp_office.has_review_role(reviewer_id));

commit;
