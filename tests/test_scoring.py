from dilution_dashboard.models import CompanySnapshot, FilingSignal
from dilution_dashboard.scoring import score_company


def test_large_atm_overhang_is_high_risk():
    filing = FilingSignal(
        ticker="TEST",
        cik="0000000000",
        company_name="Test Co",
        form="S-3",
        filing_date="2026-01-01",
        accession_number="0000000000-26-000001",
        filing_url="https://www.sec.gov/",
        financing_type="ATM",
        offering_amount_usd=600_000_000,
        use_of_proceeds="general corporate purposes",
    )
    snapshot = CompanySnapshot(
        ticker="TEST",
        cik="0000000000",
        company_name="Test Co",
        exchange="Nasdaq",
        market_cap_usd=1_000_000_000,
        diluted_shares_latest=130_000_000,
        diluted_shares_prior=100_000_000,
        revenue_latest=110_000_000,
        revenue_prior=100_000_000,
        free_cash_flow_latest=-10_000_000,
        debt_latest=80_000_000,
        cash_latest=20_000_000,
        filings=[filing],
    )
    score = score_company(snapshot)
    assert score.risk_score >= 70
    assert score.predatory_score > score.accretive_score
    assert score.overhang_score > 0


def test_growth_capex_can_offset_predatory_score():
    filing = FilingSignal(
        ticker="GOOD",
        cik="0000000000",
        company_name="Good Co",
        form="8-K",
        filing_date="2026-01-01",
        accession_number="0000000000-26-000001",
        filing_url="https://www.sec.gov/",
        financing_type="Private Placement",
        offering_amount_usd=100_000_000,
        use_of_proceeds="growth capex",
    )
    snapshot = CompanySnapshot(
        ticker="GOOD",
        cik="0000000000",
        company_name="Good Co",
        exchange="NYSE",
        market_cap_usd=2_000_000_000,
        diluted_shares_latest=105_000_000,
        diluted_shares_prior=100_000_000,
        revenue_latest=140_000_000,
        revenue_prior=100_000_000,
        free_cash_flow_latest=5_000_000,
        debt_latest=20_000_000,
        cash_latest=100_000_000,
        filings=[filing],
    )
    score = score_company(snapshot)
    assert score.accretive_score > score.predatory_score
    assert score.verdict == "Potentially accretive"

