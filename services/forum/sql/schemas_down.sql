-- CFP+ Forum P0 • Khôi phục: xoá toàn bộ 3 schema diễn đàn và role của chúng.
-- CHỈ dùng trên sandbox. Xoá cả dữ liệu thử nghiệm trong các schema này.

DO $$
DECLARE
  r record;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('cfp_forum_auth',  'cfp_forum_auth_rw'),
      ('cfp_forum_sbd',   'cfp_forum_sbd_rw'),
      ('cfp_forum_hstdn', 'cfp_forum_hstdn_rw')) AS t(sch, rol)
  LOOP
    EXECUTE format('DROP SCHEMA IF EXISTS %I CASCADE', r.sch);
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r.rol) THEN
      EXECUTE format('DROP OWNED BY %I', r.rol);
      EXECUTE format('DROP ROLE %I', r.rol);
    END IF;
  END LOOP;
END $$;
