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

do $$ declare f text; begin
  foreach f in array array['actor()', 'is_governance()', 'is_maintainer(varchar)',
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
create policy rls_insert on cfp_office.tasks for insert to office_app
  with check (created_by = cfp_office.actor()
              and (cfp_office.is_governance()
                   or cfp_office.is_maintainer((select canonical_id from cfp_office.super_pairs where id = pair_id))));
-- Cập nhật: người thực thi/reviewer theo luồng; Closure (ACCEPTED → CLOSED) chỉ governance hoặc người giao việc.
create policy rls_update on cfp_office.tasks for update to office_app
  using (cfp_office.actor() in (assignee_id, reviewer_id)
         or (status = 'ACCEPTED' and (cfp_office.actor() = created_by or cfp_office.is_governance())))
  with check ((cfp_office.actor() in (assignee_id, reviewer_id) and status <> 'CLOSED')
              or (status = 'CLOSED' and cfp_office.actor() <> assignee_id
                  and (cfp_office.actor() = created_by or cfp_office.is_governance())));

create policy rls_select on cfp_office.task_events for select to office_app using (cfp_office.can_see_task(task_id));
create policy rls_insert on cfp_office.task_events for insert to office_app
  with check (actor_id = cfp_office.actor() and cfp_office.can_see_task(task_id));

create policy rls_select on cfp_office.evidence for select to office_app using (cfp_office.can_see_task(task_id));
create policy rls_insert on cfp_office.evidence for insert to office_app
  with check (submitted_by = cfp_office.actor()
              and submitted_by = (select assignee_id from cfp_office.tasks where id = task_id));

create policy rls_select on cfp_office.reviews for select to office_app using (cfp_office.can_see_task(task_id));
create policy rls_insert on cfp_office.reviews for insert to office_app
  with check (reviewer_id = cfp_office.actor()
              and reviewer_id = (select t.reviewer_id from cfp_office.tasks t where t.id = task_id));

create policy rls_select on cfp_office.links for select to office_app
  using (cfp_office.ref_visible(from_ref) and cfp_office.ref_visible(to_ref));
create policy rls_insert on cfp_office.links for insert to office_app
  with check (created_by = cfp_office.actor());

create policy rls_select on cfp_office.audit_log for select to office_app
  using (cfp_office.is_governance() or (ref ~ '^task:[0-9]+$' and cfp_office.ref_visible(ref)));
create policy rls_insert on cfp_office.audit_log for insert to office_app
  with check (actor_id = cfp_office.actor());

commit;
