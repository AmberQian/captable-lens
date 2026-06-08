from __future__ import annotations

from .models import CompanySnapshot, ScoreResult


def score_company(snapshot: CompanySnapshot) -> ScoreResult:
    predatory = 0
    accretive = 0
    overhang = 0
    reasons: list[str] = []

    max_offering = max((f.offering_amount_usd or 0 for f in snapshot.filings), default=0)
    offering_to_market_cap = None
    if snapshot.market_cap_usd and max_offering:
        offering_to_market_cap = max_offering / snapshot.market_cap_usd
        if offering_to_market_cap > 0.30:
            predatory += 30
            overhang += 35
            reasons.append("registered/offering amount is above 30% of market cap")
        elif offering_to_market_cap > 0.15:
            predatory += 15
            overhang += 20
            reasons.append("registered/offering amount is above 15% of market cap")

    share_growth = _growth(snapshot.diluted_shares_latest, snapshot.diluted_shares_prior)
    revenue_growth = _growth(snapshot.revenue_latest, snapshot.revenue_prior)
    if share_growth is not None:
        if share_growth > 0.20:
            predatory += 25
            reasons.append("diluted share count rose more than 20% versus prior baseline")
        elif share_growth > 0.10:
            predatory += 10
            reasons.append("diluted share count rose more than 10% versus prior baseline")

    if share_growth is not None and revenue_growth is not None:
        if share_growth > 0.20 and revenue_growth < share_growth:
            predatory += 15
            reasons.append("share count growth is outpacing revenue growth")
        if revenue_growth > share_growth and revenue_growth > 0.15:
            accretive += 15
            reasons.append("revenue growth is outpacing share count growth")

    for filing in snapshot.filings:
        if filing.financing_type == "ATM":
            predatory += 15
            overhang += 20
            filing.red_flags.append("ATM program can create ongoing supply overhang")
        if filing.financing_type == "Convertible Debt":
            predatory += 12
            filing.red_flags.append("convertible debt can add contingent dilution")
        if filing.use_of_proceeds in {"general corporate purposes", "working capital", "unclear"}:
            predatory += 10
            filing.red_flags.append("use of proceeds is broad or unclear")
        if filing.use_of_proceeds == "debt repayment":
            predatory += 8
            filing.red_flags.append("proceeds are going to debt repayment instead of direct growth")
        if filing.use_of_proceeds in {"growth capex", "M&A"}:
            accretive += 18
            filing.green_flags.append(f"proceeds appear tied to {filing.use_of_proceeds}")
        if filing.financing_type == "Private Placement":
            accretive += 8
            filing.green_flags.append("private placement can be constructive if investor quality and terms are strong")

    if snapshot.free_cash_flow_latest is not None and snapshot.free_cash_flow_latest < 0:
        predatory += 10
        reasons.append("latest free cash flow estimate is negative")
    if snapshot.cash_latest is not None and snapshot.debt_latest is not None and snapshot.debt_latest > snapshot.cash_latest:
        predatory += 8
        reasons.append("latest debt exceeds latest cash balance")

    predatory = min(predatory, 100)
    accretive = min(accretive, 100)
    overhang = min(overhang, 100)
    risk = min(max(predatory + overhang // 3 - accretive // 3, 0), 100)

    if risk >= 70:
        verdict = "High predatory dilution risk"
    elif risk >= 45:
        verdict = "Needs manual review"
    elif accretive > predatory:
        verdict = "Potentially accretive"
    else:
        verdict = "Low/medium dilution signal"

    return ScoreResult(
        ticker=snapshot.ticker,
        company_name=snapshot.company_name,
        risk_score=risk,
        accretive_score=accretive,
        predatory_score=predatory,
        overhang_score=overhang,
        verdict=verdict,
        reasons=reasons[:8],
        metrics={
            "offering_to_market_cap": offering_to_market_cap,
            "share_growth": share_growth,
            "revenue_growth": revenue_growth,
            "market_cap_usd": snapshot.market_cap_usd,
            "free_cash_flow_latest": snapshot.free_cash_flow_latest,
            "cash_latest": snapshot.cash_latest,
            "debt_latest": snapshot.debt_latest,
        },
        filings=snapshot.filings,
    )


def _growth(latest: float | None, prior: float | None) -> float | None:
    if latest is None or prior in (None, 0):
        return None
    return (latest - prior) / abs(prior)

