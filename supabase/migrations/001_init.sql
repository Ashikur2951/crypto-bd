create table if not exists public.signals (id bigint generated always as identity primary key, symbol text not null, timeframe text not null check (timeframe in ('15m','1h','4h')),
 direction text not null check (direction in ('LONG','SHORT','WAIT')), entry numeric, stop_loss numeric, take_profit jsonb, candle_time bigint not null, payload jsonb, created_at timestamptz default now(),
 unique (symbol, timeframe, candle_time));
create index if not exists signals_idx on public.signals (symbol, timeframe, created_at desc);
create table if not exists public.paper_trades (id bigint generated always as identity primary key, signal_id bigint unique references public.signals(id), status text not null default 'open' check (status in ('open','tp','sl','expired')), pnl_pct numeric, created_at timestamptz default now());
create table if not exists public.backtests (id bigint generated always as identity primary key, symbol text, timeframe text, summary jsonb not null, created_at timestamptz default now());
create table if not exists public.app_settings (key text primary key, value jsonb not null, is_public boolean not null default false);
alter table public.signals enable row level security; alter table public.paper_trades enable row level security;
alter table public.backtests enable row level security; alter table public.app_settings enable row level security;
drop policy if exists "public read signals" on public.signals; create policy "public read signals" on public.signals for select using (true);
drop policy if exists "public read settings" on public.app_settings; create policy "public read settings" on public.app_settings for select using (is_public);
-- No insert/update/delete policies: only the backend (service role, private env var) may write.
