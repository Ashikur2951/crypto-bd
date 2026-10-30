import time, httpx
BASE = "https://fapi.binance.com"
class DataError(Exception): pass
_cache = {}
def _get(path, params=None, ttl=0):
    key = (path, tuple(sorted((params or {}).items())))
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < ttl: return hit[1]
    for attempt in range(2):
        try: r = httpx.get(BASE + path, params=params, timeout=10)
        except httpx.HTTPError as e: raise DataError("network_error") from e
        if r.status_code == 429 and attempt == 0: time.sleep(2); continue
        break
    if r.status_code == 418: raise DataError("ip_banned_temporarily")
    if r.status_code == 429: raise DataError("rate_limited")
    if r.status_code != 200: raise DataError(f"http_{r.status_code}")
    data = r.json()
    if ttl:
        if len(_cache) > 300: _cache.clear()
        _cache[key] = (time.time(), data)
    return data
def symbols():
    d = _get("/fapi/v1/exchangeInfo", ttl=600)
    return sorted(s["symbol"] for s in d["symbols"] if s["status"] == "TRADING" and s["quoteAsset"] == "USDT" and s["contractType"] == "PERPETUAL")
def klines(symbol, interval, limit=300):
    raw = _get("/fapi/v1/klines", {"symbol": symbol, "interval": interval, "limit": limit}, ttl=50)
    return [[k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5]), k[6]] for k in raw][:-1]  # drop open candle
