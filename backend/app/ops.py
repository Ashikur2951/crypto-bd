import os, hmac, re, time
from fastapi import APIRouter, HTTPException, Header, Body, Query, BackgroundTasks
from . import binance, engine, db, paper
router = APIRouter()
HTF = {"15m": ["1h", "4h"], "1h": ["4h"], "4h": []}
DEFAULTS = {"enabled_symbols": ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT","LTCUSDT"],
            "timeframes": ["15m", "1h", "4h"], "params": {}, "paper_fee": 0.0004}
def _auth(tok, env):
    t = os.getenv(env, "")
    if not t or not hmac.compare_digest(tok, t): raise HTTPException(401, "unauthorized")
def settings():
    s = dict(DEFAULTS)
    if db.enabled():
        for r in db.req("GET", "app_settings?select=key,value") or []:
            if r["key"] in s: s[r["key"]] = r["value"]
    return s
def _save(key, value, public):
    db.req("POST", "app_settings?on_conflict=key", json={"key": key, "value": value, "is_public": public}, headers={"Prefer": "resolution=merge-duplicates"})
@router.get("/api/klines")
def klines(symbol: str = Query(pattern="^[A-Z0-9]{3,20}$"), timeframe: str = Query(pattern="^(15m|1h|4h)$")):
    try: return {"candles": binance.klines(symbol, timeframe, 80), "source": "binance-live", "fetched_at": int(time.time())}
    except binance.DataError as e: raise HTTPException(503, f"market data unavailable: {e}")
def _cron_job():
    s = settings(); fee = s["paper_fee"]
    p = {**engine.P, **{k: v for k, v in s["params"].items() if k in engine.P}}
    cache = {}
    def kl(sym, tf):
        if (sym, tf) not in cache: cache[(sym, tf)] = binance.klines(sym, tf)
        return cache[(sym, tf)]
    res = {"new_signals": 0, "settled": 0, "errors": []}
    for sym in s["enabled_symbols"]:
        for tf in s["timeframes"]:
            try:
                sig = engine.generate(kl(sym, tf), [kl(sym, x) for x in HTF[tf]], p)
                if sig["direction"] == "WAIT": continue
                row = db.req("POST", "signals?on_conflict=symbol,timeframe,candle_time", headers={"Prefer": "resolution=ignore-duplicates,return=representation"},
                    json={"symbol": sym, "timeframe": tf, "direction": sig["direction"], "entry": sig["entry"], "stop_loss": sig["stop_loss"],
                          "take_profit": sig["take_profit"], "candle_time": sig["candle_time"], "payload": sig})
                if row:  # new signal only -> no duplicate paper trades on retries
                    db.req("POST", "paper_trades?on_conflict=signal_id", headers={"Prefer": "resolution=ignore-duplicates"},
                        json={"signal_id": row[0]["id"], "symbol": sym, "timeframe": tf, "direction": sig["direction"], "entry": sig["entry"],
                              "stop_loss": sig["stop_loss"], "take_profit1": sig["take_profit"][0], "candle_time": sig["candle_time"], "fee": fee})
                    res["new_signals"] += 1
            except Exception as e: res["errors"].append(f"{sym}/{tf}: {type(e).__name__}")
    try:
        for t in db.req("GET", "paper_trades?status=eq.open&select=*") or []:
            out = paper.settle({**t, "entry": float(t["entry"]), "stop_loss": float(t["stop_loss"]), "take_profit1": float(t["take_profit1"]), "fee": float(t["fee"])}, kl(t["symbol"], t["timeframe"]))
            if out:
                db.req("PATCH", f"paper_trades?id=eq.{t['id']}", json={"status": out[0], "pnl_pct": out[1] * 100}); res["settled"] += 1
    except Exception as e: res["errors"].append(f"settle: {type(e).__name__}")
    _save("last_run", {"at": int(time.time()), "new_signals": res["new_signals"], "ok": not res["errors"]}, True)
    _save("last_run_errors", res["errors"][:20], False)
    return res
@router.get("/api/admin/settings")
def get_settings(x_admin_token: str = Header(default="")):
    _auth(x_admin_token, "ADMIN_TOKEN"); out = settings()
    if db.enabled():
        r = db.req("GET", "app_settings?key=eq.last_run_errors&select=value"); out["recent_errors"] = r[0]["value"] if r else []
    return out
@router.put("/api/admin/settings")
def put_settings(body: dict = Body(...), x_admin_token: str = Header(default="")):
    _auth(x_admin_token, "ADMIN_TOKEN")
    if not db.enabled(): raise HTTPException(503, "database not configured")
    k, v = body.get("key"), body.get("value")
    if k == "enabled_symbols": ok = isinstance(v, list) and 0 < len(v) <= 30 and all(isinstance(x, str) and re.fullmatch(r"[A-Z0-9]{3,20}", x) for x in v) and set(v) <= set(binance.symbols())
    elif k == "timeframes": ok = isinstance(v, list) and bool(v) and set(v) <= set(HTF)
    elif k == "params": ok = isinstance(v, dict) and all(a in engine.P and isinstance(b, (int, float)) and 0 < b <= 1000 for a, b in v.items())
    elif k == "paper_fee": ok = isinstance(v, (int, float)) and 0 <= v < 0.01
    else: ok = False
    if not ok: raise HTTPException(422, "invalid setting")
    _save(k, v, True); return {"saved": k}
@router.post("/api/cron/run")
def cron(bg: BackgroundTasks, x_cron_token: str = Header(default="")):
    _auth(x_cron_token, "CRON_TOKEN")
    if not db.enabled(): raise HTTPException(503, "database not configured")
    bg.add_task(_cron_job)
    return {"started": True}
