-- CFP+ • 002 • Văn Phòng SI AI: schema cfp_office + role office_app (sinh từ services/forum/office.py)
-- Không chứa mật khẩu. Idempotent. Áp sau 001_isolation.sql.
begin;
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'office_app') then
    create role office_app nologin noinherit;
  end if;
end $$;
create schema if not exists cfp_office;
revoke all on schema cfp_office from public;
set local search_path = cfp_office;
CREATE TABLE IF NOT EXISTS audit_log (
	id SERIAL NOT NULL, 
	actor_id INTEGER, 
	action VARCHAR(40) NOT NULL, 
	ref VARCHAR(64) NOT NULL, 
	data TEXT NOT NULL, 
	at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE TABLE IF NOT EXISTS enterprises (
	id SERIAL NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	name_key VARCHAR(200) NOT NULL, 
	country_id VARCHAR(32) NOT NULL, 
	chapter VARCHAR(1) NOT NULL, 
	official_url VARCHAR(1000) NOT NULL, 
	source_url VARCHAR(1000) NOT NULL, 
	products TEXT NOT NULL, 
	capacity TEXT NOT NULL, 
	needs TEXT NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	created_by INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name_key, country_id)
);
CREATE TABLE IF NOT EXISTS links (
	id SERIAL NOT NULL, 
	from_ref VARCHAR(64) NOT NULL, 
	to_ref VARCHAR(64) NOT NULL, 
	relation VARCHAR(40) NOT NULL, 
	created_by INTEGER NOT NULL, 
	at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (from_ref, to_ref, relation)
);
CREATE TABLE IF NOT EXISTS office_roles (
	user_id INTEGER NOT NULL, 
	role VARCHAR(16) NOT NULL, 
	PRIMARY KEY (user_id, role)
);
CREATE TABLE IF NOT EXISTS offices (
	canonical_id VARCHAR(32) NOT NULL, 
	display_name VARCHAR(120) NOT NULL, 
	platform VARCHAR(120) NOT NULL, 
	specialties TEXT NOT NULL, 
	capabilities TEXT NOT NULL, 
	limits TEXT NOT NULL, 
	verification VARCHAR(40) NOT NULL, 
	created_by INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (canonical_id)
);
CREATE TABLE IF NOT EXISTS research_topics (
	id SERIAL NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	title_key VARCHAR(200) NOT NULL, 
	chapter VARCHAR(1) NOT NULL, 
	field VARCHAR(120) NOT NULL, 
	summary TEXT NOT NULL, 
	created_by INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (title_key, chapter)
);
CREATE TABLE IF NOT EXISTS brand_items (
	id SERIAL NOT NULL, 
	canonical_id VARCHAR(32) NOT NULL, 
	kind VARCHAR(16) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	name_key VARCHAR(160) NOT NULL, 
	description TEXT NOT NULL, 
	url VARCHAR(1000) NOT NULL, 
	source_type VARCHAR(24) NOT NULL, 
	source_url VARCHAR(1000) NOT NULL, 
	authorization_url VARCHAR(1000), 
	created_by INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (canonical_id, kind, name_key), 
	FOREIGN KEY(canonical_id) REFERENCES offices (canonical_id)
);
CREATE TABLE IF NOT EXISTS datasets (
	id SERIAL NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	kind VARCHAR(16) NOT NULL, 
	url VARCHAR(1000) NOT NULL, 
	author VARCHAR(200) NOT NULL, 
	version VARCHAR(64) NOT NULL, 
	source_url VARCHAR(1000) NOT NULL, 
	access VARCHAR(8) NOT NULL, 
	chapter VARCHAR(1) NOT NULL, 
	topic_id INTEGER, 
	created_by INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (url, version), 
	FOREIGN KEY(topic_id) REFERENCES research_topics (id)
);
CREATE TABLE IF NOT EXISTS office_maintainers (
	canonical_id VARCHAR(32) NOT NULL, 
	user_id INTEGER NOT NULL, 
	PRIMARY KEY (canonical_id, user_id), 
	FOREIGN KEY(canonical_id) REFERENCES offices (canonical_id)
);
CREATE TABLE IF NOT EXISTS super_pairs (
	id SERIAL NOT NULL, 
	canonical_id VARCHAR(32) NOT NULL, 
	software VARCHAR(160) NOT NULL, 
	software_key VARCHAR(160) NOT NULL, 
	lead_user_id INTEGER NOT NULL, 
	created_by INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (canonical_id, software_key), 
	FOREIGN KEY(canonical_id) REFERENCES offices (canonical_id)
);
CREATE TABLE IF NOT EXISTS tasks (
	id SERIAL NOT NULL, 
	pair_id INTEGER NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	acceptance TEXT NOT NULL, 
	assignee_id INTEGER NOT NULL, 
	reviewer_id INTEGER NOT NULL, 
	status VARCHAR(24) NOT NULL, 
	idempotency_key VARCHAR(80) NOT NULL, 
	created_by INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(pair_id) REFERENCES super_pairs (id), 
	UNIQUE (idempotency_key)
);
CREATE TABLE IF NOT EXISTS evidence (
	id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	kind VARCHAR(16) NOT NULL, 
	url VARCHAR(1000) NOT NULL, 
	sha VARCHAR(80), 
	description TEXT NOT NULL, 
	submitted_by INTEGER NOT NULL, 
	at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (task_id, url), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);
CREATE TABLE IF NOT EXISTS reviews (
	id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	reviewer_id INTEGER NOT NULL, 
	decision VARCHAR(24) NOT NULL, 
	notes TEXT NOT NULL, 
	at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);
CREATE TABLE IF NOT EXISTS task_events (
	id SERIAL NOT NULL, 
	task_id INTEGER NOT NULL, 
	actor_id INTEGER NOT NULL, 
	from_status VARCHAR(24), 
	to_status VARCHAR(24) NOT NULL, 
	note TEXT NOT NULL, 
	at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);
revoke all on cfp_office.audit_log from public;
alter table cfp_office.audit_log enable row level security;
alter table cfp_office.audit_log force row level security;
drop policy if exists office_app_all on cfp_office.audit_log;
create policy office_app_all on cfp_office.audit_log for all to office_app using (true) with check (true);
revoke all on cfp_office.enterprises from public;
alter table cfp_office.enterprises enable row level security;
alter table cfp_office.enterprises force row level security;
drop policy if exists office_app_all on cfp_office.enterprises;
create policy office_app_all on cfp_office.enterprises for all to office_app using (true) with check (true);
revoke all on cfp_office.links from public;
alter table cfp_office.links enable row level security;
alter table cfp_office.links force row level security;
drop policy if exists office_app_all on cfp_office.links;
create policy office_app_all on cfp_office.links for all to office_app using (true) with check (true);
revoke all on cfp_office.office_roles from public;
alter table cfp_office.office_roles enable row level security;
alter table cfp_office.office_roles force row level security;
drop policy if exists office_app_all on cfp_office.office_roles;
create policy office_app_all on cfp_office.office_roles for all to office_app using (true) with check (true);
revoke all on cfp_office.offices from public;
alter table cfp_office.offices enable row level security;
alter table cfp_office.offices force row level security;
drop policy if exists office_app_all on cfp_office.offices;
create policy office_app_all on cfp_office.offices for all to office_app using (true) with check (true);
revoke all on cfp_office.research_topics from public;
alter table cfp_office.research_topics enable row level security;
alter table cfp_office.research_topics force row level security;
drop policy if exists office_app_all on cfp_office.research_topics;
create policy office_app_all on cfp_office.research_topics for all to office_app using (true) with check (true);
revoke all on cfp_office.brand_items from public;
alter table cfp_office.brand_items enable row level security;
alter table cfp_office.brand_items force row level security;
drop policy if exists office_app_all on cfp_office.brand_items;
create policy office_app_all on cfp_office.brand_items for all to office_app using (true) with check (true);
revoke all on cfp_office.datasets from public;
alter table cfp_office.datasets enable row level security;
alter table cfp_office.datasets force row level security;
drop policy if exists office_app_all on cfp_office.datasets;
create policy office_app_all on cfp_office.datasets for all to office_app using (true) with check (true);
revoke all on cfp_office.office_maintainers from public;
alter table cfp_office.office_maintainers enable row level security;
alter table cfp_office.office_maintainers force row level security;
drop policy if exists office_app_all on cfp_office.office_maintainers;
create policy office_app_all on cfp_office.office_maintainers for all to office_app using (true) with check (true);
revoke all on cfp_office.super_pairs from public;
alter table cfp_office.super_pairs enable row level security;
alter table cfp_office.super_pairs force row level security;
drop policy if exists office_app_all on cfp_office.super_pairs;
create policy office_app_all on cfp_office.super_pairs for all to office_app using (true) with check (true);
revoke all on cfp_office.tasks from public;
alter table cfp_office.tasks enable row level security;
alter table cfp_office.tasks force row level security;
drop policy if exists office_app_all on cfp_office.tasks;
create policy office_app_all on cfp_office.tasks for all to office_app using (true) with check (true);
revoke all on cfp_office.evidence from public;
alter table cfp_office.evidence enable row level security;
alter table cfp_office.evidence force row level security;
drop policy if exists office_app_all on cfp_office.evidence;
create policy office_app_all on cfp_office.evidence for all to office_app using (true) with check (true);
revoke all on cfp_office.reviews from public;
alter table cfp_office.reviews enable row level security;
alter table cfp_office.reviews force row level security;
drop policy if exists office_app_all on cfp_office.reviews;
create policy office_app_all on cfp_office.reviews for all to office_app using (true) with check (true);
revoke all on cfp_office.task_events from public;
alter table cfp_office.task_events enable row level security;
alter table cfp_office.task_events force row level security;
drop policy if exists office_app_all on cfp_office.task_events;
create policy office_app_all on cfp_office.task_events for all to office_app using (true) with check (true);
grant usage on schema cfp_office to office_app;
grant select, insert, update, delete on all tables in schema cfp_office to office_app;
grant usage, select on all sequences in schema cfp_office to office_app;
-- Nhật ký kiểm toán, lịch sử, evidence, review: chỉ được thêm, không sửa/xoá.
revoke update, delete on cfp_office.audit_log from office_app;
revoke update, delete on cfp_office.task_events from office_app;
revoke update, delete on cfp_office.reviews from office_app;
revoke update, delete on cfp_office.evidence from office_app;
-- Vai trò governance/reviewer chỉ cấp qua CLI quản trị, app không tự cấp.
revoke insert, update, delete on cfp_office.office_roles from office_app;
-- Đường cấp vai trò duy nhất: role office_governance (NOLOGIN). Người vận hành Human Governance
-- được cấp membership riêng; CLI dùng SET ROLE office_governance. RLS FORCE vẫn chặn mọi role khác.
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'office_governance') then
    create role office_governance nologin noinherit;
  end if;
end $$;
grant usage on schema cfp_office to office_governance;
grant select, insert, delete on cfp_office.office_roles to office_governance;
drop policy if exists office_governance_roles on cfp_office.office_roles;
create policy office_governance_roles on cfp_office.office_roles for all to office_governance using (true) with check (true);
alter role office_app set search_path = cfp_office;
do $$ declare r text; begin
  foreach r in array array['anon','authenticated','forum_auth_app','forum_sbd_app','forum_hstdn_app'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke all on schema cfp_office from %I', r);
      execute format('revoke all on all tables in schema cfp_office from %I', r);
    end if;
  end loop;
end $$;
commit;
