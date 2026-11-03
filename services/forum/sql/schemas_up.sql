-- CFP+ Forum P0 • Cách ly 3 schema trong một database Postgres (sandbox).
-- Mỗi kho dữ liệu = 1 schema + 1 role đăng nhập riêng làm chủ schema đó.
-- Role không có USAGE trên schema của kho khác → không đọc/ghi chéo được.
-- search_path gắn theo role → mã không cần biết tên schema.
-- Mật khẩu KHÔNG nằm trong file này; đặt riêng bằng ALTER ROLE ... PASSWORD.
-- Khôi phục: chạy schemas_down.sql.

DO $$
DECLARE
  r record;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('cfp_forum_auth',  'cfp_forum_auth_rw'),
      ('cfp_forum_sbd',   'cfp_forum_sbd_rw'),
      ('cfp_forum_hstdn', 'cfp_forum_hstdn_rw')) AS t(sch, rol)
  LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r.rol) THEN
      EXECUTE format('CREATE ROLE %I LOGIN NOINHERIT NOCREATEDB NOCREATEROLE CONNECTION LIMIT 10', r.rol);
    END IF;
    -- Người chạy script cần SET ROLE được để tạo schema thuộc role đó (PG16+).
    EXECUTE format('GRANT %I TO current_user', r.rol);
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I AUTHORIZATION %I', r.sch, r.rol);
    EXECUTE format('REVOKE ALL ON SCHEMA %I FROM PUBLIC', r.sch);
    EXECUTE format('ALTER ROLE %I SET search_path = %I', r.rol, r.sch);
    EXECUTE format('ALTER ROLE %I SET statement_timeout = %L', r.rol, '15s');
  END LOOP;
END $$;
