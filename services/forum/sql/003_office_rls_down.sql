-- CFP+ • 003 • Khôi phục: bỏ RLS theo người dùng, trả về đúng policy của 002_office.sql.
-- Không xoá dữ liệu nghiệp vụ (chỉ bỏ cột dẫn xuất review_round của 003b). Idempotent.
begin;
drop trigger if exists enforce_task_transition on cfp_office.tasks;
drop function if exists cfp_office.enforce_task_transition();
drop trigger if exists stamp_review_round on cfp_office.reviews;
drop function if exists cfp_office.stamp_review_round();
-- Số vòng duyệt chỉ là dữ liệu dẫn xuất của 003b (Review, Evidence, nhật ký vẫn giữ nguyên).
alter table cfp_office.reviews drop column if exists review_round;
alter table cfp_office.tasks drop column if exists review_round;
revoke update (status, updated_at) on cfp_office.tasks from office_app;
grant update on cfp_office.tasks to office_app;
do $$ declare t text; begin
  foreach t in array array['offices','office_maintainers','brand_items','enterprises','research_topics',
                           'datasets','super_pairs','tasks','task_events','evidence','reviews','links','audit_log'] loop
    execute format('drop policy if exists rls_select on cfp_office.%I', t);
    execute format('drop policy if exists rls_insert on cfp_office.%I', t);
    execute format('drop policy if exists rls_update on cfp_office.%I', t);
    execute format('drop policy if exists office_app_all on cfp_office.%I', t);
    execute format('create policy office_app_all on cfp_office.%I for all to office_app using (true) with check (true)', t);
  end loop;
end $$;
drop function if exists cfp_office.in_progress_count();
drop function if exists cfp_office.ref_visible(varchar);
drop function if exists cfp_office.can_see_dataset_row(integer, varchar, integer);
drop function if exists cfp_office.can_see_task(integer);
drop function if exists cfp_office.can_see_task_row(integer, integer, integer, integer);
drop function if exists cfp_office.is_maintainer(varchar);
drop function if exists cfp_office.is_governance();
drop function if exists cfp_office.actor();
commit;
