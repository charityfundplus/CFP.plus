-- CFP+ Văn Phòng SI AI • SANDBOX • Bật LOGIN + mật khẩu ngẫu nhiên cho office_app, in URL kết nối.
-- Cùng cách làm với set_passwords_sandbox.sql (#193). Chạy trong Supabase SQL Editor SAU 002_office.sql.
-- Mật khẩu sinh trên server; KHÔNG dán kết quả vào GitHub/chat. Chỉ dán URL vào secret CFP_OFFICE_DB trên Render.
DO $$
DECLARE
  pw text := encode(extensions.gen_random_bytes(24), 'hex');
  ref text := 'gmnsmggqvbwlgluvscfh';
  v_host text := 'aws-0-us-west-2.pooler.supabase.com';   -- <== host Session pooler của dự án
BEGIN
  EXECUTE format('ALTER ROLE office_app LOGIN CONNECTION LIMIT 20 PASSWORD %L', pw);
  RAISE NOTICE 'CFP_OFFICE_DB=postgresql+psycopg://office_app.%:%@%:5432/postgres?sslmode=require', ref, pw, v_host;
END $$;
