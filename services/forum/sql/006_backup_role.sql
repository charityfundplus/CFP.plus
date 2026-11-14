-- CFP+ • 006 • Role sao lưu CHỈ ĐỌC: cfp_backup_ro (dùng cho services/forum/backup/backup_drill.sh)
-- Không chứa mật khẩu. Idempotent. Chạy lại SAU mỗi migration mới để phủ bảng mới.
-- - Chỉ USAGE + SELECT trên các schema kho CFP+; không INSERT/UPDATE/DELETE/DDL; phiên mặc định read-only.
-- - BYPASSRLS: cfp_office bật FORCE RLS; pg_dump phải đọc đủ mọi dòng, nếu không bản sao lưu bị thiếu âm thầm.
-- - NOLOGIN khi tạo. Bật đăng nhập + đặt mật khẩu do người có quyền làm thủ công (giống set_passwords_sandbox.sql):
--     ALTER ROLE cfp_backup_ro LOGIN PASSWORD '<mật khẩu dài, lưu trong GitHub secret>';
-- Khôi phục: 006_backup_role_down.sql. CHƯA ÁP lên Supabase: cần SecuritySI + Human Governance.
begin;
do $$
declare
  s record;
begin
  if not exists (select 1 from pg_roles where rolname = 'cfp_backup_ro') then
    create role cfp_backup_ro nologin noinherit bypassrls;
  end if;
  alter role cfp_backup_ro bypassrls;
  alter role cfp_backup_ro connection limit 3;
  alter role cfp_backup_ro set default_transaction_read_only = on;
  alter role cfp_backup_ro set statement_timeout = '10min';
  for s in
    select n.nspname as sch, pg_get_userbyid(n.nspowner) as owner
    from pg_namespace n
    where n.nspname in ('cfp_forum_auth', 'cfp_forum_sbd', 'cfp_forum_hstdn', 'cfp_office', 'cfp_worker')
  loop
    execute format('grant usage on schema %I to cfp_backup_ro', s.sch);
    execute format('grant select on all tables in schema %I to cfp_backup_ro', s.sch);
    execute format('grant select on all sequences in schema %I to cfp_backup_ro', s.sch);
    -- Bảng do chủ schema tạo về sau (diễn đàn: app tạo bảng bằng role *_rw) cũng đọc được.
    execute format('alter default privileges for role %I in schema %I grant select on tables to cfp_backup_ro',
                   s.owner, s.sch);
    execute format('alter default privileges for role %I in schema %I grant select on sequences to cfp_backup_ro',
                   s.owner, s.sch);
  end loop;
end $$;
commit;
