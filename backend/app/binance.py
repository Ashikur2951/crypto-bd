import httpx
BASE = "https://fapi.binance.com"
class DataError(Exception): pass
def _get(path, params=None):
    try: r = httpx.get(BASE + path, params=params, timeout=10)
    except httpx.HTTPError as e: raise DataError("network_error") from e
    if r.status_code in (418, 429): raise DataError("rate_limited")
    if r.status_code != 200: raise DataError(f"http_{r.status_code}")
    return r.json()
def symbols():
    d = _get("/fapi/v1/exchangeInfo")
    return sorted(s["symbol"] for s in d["symbols"] if s["status"] == "TRADING" and s["quoteAsset"] == "USDT" and s["contractType"] == "PERPETUAL")
def klines(symbol, interval, limit=300):
    raw = _get("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    return [[k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5]), k[6]] for k in raw][:-1]  # drop open candle
