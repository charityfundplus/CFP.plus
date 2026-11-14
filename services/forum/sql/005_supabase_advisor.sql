-- CFP+ • 005 • Supabase security advisor 0028/0029 • thu hồi quyền GỌI TRỰC TIẾP public.rls_auto_enable()
--
-- Hiện trạng (đọc ngày 14/11/2026 trên cfp-plus-forum-sandbox, không ghi):
--   public.rls_auto_enable() • owner postgres • SECURITY DEFINER • RETURNS event_trigger • ACL mặc định (PUBLIC EXECUTE)
--   Được event trigger "ensure_rls" (ddl_command_end: CREATE TABLE / CREATE TABLE AS / SELECT INTO) gọi để
--   tự bật RLS cho bảng mới trong schema public. Hàm KHÔNG có trong repo này → do project Supabase tạo sẵn.
--   Advisor cảnh báo anon/authenticated có quyền EXECUTE qua /rest/v1/rpc/rls_auto_enable.
--
-- Thay đổi: chỉ REVOKE EXECUTE khỏi PUBLIC, anon, authenticated. KHÔNG xóa hàm, KHÔNG đổi event trigger.
-- Event trigger vẫn chạy vì Postgres không kiểm tra quyền EXECUTE khi kích hoạt trigger
-- (đã kiểm chứng bằng tests/forum/test_005_supabase_advisor.sh).
-- Idempotent. Hàm không tồn tại (CI, Postgres thường) → bỏ qua. Khôi phục: 005_supabase_advisor_down.sql.
-- CHƯA ÁP lên Supabase: cần SecuritySI + phê duyệt Human Governance.
begin;
do $$
declare
  r text;
begin
  if to_regprocedure('public.rls_auto_enable()') is null then
    raise notice '005: public.rls_auto_enable() không tồn tại — bỏ qua';
    return;
  end if;
  revoke execute on function public.rls_auto_enable() from public;
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke execute on function public.rls_auto_enable() from %I', r);
    end if;
  end loop;
end $$;
commit;
