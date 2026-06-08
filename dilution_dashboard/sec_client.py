from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SEC_DATA = "https://data.sec.gov"
SEC_WWW = "https://www.sec.gov"


class SecClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class FilingMeta:
    cik: str
    accession_number: str
    form: str
    filing_date: str
    report_date: str
    primary_document: str

    @property
    def accession_nodashes(self) -> str:
        return self.accession_number.replace("-", "")

    @property
    def archive_url(self) -> str:
        cik_int = str(int(self.cik))
        return (
            f"{SEC_WWW}/Archives/edgar/data/{cik_int}/"
            f"{self.accession_nodashes}/{self.primary_document}"
        )


class SecClient:
    def __init__(
        self,
        user_agent: str,
        cache_dir: str | Path = ".cache/sec",
        min_interval_seconds: float = 0.12,
    ) -> None:
        if "@" not in user_agent:
            raise ValueError("SEC user agent should include a contact email, e.g. 'name email@example.com'.")
        self.user_agent = user_agent
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_interval_seconds = min_interval_seconds
        self._last_request_at = 0.0

    def ticker_map(self) -> dict[str, dict[str, Any]]:
        data = self._json(f"{SEC_WWW}/files/company_tickers_exchange.json", "company_tickers_exchange.json")
        fields = data["fields"]
        rows = data["data"]
        ticker_idx = fields.index("ticker")
        cik_idx = fields.index("cik")
        title_idx = fields.index("name")
        exchange_idx = fields.index("exchange")
        return {
            row[ticker_idx].upper(): {
                "ticker": row[ticker_idx].upper(),
                "cik": str(row[cik_idx]).zfill(10),
                "name": row[title_idx],
                "exchange": row[exchange_idx],
            }
            for row in rows
        }

    def submissions(self, cik: str) -> dict[str, Any]:
        cik = str(cik).zfill(10)
        return self._json(f"{SEC_DATA}/submissions/CIK{cik}.json", f"submissions/{cik}.json")

    def companyfacts(self, cik: str) -> dict[str, Any]:
        cik = str(cik).zfill(10)
        return self._json(f"{SEC_DATA}/api/xbrl/companyfacts/CIK{cik}.json", f"companyfacts/{cik}.json")

    def recent_filings(self, cik: str, forms: set[str] | None = None, limit: int = 80) -> list[FilingMeta]:
        subs = self.submissions(cik)
        recent = subs["filings"]["recent"]
        rows = []
        for i, form in enumerate(recent.get("form", [])):
            if forms and form not in forms:
                continue
            rows.append(
                FilingMeta(
                    cik=str(cik).zfill(10),
                    accession_number=recent["accessionNumber"][i],
                    form=form,
                    filing_date=recent["filingDate"][i],
                    report_date=recent.get("reportDate", [""])[i] if recent.get("reportDate") else "",
                    primary_document=recent["primaryDocument"][i],
                )
            )
            if len(rows) >= limit:
                break
        return rows

    def filing_text(self, filing: FilingMeta) -> str:
        cache_key = f"filings/{filing.cik}_{filing.accession_nodashes}_{filing.primary_document}"
        return self._text(filing.archive_url, cache_key)

    def _json(self, url: str, cache_key: str) -> dict[str, Any]:
        text = self._text(url, cache_key)
        return json.loads(text)

    def _text(self, url: str, cache_key: str) -> str:
        path = self.cache_dir / cache_key
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")

        path.parent.mkdir(parents=True, exist_ok=True)
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept-Encoding": "identity",
                "Host": urllib.parse.urlparse(url).netloc,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise SecClientError(f"SEC request failed {exc.code} for {url}") from exc
        except urllib.error.URLError as exc:
            raise SecClientError(f"SEC request failed for {url}: {exc.reason}") from exc
        finally:
            self._last_request_at = time.monotonic()

        text = raw.decode("utf-8", errors="ignore")
        path.write_text(text, encoding="utf-8")
        return text

