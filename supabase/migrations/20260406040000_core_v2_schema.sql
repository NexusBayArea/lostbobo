-- Enable Extensions
create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

-- 1. Profiles (extends Supabase auth)
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  plan text default 'free', -- free | pro | enterprise
  created_at timestamptz default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$ language plpgsql;

-- Avoid duplicate trigger error
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

-- 2. Onboarding State
create table if not exists public.onboarding_state (
  user_id uuid primary key references public.profiles(id) on delete cascade,
  step text,
  data jsonb default '{}'::jsonb,
  completed boolean default false,
  updated_at timestamptz default now()
);

-- 3. Simulations (core entity)
create table if not exists public.simulations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade,

  status text check (status in ('queued','running','completed','failed')) default 'queued',

  input jsonb,
  output jsonb,
  error text,

  runpod_job_id text, -- external mapping

  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Auto-update timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

-- Avoid duplicate trigger error
drop trigger if exists update_simulations_updated_at on public.simulations;
create trigger update_simulations_updated_at
before update on public.simulations
for each row execute procedure update_updated_at_column();

-- 4. Usage Tracking
create table if not exists public.usage_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade,

  simulation_id uuid references public.simulations(id) on delete cascade,

  event_type text, -- run_started, run_completed, run_failed
  created_at timestamptz default now()
);

-- 5. Weekly Usage View
-- Using OR REPLACE for views
create or replace view public.weekly_usage as
select
  user_id,
  count(*) as runs_this_week
from public.usage_events
where event_type = 'run_started'
  and created_at >= date_trunc('week', now())
group by user_id;

-- 6. Enforce Free Tier Limit (10/week)
create or replace function public.check_usage_limit(p_user_id uuid)
returns boolean as $$
declare
  run_count int;
  user_plan text;
begin
  select plan into user_plan from public.profiles where id = p_user_id;

  select count(*) into run_count
  from public.usage_events
  where user_id = p_user_id
    and event_type = 'run_started'
    and created_at >= date_trunc('week', now());

  if user_plan = 'free' and run_count >= 10 then
    return false;
  end if;

  return true;
end;
$$ language plpgsql;

-- 7. Hard Enforcement via RPC
create or replace function public.can_run_simulation(p_user_id uuid)
returns json as $$
begin
  if not public.check_usage_limit(p_user_id) then
    return json_build_object(
      'allowed', false,
      'reason', 'weekly_limit_reached'
    );
  end if;

  return json_build_object('allowed', true);
end;
$$ language plpgsql;

-- 8. Billing
create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade,

  stripe_customer_id text,
  stripe_subscription_id text,

  status text, -- active, canceled, trialing
  plan text,   -- pro, enterprise

  current_period_end timestamptz,

  created_at timestamptz default now()
);

-- 9. RLS (Row Level Security)
alter table public.profiles enable row level security;
alter table public.onboarding_state enable row level security;
alter table public.simulations enable row level security;
alter table public.usage_events enable row level security;
alter table public.subscriptions enable row level security;

-- Policies (DROP and CREATE to avoid "already exists")
-- Profiles
drop policy if exists "Users can view own profile" on public.profiles;
create policy "Users can view own profile"
on public.profiles
for select using (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.profiles;
create policy "Users can update own profile"
on public.profiles
for update using (auth.uid() = id);

-- Onboarding
drop policy if exists "Users manage onboarding" on public.onboarding_state;
create policy "Users manage onboarding"
on public.onboarding_state
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

-- Simulations
drop policy if exists "Users manage simulations" on public.simulations;
create policy "Users manage simulations"
on public.simulations
for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

-- Usage
drop policy if exists "Users view usage" on public.usage_events;
create policy "Users view usage"
on public.usage_events
for select using (auth.uid() = user_id);

-- Subscriptions
drop policy if exists "Users view subscription" on public.subscriptions;
create policy "Users view subscription"
on public.subscriptions
for select using (auth.uid() = user_id);
