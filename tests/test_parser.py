from dilution_dashboard.parser import parse_filing


def test_parse_atm_amount_and_general_corporate_use():
    raw = """
    We have entered into an at-the-market sales agreement. We may offer and sell
    shares having an aggregate offering price of up to $600 million.
    Use of proceeds: We intend to use the net proceeds for working capital and
    general corporate purposes.
    """
    parsed = parse_filing(raw)
    assert parsed.financing_type == "ATM"
    assert parsed.offering_amount_usd == 600_000_000
    assert parsed.use_of_proceeds == "working capital"


def test_parse_growth_capex_use():
    raw = """
    This prospectus relates to a private placement. Use of proceeds from this
    offering will fund capital expenditures for construction of a new manufacturing
    facility and capacity expansion.
    """
    parsed = parse_filing(raw)
    assert parsed.financing_type == "Private Placement"
    assert parsed.use_of_proceeds == "growth capex"

