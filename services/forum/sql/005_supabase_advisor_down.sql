-- CFP+ • 005 DOWN • trả quyền EXECUTE của public.rls_auto_enable() về mặc định Postgres (PUBLIC).
-- Chỉ dùng khi cần khôi phục trạng thái trước 005. Advisor 0028/0029 sẽ cảnh báo lại.
begin;
do $$
begin
  if to_regprocedure('public.rls_auto_enable()') is null then
    raise notice '005 down: public.rls_auto_enable() không tồn tại — bỏ qua';
    return;
  end if;
  grant execute on function public.rls_auto_enable() to public;
end $$;
commit;
