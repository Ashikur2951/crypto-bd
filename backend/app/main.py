import os, hmac, time
from fastapi import FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from . import binance, engine
TFS = {"15m": ["1h", "4h"], "1h": ["4h"], "4h": []}
app = FastAPI(title="Crypto Signal BD")
app.add_middleware(CORSMiddleware, allow_origins=[o for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o],
                   allow_methods=["GET", "POST", "PUT"], allow_headers=["*"])
from .ops import router
app.include_router(router)
_cache = {}
def _symbols():
    t = _cache.get("s")
    if not t or time.time() - t[0] > 600: _cache["s"] = (time.time(), binance.symbols())
    return _cache["s"][1]
def _check(symbol, tf):
    if tf not in TFS: raise HTTPException(422, "invalid timeframe")
    if symbol not in _symbols(): raise HTTPException(404, "symbol not tradable on Binance USDⓈ-M")
@app.get("/health")
def health(): return {"status": "ok", "time": int(time.time())}
@app.get("/api/symbols")
def symbols():
    try: return {"symbols": _symbols(), "source": "binance-live"}
    except binance.DataError as e: raise HTTPException(503, str(e))
@app.get("/api/signal")
def signal(symbol: str = Query(pattern="^[A-Z0-9]{3,20}$"), timeframe: str = "15m"):
    try:
        _check(symbol, timeframe)
        cs = binance.klines(symbol, timeframe); htf = [binance.klines(symbol, x) for x in TFS[timeframe]]
    except binance.DataError as e: raise HTTPException(503, f"market data unavailable: {e}")
    s = engine.generate(cs, htf)
    return {**s, "symbol": symbol, "timeframe": timeframe, "price": cs[-1][4] if cs else None, "generated_at": int(time.time()), "source": "binance-live"}
@app.get("/api/backtest")
def backtest(symbol: str = Query(pattern="^[A-Z0-9]{3,20}$"), timeframe: str = "1h"):
    try: _check(symbol, timeframe); cs = binance.klines(symbol, timeframe, 1000)
    except binance.DataError as e: raise HTTPException(503, f"market data unavailable: {e}")
    return {**engine.backtest(cs), "symbol": symbol, "timeframe": timeframe, "candles": len(cs), "period": [cs[0][0], cs[-1][0]] if cs else None}
@app.get("/api/admin/ping")
def admin_ping(x_admin_token: str = Header(default="")):
    tok = os.getenv("ADMIN_TOKEN", "")
    if not tok or not hmac.compare_digest(x_admin_token, tok): raise HTTPException(401, "unauthorized")
    return {"admin": True}
