import time

import httpx

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
PARAMS = {"id": "GGGDTAINA188N"}

AGENTS = {
    "chrome-ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "curl-ua": "curl/8.4.0",
    "app-ua": "EconomicIndicatorsDashboard/1.0 (interview project)",
}


def attempt(name: str, **client_kwargs) -> None:
    ua = client_kwargs.pop("ua")
    start = time.time()
    try:
        with httpx.Client(timeout=20, headers={"User-Agent": ua, "Accept": "*/*"}, **client_kwargs) as client:
            r = client.get(URL, params=PARAMS)
        print(f"{name}: HTTP {r.status_code}, {len(r.text)} bytes, {time.time() - start:.1f}s")
    except Exception as exc:  # noqa: BLE001
        print(f"{name}: {type(exc).__name__} after {time.time() - start:.1f}s")


for label, agent in AGENTS.items():
    attempt(label, ua=agent)

# Extra checks: ignore system proxy settings, and force a fresh connection per request
attempt("no-proxy (curl-ua)", ua=AGENTS["curl-ua"], trust_env=False)
attempt("http2-off (curl-ua)", ua=AGENTS["curl-ua"], http2=False)