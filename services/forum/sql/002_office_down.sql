-- CFP+ • 002 • Khôi phục Văn Phòng SI AI: xoá schema cfp_office và 2 role của nó.
-- CHỈ dùng trên sandbox. Xoá toàn bộ dữ liệu Văn Phòng. Không đụng tới cfp_forum_* (#193).
begin;
drop schema if exists cfp_office cascade;
do $$ declare r text; begin
  foreach r in array array['office_app', 'office_governance'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      -- office_app/office_governance không sở hữu object nào (bảng thuộc người chạy migration);
      -- DROP SCHEMA ... CASCADE đã xoá mọi quyền gắn với schema → DROP ROLE trực tiếp.
      begin
        execute format('drop role %I', r);
      exception when dependent_objects_still_exist then
        -- Role dùng chung toàn cluster: còn quyền ở database khác → giữ role, chỉ gỡ schema ở đây.
        raise notice 'giữ role % (còn được dùng ở database khác)', r;
      end;
    end if;
  end loop;
end $$;
commit;
