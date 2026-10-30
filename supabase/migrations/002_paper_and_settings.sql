alter table public.paper_trades add column if not exists symbol text;
alter table public.paper_trades add column if not exists timeframe text;
alter table public.paper_trades add column if not exists direction text;
alter table public.paper_trades add column if not exists entry numeric;
alter table public.paper_trades add column if not exists stop_loss numeric;
alter table public.paper_trades add column if not exists take_profit1 numeric;
alter table public.paper_trades add column if not exists candle_time bigint;
alter table public.paper_trades add column if not exists fee numeric default 0.0004;
create index if not exists paper_status_idx on public.paper_trades (status, created_at desc);
drop policy if exists "public read paper trades" on public.paper_trades;
create policy "public read paper trades" on public.paper_trades for select using (true);
insert into public.app_settings (key, value, is_public) values
 ('enabled_symbols','["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT","LTCUSDT"]',true),
 ('timeframes','["15m","1h","4h"]',true), ('params','{}',true), ('paper_fee','0.0004',true)
on conflict (key) do nothing;
