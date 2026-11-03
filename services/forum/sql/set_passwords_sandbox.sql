-- CFP+ Forum P0 • SANDBOX • Đặt mật khẩu ngẫu nhiên cho 3 role và in ra 3 URL kết nối.
-- Chạy trong Supabase Dashboard → SQL Editor của dự án cfp-plus-forum-sandbox.
-- Mật khẩu được sinh trên server; KHÔNG dán kết quả vào GitHub, chat hay tài liệu.
-- Chỉ dán 3 URL vào biến môi trường bí mật trên Render. Chạy lại = đổi mật khẩu mới.
--
-- BƯỚC DUY NHẤT CẦN SỬA: thay host dưới đây bằng host của "Session pooler"
-- (Dashboard → nút Connect → Session pooler; dạng aws-?-us-west-2.pooler.supabase.com).

DROP TABLE IF EXISTS pg_temp.cfp_pooler, pg_temp.cfp_forum_urls;
CREATE TEMP TABLE cfp_pooler(host text);
INSERT INTO cfp_pooler VALUES ('aws-0-us-west-2.pooler.supabase.com');   -- <== SỬA DÒNG NÀY NẾU KHÁC

CREATE TEMP TABLE cfp_forum_urls(env_key text, url text);

DO $$
DECLARE
  r record;
  pw text;
  ref text := 'gmnsmggqvbwlgluvscfh';
  v_host text := (SELECT p.host FROM cfp_pooler p);
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('CFP_FORUM_AUTH_DB',        'cfp_forum_auth_rw'),
      ('CFP_FORUM_DB_SIEU_BO_DOI', 'cfp_forum_sbd_rw'),
      ('CFP_FORUM_DB_SI_AI_HSTDN', 'cfp_forum_hstdn_rw')) AS t(env_key, rol)
  LOOP
    pw := encode(extensions.gen_random_bytes(24), 'hex');   -- 48 ký tự hex, không cần mã hoá URL
    EXECUTE format('ALTER ROLE %I PASSWORD %L', r.rol, pw);
    INSERT INTO cfp_forum_urls VALUES (r.env_key,
      format('postgresql+psycopg://%s.%s:%s@%s:5432/postgres?sslmode=require', r.rol, ref, pw, v_host));
  END LOOP;
END $$;

SELECT env_key, url FROM cfp_forum_urls ORDER BY env_key;
