-- CFP+ • 004 • Worker P0: schema cfp_worker + role worker_app / worker_governance (sinh từ services/forum/worker.py)
-- Không chứa mật khẩu. Idempotent. Độc lập với cfp_office (002/003) và cfp_forum_* (#193).
-- CHƯA ÁP lên Supabase: cần SecuritySI + phê duyệt Human Governance riêng. Khôi phục: 004_worker_down.sql.
-- Quyền tối thiểu: worker_app chỉ thấy cfp_worker; không UPDATE/DELETE nhật ký; không đổi kill switch.
begin;
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'worker_app') then
    create role worker_app nologin noinherit;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'worker_governance') then
    create role worker_governance nologin noinherit;
  end if;
end $$;
create schema if not exists cfp_worker;
revoke all on schema cfp_worker from public;
set local search_path = cfp_worker;
CREATE TABLE IF NOT EXISTS control (
	key VARCHAR(40) NOT NULL, 
	value VARCHAR(200) NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (key)
);
CREATE TABLE IF NOT EXISTS heartbeats (
	worker_id VARCHAR(120) NOT NULL, 
	last_seen TIMESTAMP WITH TIME ZONE NOT NULL, 
	state VARCHAR(16) NOT NULL, 
	version VARCHAR(24) NOT NULL, 
	ticks INTEGER NOT NULL, 
	PRIMARY KEY (worker_id)
);
CREATE TABLE IF NOT EXISTS jobs (
	id SERIAL NOT NULL, 
	kind VARCHAR(40) NOT NULL, 
	idempotency_key VARCHAR(120) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	attempts INTEGER NOT NULL, 
	max_attempts INTEGER NOT NULL, 
	next_run_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	locked_by VARCHAR(120), 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	last_error TEXT, 
	result TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (idempotency_key)
);
CREATE TABLE IF NOT EXISTS logs (
	id SERIAL NOT NULL, 
	at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	worker_id VARCHAR(120) NOT NULL, 
	job_id INTEGER, 
	level VARCHAR(8) NOT NULL, 
	event VARCHAR(40) NOT NULL, 
	message TEXT NOT NULL, 
	PRIMARY KEY (id)
);
alter table cfp_worker.control enable row level security;
alter table cfp_worker.control force row level security;
alter table cfp_worker.heartbeats enable row level security;
alter table cfp_worker.heartbeats force row level security;
alter table cfp_worker.jobs enable row level security;
alter table cfp_worker.jobs force row level security;
alter table cfp_worker.logs enable row level security;
alter table cfp_worker.logs force row level security;
grant usage on schema cfp_worker to worker_app, worker_governance;
-- worker_app: hàng đợi + heartbeat (đọc/ghi), nhật ký (chỉ thêm), kill switch (chỉ đọc). Không DELETE.
grant select, insert, update on cfp_worker.jobs, cfp_worker.heartbeats to worker_app;
grant select, insert on cfp_worker.logs to worker_app;
grant select on cfp_worker.control to worker_app;
grant usage, select on all sequences in schema cfp_worker to worker_app, worker_governance;
-- worker_governance (NOLOGIN, cấp membership cho người vận hành): bật/tắt kill switch + ghi nhật ký.
grant select, insert, update on cfp_worker.control to worker_governance;
grant select, insert on cfp_worker.logs to worker_governance;
drop policy if exists worker_app_rw on cfp_worker.jobs;
create policy worker_app_rw on cfp_worker.jobs for all to worker_app using (true) with check (true);
drop policy if exists worker_app_rw on cfp_worker.heartbeats;
create policy worker_app_rw on cfp_worker.heartbeats for all to worker_app using (true) with check (true);
drop policy if exists worker_app_read on cfp_worker.logs;
create policy worker_app_read on cfp_worker.logs for select to worker_app using (true);
drop policy if exists worker_app_append on cfp_worker.logs;
create policy worker_app_append on cfp_worker.logs for insert to worker_app with check (true);
drop policy if exists worker_app_read on cfp_worker.control;
create policy worker_app_read on cfp_worker.control for select to worker_app using (true);
drop policy if exists worker_governance_control on cfp_worker.control;
create policy worker_governance_control on cfp_worker.control for all to worker_governance using (true) with check (true);
drop policy if exists worker_governance_log on cfp_worker.logs;
create policy worker_governance_log on cfp_worker.logs for insert to worker_governance with check (event = 'kill_switch');
insert into cfp_worker.control (key, value) values ('paused', 'false') on conflict (key) do nothing;
alter role worker_app set search_path = cfp_worker;
do $$ declare r text; begin
  foreach r in array array['anon','authenticated','service_role','office_app','cfp_forum_auth_rw','cfp_forum_sbd_rw','cfp_forum_hstdn_rw'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on schema cfp_worker from %I', r);
      execute format('revoke all on all tables in schema cfp_worker from %I', r);
    end if;
  end loop;
end $$;
commit;
