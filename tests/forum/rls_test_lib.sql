-- SEC-P0-195-03b • Hàm kiểm thử dùng chung cho rls_task_transitions.sql và rls_upgrade_in_review.sql.
-- Gọi bằng \ir BÊN TRONG giao dịch test (superuser). Tạo schema cfp_test, bảng kết quả, classify() và expect().
-- Nhóm kết quả: ok (đúng 1 hàng) • zero_rows (RLS ẩn hàng) • priv / rls / actor (42501) • state (23514).
create schema cfp_test;
create table cfp_test.results (n serial, label text, want text, got text, sqlstate text, detail text);
grant usage on schema cfp_test to office_app;
grant insert, select on cfp_test.results to office_app;
grant usage on sequence cfp_test.results_n_seq to office_app;
grant usage on schema cfp_test to cfp_migrator;  -- E1 ghi kết quả dưới role cfp_migrator
grant insert, select on cfp_test.results to cfp_migrator;
grant usage on sequence cfp_test.results_n_seq to cfp_migrator;

create function cfp_test.classify(st text, msg text) returns text language sql immutable as $$
  select case
    when st = '42501' and msg like 'permission denied%' then 'priv'
    when st = '42501' and msg like '%row-level security policy%' then 'rls'
    when st = '42501' and msg like 'SEC-195-03b:%' then 'actor'
    when st = '23514' and msg like 'SEC-195-03b:%' then 'state'
    else 'other:' || st end
$$;

-- expect(uid, sql, want, label): chạy câu lệnh trong khối con. Không phải 'ok' với đúng 1 hàng → hoàn tác khối con.
create function cfp_test.expect(uid integer, stmt text, want text, label text) returns void
language plpgsql security invoker as $$
declare n bigint; got text; st text; msg text := '';
begin
  perform set_config('cfp.user_id', coalesce(uid::text, ''), true);
  begin
    execute stmt;
    get diagnostics n = row_count;
    got := case when n = 0 then 'zero_rows' when n = 1 then 'ok' else 'ok:' || n end;
    if got <> 'ok' or want <> 'ok' then  -- không giữ tác động của ca âm / ca lệch
      raise exception using errcode = 'P0001', message = 'CFP_TEST_UNDO:' || got;
    end if;
  exception when others then
    if sqlerrm like 'CFP_TEST_UNDO:%' then
      got := substr(sqlerrm, 15);
    else
      st := sqlstate; msg := sqlerrm; got := cfp_test.classify(st, msg);
    end if;
  end;
  insert into cfp_test.results (label, want, got, sqlstate, detail) values (label, want, got, st, msg);
end $$;
grant execute on function cfp_test.expect(integer, text, text, text) to office_app;
