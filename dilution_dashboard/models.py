from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FilingSignal:
    ticker: str
    cik: str
    company_name: str
    form: str
    filing_date: str
    accession_number: str
    filing_url: str
    financing_type: str
    offering_amount_usd: float | None
    use_of_proceeds: str
    red_flags: list[str] = field(default_factory=list)
    green_flags: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass
class CompanySnapshot:
    ticker: str
    cik: str
    company_name: str
    exchange: str
    market_cap_usd: float | None
    diluted_shares_latest: float | None
    diluted_shares_prior: float | None
    revenue_latest: float | None
    revenue_prior: float | None
    free_cash_flow_latest: float | None
    debt_latest: float | None
    cash_latest: float | None
    filings: list[FilingSignal]


@dataclass
class ScoreResult:
    ticker: str
    company_name: str
    risk_score: int
    accretive_score: int
    predatory_score: int
    overhang_score: int
    verdict: str
    reasons: list[str]
    metrics: dict[str, float | None]
    filings: list[FilingSignal]

