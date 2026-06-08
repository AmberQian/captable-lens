from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


class MarketDataError(RuntimeError):
    pass


@dataclass(frozen=True)
class MarketCapResult:
    ticker: str
    market_cap_usd: float | None
    source: str


def load_manual_market_caps(path: str | None) -> dict[str, float]:
    if not path:
        return {}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {ticker.upper(): float(value) for ticker, value in raw.items()}


def resolve_market_caps(
    tickers: list[str],
    manual_path: str | None = None,
    provider: str = "yahoo",
    cache_dir: str | Path = ".cache/market",
    max_age_seconds: int = 12 * 60 * 60,
) -> dict[str, float]:
    manual = load_manual_market_caps(manual_path)
    normalized = sorted({ticker.upper() for ticker in tickers})
    if provider == "none":
        return manual
    if provider != "yahoo":
        raise ValueError(f"Unsupported market data provider: {provider}")

    missing = [ticker for ticker in normalized if ticker not in manual]
    if not missing:
        return manual

    cache = MarketCapCache(cache_dir)
    cached = cache.read_fresh(max_age_seconds)
    need_fetch = [ticker for ticker in missing if ticker not in cached]
    fetched: dict[str, float] = {}
    if need_fetch:
        fetched = fetch_yahoo_market_caps(need_fetch)
        cache.merge(fetched)

    resolved = {}
    resolved.update(cached)
    resolved.update(fetched)
    resolved.update(manual)
    return {ticker: cap for ticker, cap in resolved.items() if ticker in normalized and cap is not None}


def fetch_yahoo_market_caps(tickers: list[str], batch_size: int = 50) -> dict[str, float]:
    results: dict[str, float] = {}
    normalized = [ticker.upper() for ticker in tickers]
    for i in range(0, len(normalized), batch_size):
        batch = normalized[i : i + batch_size]
        query = urllib.parse.urlencode({"symbols": ",".join(batch)})
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?{query}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "CapTable Lens market-data fetcher",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise MarketDataError(f"Market cap request failed for {', '.join(batch)}: {exc}") from exc

        quotes = payload.get("quoteResponse", {}).get("result", [])
        for quote in quotes:
            ticker = str(quote.get("symbol", "")).upper()
            cap = quote.get("marketCap")
            if ticker and cap is not None:
                results[ticker] = float(cap)
    return results


class MarketCapCache:
    def __init__(self, cache_dir: str | Path) -> None:
        self.path = Path(cache_dir) / "market_caps.json"

    def read_fresh(self, max_age_seconds: int) -> dict[str, float]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        fetched_at = float(raw.get("fetched_at", 0))
        if time.time() - fetched_at > max_age_seconds:
            return {}
        caps = raw.get("market_caps", {})
        return {ticker.upper(): float(value) for ticker, value in caps.items() if value is not None}

    def merge(self, market_caps: dict[str, float]) -> None:
        existing = {}
        if self.path.exists():
            try:
                existing = json.loads(self.path.read_text(encoding="utf-8")).get("market_caps", {})
            except json.JSONDecodeError:
                existing = {}
        existing.update({ticker.upper(): float(value) for ticker, value in market_caps.items()})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"fetched_at": time.time(), "market_caps": existing}, indent=2, sort_keys=True),
            encoding="utf-8",
        )

