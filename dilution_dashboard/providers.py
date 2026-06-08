from __future__ import annotations

from typing import Protocol

from .sec_client import FilingMeta, SecClient


class EdgarProvider(Protocol):
    """Boundary for SEC/EDGAR data providers.

    CapTable Lens keeps its dilution scoring independent from the filing backend.
    The default provider uses direct SEC public endpoints; optional future
    providers can wrap projects such as edgartools or sec-edgar-api without
    changing parser, scoring, storage, or dashboard code.
    """

    def ticker_map(self) -> dict:
        ...

    def recent_filings(self, cik: str, forms: set[str] | None = None, limit: int = 80) -> list[FilingMeta]:
        ...

    def filing_text(self, filing: FilingMeta) -> str:
        ...

    def companyfacts(self, cik: str) -> dict:
        ...


class DirectSecProvider:
    """Provider backed by SEC public JSON and archive endpoints."""

    def __init__(self, user_agent: str, cache_dir: str = ".cache/sec") -> None:
        self.client = SecClient(user_agent=user_agent, cache_dir=cache_dir)

    def ticker_map(self) -> dict:
        return self.client.ticker_map()

    def recent_filings(self, cik: str, forms: set[str] | None = None, limit: int = 80) -> list[FilingMeta]:
        return self.client.recent_filings(cik, forms, limit)

    def filing_text(self, filing: FilingMeta) -> str:
        return self.client.filing_text(filing)

    def companyfacts(self, cik: str) -> dict:
        return self.client.companyfacts(cik)

