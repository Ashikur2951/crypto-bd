"""Deterministic rules. LONG: higher-TF trends up (EMA20>EMA50), own EMA20>EMA50, RSI 50-70, MACD hist>0, volume>=avg20.
SHORT is the mirror (RSI 30-50, hist<0). Otherwise WAIT. SL = entry -/+ 1.5*ATR, TP1 = 1.5R, TP2 = 3R."""
from .indicators import ema, rsi, macd, atr
P = {"atr_sl": 1.5, "rr1": 1.5, "rr2": 3.0, "min_candles": 120, "vol_mult": 1.0}
def _ok(cs, n):
    return bool(cs) and len(cs) >= n and all(len(x) >= 6 and x[2] >= x[3] and x[4] > 0 for x in cs)
def trend(cs):
    c = [x[4] for x in cs]; a, b = ema(c, 20), ema(c, 50)
    if not a or not b or a[-1] is None or b[-1] is None: return None
    return "UP" if a[-1] > b[-1] else "DOWN"
def generate(cs, htf=(), p=P):
    """cs: [[time,o,h,l,c,v],...] CLOSED candles only."""
    if not _ok(cs, p["min_candles"]) or any(not _ok(x, p["min_candles"]) for x in htf):
        return {"direction": "WAIT", "reason": "insufficient_or_invalid_data"}
    c = [x[4] for x in cs]; h = [x[2] for x in cs]; l = [x[3] for x in cs]; v = [x[5] for x in cs]
    e20, e50 = ema(c, 20)[-1], ema(c, 50)[-1]; r = rsi(c)[-1]; hist = macd(c)[2][-1]; a = atr(h, l, c)[-1]
    if None in (e20, e50, r, hist, a) or a <= 0: return {"direction": "WAIT", "reason": "indicators_unavailable"}
    volok = v[-1] >= p["vol_mult"] * (sum(v[-21:-1]) / 20)
    trends = [trend(x) for x in htf]; d = "WAIT"
    if e20 > e50 and 50 <= r <= 70 and hist > 0 and volok and all(t == "UP" for t in trends): d = "LONG"
    elif e20 < e50 and 30 <= r <= 50 and hist < 0 and volok and all(t == "DOWN" for t in trends): d = "SHORT"
    ind = {"ema20": e20, "ema50": e50, "rsi": r, "macd_hist": hist, "atr": a, "volume_ok": volok, "htf_trends": trends}
    if d == "WAIT": return {"direction": "WAIT", "reason": "rules_not_met", "indicators": ind}
    e = c[-1]; s = 1 if d == "LONG" else -1; risk = p["atr_sl"] * a
    return {"direction": d, "entry": e, "stop_loss": e - s*risk, "take_profit": [e + s*risk*p["rr1"], e + s*risk*p["rr2"]],
            "risk_reward": p["rr1"], "candle_time": cs[-1][0], "indicators": ind,
            "invalidation": "Invalid if price closes beyond stop loss or signal is older than 3 candles."}
def backtest(cs, fee=0.0004, slip=0.0002, p=P, warm=120):
    """Walk-forward: decision at candle i uses only cs[:i+1]; exits simulated on later candles (SL checked first). Single-timeframe."""
    trades, eq, peak, mdd, i = [], 1.0, 1.0, 0.0, warm
    while i < len(cs) - 1:
        s = generate(cs[:i+1], (), p)
        if s["direction"] == "WAIT": i += 1; continue
        d = 1 if s["direction"] == "LONG" else -1; ent = cs[i][4] * (1 + d*slip); sl, tp = s["stop_loss"], s["take_profit"][0]; out = None; j = i + 1
        while j < len(cs):
            hi, lo = cs[j][2], cs[j][3]
            if (d == 1 and lo <= sl) or (d == -1 and hi >= sl): out = sl; break
            if (d == 1 and hi >= tp) or (d == -1 and lo <= tp): out = tp; break
            j += 1
        if out is None: break
        ret = d * (out * (1 - d*slip) - ent) / ent - 2*fee
        eq *= 1 + ret; peak = max(peak, eq); mdd = max(mdd, (peak - eq) / peak); trades.append(ret); i = j + 1
    w = [t for t in trades if t > 0]
    return {"trades": len(trades), "win_rate": len(w)/len(trades) if trades else None, "total_return": eq - 1, "max_drawdown": mdd,
            "fee_per_side": fee, "slippage": slip, "simulated": True}
