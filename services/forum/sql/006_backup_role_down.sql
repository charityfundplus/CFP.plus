-- CFP+ • 006 DOWN • gỡ role sao lưu cfp_backup_ro (quyền, default privileges, role). Không đụng dữ liệu.
begin;
do $$
declare
  s record;
begin
  if not exists (select 1 from pg_roles where rolname = 'cfp_backup_ro') then
    raise notice '006 down: cfp_backup_ro không tồn tại — bỏ qua';
    return;
  end if;
  for s in
    select n.nspname as sch, pg_get_userbyid(n.nspowner) as owner
    from pg_namespace n
    where n.nspname in ('cfp_forum_auth', 'cfp_forum_sbd', 'cfp_forum_hstdn', 'cfp_office', 'cfp_worker')
  loop
    execute format('alter default privileges for role %I in schema %I revoke select on tables from cfp_backup_ro',
                   s.owner, s.sch);
    execute format('alter default privileges for role %I in schema %I revoke select on sequences from cfp_backup_ro',
                   s.owner, s.sch);
    execute format('revoke all on all tables in schema %I from cfp_backup_ro', s.sch);
    execute format('revoke all on all sequences in schema %I from cfp_backup_ro', s.sch);
    execute format('revoke all on schema %I from cfp_backup_ro', s.sch);
  end loop;
  drop role cfp_backup_ro;
end $$;
commit;
