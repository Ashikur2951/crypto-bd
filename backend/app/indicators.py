def ema(v, n):
    if len(v) < n: return []
    k = 2 / (n + 1); out = [sum(v[:n]) / n]
    for x in v[n:]: out.append(x * k + out[-1] * (1 - k))
    return [None] * (n - 1) + out
def rsi(c, n=14):
    if len(c) <= n: return []
    g = [max(c[i] - c[i-1], 0) for i in range(1, len(c))]; l = [max(c[i-1] - c[i], 0) for i in range(1, len(c))]
    ag, al = sum(g[:n]) / n, sum(l[:n]) / n; out = [None] * n
    for i in range(n, len(g) + 1):
        if i > n: ag, al = (ag*(n-1)+g[i-1])/n, (al*(n-1)+l[i-1])/n
        out.append(100.0 if al == 0 else 100 - 100 / (1 + ag / al))
    return out
def macd(c, f=12, s=26, sig=9):
    ef, es = ema(c, f), ema(c, s)
    line = [a - b for a, b in zip(ef, es) if a is not None and b is not None]
    sg = ema(line, sig); pad = len(c) - len(line)
    hist = [None if x is None else line[i] - x for i, x in enumerate(sg)]
    return [None]*pad + line, [None]*pad + sg, [None]*pad + hist
def atr(h, l, c, n=14):
    if len(c) <= n: return []
    tr = [max(h[i]-l[i], abs(h[i]-c[i-1]), abs(l[i]-c[i-1])) for i in range(1, len(c))]
    a = sum(tr[:n]) / n; out = [None]*n + [a]
    for x in tr[n:]: a = (a*(n-1)+x)/n; out.append(a)
    return out
