def pnl(d, entry, exit_, fee): return d * (exit_ - entry) / entry - 2 * fee
def settle(t, cs):
    """t: open paper trade dict; cs: closed candles. SL is checked before TP (conservative). Returns (status, pnl_pct) or None."""
    d = 1 if t["direction"] == "LONG" else -1
    for c in cs:
        if c[0] <= t["candle_time"]: continue
        if (d == 1 and c[3] <= t["stop_loss"]) or (d == -1 and c[2] >= t["stop_loss"]): return "sl", pnl(d, t["entry"], t["stop_loss"], t["fee"])
        if (d == 1 and c[2] >= t["take_profit1"]) or (d == -1 and c[3] <= t["take_profit1"]): return "tp", pnl(d, t["entry"], t["take_profit1"], t["fee"])
    return None
