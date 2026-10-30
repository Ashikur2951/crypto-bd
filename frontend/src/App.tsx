import { useEffect, useState } from "react";
const API = import.meta.env.VITE_API_URL as string;
const SB = import.meta.env.VITE_SUPABASE_URL as string, KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string;
const sb = (p: string) => fetch(`${SB}/rest/v1/${p}`, { headers: { apikey: KEY } }).then(r => { if (!r.ok) throw 0; return r.json(); });
const api = (p: string, o?: RequestInit) => fetch(API + p, o).then(async r => { const j = await r.json().catch(() => ({})); if (!r.ok) throw new Error(j.detail || String(r.status)); return j; });
const COINS = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT","LTCUSDT"];
const L: any = { bn: { title: "ক্রিপ্টো সিগন্যাল বিডি", load: "লোড হচ্ছে…", err: "সার্ভিস এখন পাওয়া যাচ্ছে না", empty: "কোনো তথ্য নেই", disc: "এই সিগন্যাল শুধু তথ্যের জন্য; লাভের নিশ্চয়তা নেই। পেপার ট্রেড/ব্যাকটেস্ট সিমুলেটেড।", sl: "স্টপ লস", tp: "টেক প্রফিট", entry: "এন্ট্রি", tabs: ["সিগন্যাল", "হিস্টোরি", "পেপার", "ব্যাকটেস্ট", "অ্যাডমিন"] },
  en: { title: "Crypto Signal BD", load: "Loading…", err: "Service unavailable right now", empty: "No data", disc: "Signals are informational only; no profit is guaranteed. Paper trades and backtests are simulated.", sl: "Stop Loss", tp: "Take Profit", entry: "Entry", tabs: ["Signal", "History", "Paper", "Backtest", "Admin"] } };
const fmt = (n: any) => (n == null ? "-" : Number(n).toFixed(4));
const when = (s: number) => new Date(s * 1000).toLocaleString();
function useLoad<T>(fn: () => Promise<T>, deps: any[]) {
  const [d, setD] = useState<T | null>(null); const [err, setErr] = useState(false); const [busy, setBusy] = useState(true);
  useEffect(() => { setBusy(true); setErr(false); fn().then(setD).catch(() => { setErr(true); setD(null); }).finally(() => setBusy(false)); }, deps);
  return { d, err, busy };
}
function Chart({ c }: { c: number[][] }) {
  const hi = Math.max(...c.map(x => x[2])), lo = Math.min(...c.map(x => x[3])), W = 440, H = 200, w = W / c.length, y = (v: number) => H - ((v - lo) / (hi - lo || 1)) * H;
  return <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", background: "#111" }}>{c.map((k, i) => { const up = k[4] >= k[1], col = up ? "#26a69a" : "#ef5350";
    return <g key={i}><line x1={i*w+w/2} x2={i*w+w/2} y1={y(k[2])} y2={y(k[3])} stroke={col} /><rect x={i*w+1} width={w-2} y={y(Math.max(k[1],k[4]))} height={Math.max(1, Math.abs(y(k[1])-y(k[4])))} fill={col} /></g>; })}</svg>;
}
function Sel({ v, set, o }: { v: string; set: (s: string) => void; o: string[] }) { return <select value={v} onChange={e => set(e.target.value)}>{o.map(x => <option key={x}>{x}</option>)}</select>; }
export default function App() {
  const [lang, setLang] = useState("bn"); const t = L[lang]; const [tab, setTab] = useState(0);
  const [sym, setSym] = useState("BTCUSDT"); const [tf, setTf] = useState("1h"); const [q, setQ] = useState(""); const [all, setAll] = useState(COINS);
  const [hs, setHs] = useState(""); const [ht, setHt] = useState(""); const [hd, setHd] = useState(""); const [hdate, setHdate] = useState("");
  const [tok, setTok] = useState(""); const [sym2, setSym2] = useState(""); const [msg, setMsg] = useState("");
  useEffect(() => { api("/api/symbols").then(j => j.symbols && setAll(j.symbols)).catch(() => {}); }, []);
  const sig = useLoad(() => tab === 0 ? api(`/api/signal?symbol=${sym}&timeframe=${tf}`) : Promise.resolve(null), [sym, tf, tab]);
  const kl = useLoad(() => tab === 0 ? api(`/api/klines?symbol=${sym}&timeframe=${tf}`) : Promise.resolve(null), [sym, tf, tab]);
  const hist = useLoad(() => tab === 1 ? sb(`signals?select=*&order=created_at.desc&limit=50${hs ? `&symbol=eq.${hs}` : ""}${ht ? `&timeframe=eq.${ht}` : ""}${hd ? `&direction=eq.${hd}` : ""}${hdate ? `&created_at=gte.${hdate}` : ""}`) : Promise.resolve(null), [tab, hs, ht, hd, hdate]);
  const pap = useLoad(() => tab === 2 ? Promise.all([sb("paper_trades?select=*&order=created_at.desc&limit=50"), sb("app_settings?key=eq.last_run&select=value")]) : Promise.resolve(null), [tab]);
  const bt = useLoad(() => tab === 3 ? api(`/api/backtest?symbol=${sym}&timeframe=${tf}`) : Promise.resolve(null), [sym, tf, tab]);
  const list = (q ? all.filter(s => s.includes(q.toUpperCase())) : [...COINS.filter(c => all.includes(c)), ...all.filter(s => !COINS.includes(s))]).slice(0, 80); const d: any = sig.d; const age = d ? Math.round((Date.now() / 1000 - d.generated_at) / 60) : 0;
  const st = (x: { busy: boolean; err: boolean }) => x.busy ? <p>{t.load}</p> : x.err ? <p style={{ color: "red" }}>{t.err}</p> : null;
  const admin = async (method: string, body?: any) => { try { const j = await api("/api/admin/settings", { method, headers: { "x-admin-token": tok, "Content-Type": "application/json" }, body: body && JSON.stringify(body) }); setMsg(JSON.stringify(j)); } catch (e: any) { setMsg("✗ " + e.message); } };
  return (<div style={{ maxWidth: 520, margin: "auto", padding: 12, fontFamily: "sans-serif" }}>
    <h1 style={{ fontSize: 22 }}>{t.title}</h1><button onClick={() => setLang(lang === "bn" ? "en" : "bn")}>{lang === "bn" ? "English" : "বাংলা"}</button>
    <div style={{ display: "flex", gap: 4, flexWrap: "wrap", margin: "8px 0" }}>{t.tabs.map((x: string, i: number) => <button key={i} onClick={() => setTab(i)} style={{ fontWeight: tab === i ? "bold" : "normal" }}>{x}</button>)}</div>
    {(tab === 0 || tab === 3) && <p><input placeholder="search" size={8} value={q} onChange={e => setQ(e.target.value)} /> <Sel v={sym} set={setSym} o={list.includes(sym) ? list : [sym, ...list]} /> <Sel v={tf} set={setTf} o={["15m", "1h", "4h"]} /></p>}
    {tab === 0 && <>{st(sig)}{d && !sig.busy && <div style={{ border: "1px solid #888", borderRadius: 8, padding: 12 }}>
      <h2 className={"dir " + d.direction}>{d.direction}</h2><p>Price: {d.price} · Live (Binance) · {age}m ago {age > 20 && "⚠ stale"}</p>
      {d.entry && <><p>{t.entry}: {fmt(d.entry)} · {t.sl}: {fmt(d.stop_loss)}</p><p>{t.tp}: {d.take_profit.map(fmt).join(" / ")} · R:R {d.risk_reward}</p><p style={{ fontSize: 12 }}>{d.invalidation}</p></>}
      {d.reason && <p>{d.reason}</p>}
      {d.indicators && <p style={{ fontSize: 12 }}>EMA20 {fmt(d.indicators.ema20)} · EMA50 {fmt(d.indicators.ema50)} · RSI {fmt(d.indicators.rsi)} · MACD-h {fmt(d.indicators.macd_hist)} · ATR {fmt(d.indicators.atr)} · Vol {String(d.indicators.volume_ok)} · HTF {d.indicators.htf_trends.join("/") || "-"}</p>}</div>}
      {kl.d && <Chart c={(kl.d as any).candles} />}</>}
    {tab === 1 && <><p><Sel v={hs} set={setHs} o={["", ...COINS]} /> <Sel v={ht} set={setHt} o={["", "15m", "1h", "4h"]} /> <Sel v={hd} set={setHd} o={["", "LONG", "SHORT"]} /> <input type="date" value={hdate} onChange={e => setHdate(e.target.value)} /></p>{st(hist)}
      {hist.d && ((hist.d as any[]).length === 0 ? <p>{t.empty}</p> : (hist.d as any[]).map(r => <p key={r.id} style={{ borderBottom: "1px solid #ccc" }}><b>{r.direction}</b> {r.symbol} {r.timeframe} · {fmt(r.entry)} / SL {fmt(r.stop_loss)}<br /><small>{new Date(r.created_at).toLocaleString()}</small></p>))}</>}
    {tab === 2 && <>{st(pap)}{pap.d && <>{(pap.d as any)[1][0] && <p style={{ fontSize: 12 }}>Last update: {when((pap.d as any)[1][0].value.at)} {Date.now() / 1000 - (pap.d as any)[1][0].value.at > 1800 && "⚠ stale"}</p>}
      <p>SIMULATED</p>{(pap.d as any)[0].length === 0 ? <p>{t.empty}</p> : (pap.d as any)[0].map((r: any) => <p key={r.id} style={{ borderBottom: "1px solid #ccc" }}>{r.symbol} {r.timeframe} {r.direction} · {r.status.toUpperCase()} {r.pnl_pct != null && `${Number(r.pnl_pct).toFixed(2)}%`}</p>)}</>}</>}
    {tab === 3 && <>{st(bt)}{bt.d && <pre style={{ whiteSpace: "pre-wrap" }}>{(() => { const b: any = bt.d; return `Simulated · ${b.candles} candles\nTrades: ${b.trades}\nWin rate: ${b.win_rate == null ? "n/a" : (b.win_rate * 100).toFixed(1) + "%"}\nReturn: ${(b.total_return * 100).toFixed(2)}%\nMax drawdown: ${(b.max_drawdown * 100).toFixed(2)}%\nFee/side ${b.fee_per_side * 100}% · slippage ${b.slippage * 100}%\nPeriod: ${when(b.period[0] / 1000)} → ${when(b.period[1] / 1000)}`; })()}</pre>}</>}
    {tab === 4 && <><p><input type="password" placeholder="ADMIN_TOKEN" value={tok} onChange={e => setTok(e.target.value)} /> <button onClick={() => admin("GET")}>Load</button></p>
      <p><input placeholder="BTCUSDT,ETHUSDT,…" value={sym2} onChange={e => setSym2(e.target.value)} /> <button onClick={() => admin("PUT", { key: "enabled_symbols", value: sym2.split(",").map(s => s.trim().toUpperCase()).filter(Boolean) })}>Save coins</button></p>
      <p><button onClick={() => admin("PUT", { key: "timeframes", value: ["15m", "1h", "4h"] })}>All timeframes</button> <button onClick={() => admin("PUT", { key: "timeframes", value: ["1h", "4h"] })}>1h+4h only</button></p>
      <pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>{msg}</pre></>}
    <p style={{ fontSize: 12 }}>{t.disc}</p></div>);
}
