import os, httpx
def enabled(): return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"))
def req(method, path, headers=None, **kw):
    k = os.getenv("SUPABASE_SERVICE_KEY", "")
    h = {"apikey": k, "Authorization": "Bearer " + k, "Content-Type": "application/json", **(headers or {})}
    r = httpx.request(method, os.getenv("SUPABASE_URL", "").rstrip("/") + "/rest/v1/" + path, headers=h, timeout=15, **kw)
    r.raise_for_status()
    return r.json() if r.text else None
