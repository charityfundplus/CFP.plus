-- CFP+ • 004 • Khôi phục Worker P0: xoá schema cfp_worker và 2 role của nó.
-- CHỈ dùng trên sandbox. Xoá hàng đợi/nhật ký worker. Không đụng tới cfp_office hay cfp_forum_*.
begin;
drop schema if exists cfp_worker cascade;
do $$ declare r text; begin
  foreach r in array array['worker_app', 'worker_governance'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      begin
        execute format('drop role %I', r);
      exception when dependent_objects_still_exist then
        raise notice 'giữ role % (còn được dùng ở database khác)', r;
      end;
    end if;
  end loop;
end $$;
commit;
