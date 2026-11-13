-- CFP+ • 003 • Khôi phục: bỏ RLS theo người dùng, trả về đúng policy của 002_office.sql.
-- Không xoá dữ liệu. Idempotent.
begin;
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
