-- TechEvents Peru - explicit grants and Row Level Security
-- Run after database/schema.sql in RECOPILAR_LINK > SQL Editor.

begin;

alter table public.events enable row level security;
alter table public.event_sources enable row level security;
alter table public.scraping_logs enable row level security;

revoke all on table public.events from anon, authenticated;
revoke all on table public.event_sources from anon, authenticated;
revoke all on table public.scraping_logs from anon, authenticated;
revoke all on sequence public.scraping_logs_id_seq from anon, authenticated;

grant select on table public.events to anon, authenticated;

drop policy if exists "Public can read published events" on public.events;
create policy "Public can read published events"
on public.events
for select
to anon, authenticated
using (status = 'published');

-- No client policy exists for INSERT, UPDATE or DELETE. A backend secret key
-- uses service_role and bypasses RLS; it must never be exposed to a browser.

commit;
