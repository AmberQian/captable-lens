from __future__ import annotations

from typing import Any


TAGS = {
    "diluted_shares": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
        "WeightedAverageDilutedSharesOutstanding",
        "EntityCommonStockSharesOutstanding",
    ],
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
    ],
    "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
    "debt": [
        "DebtCurrent",
        "LongTermDebtCurrent",
        "LongTermDebtAndFinanceLeaseObligationsCurrent",
        "LongTermDebtNoncurrent",
        "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
    ],
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
}


ANNUAL_FORMS = {"10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A"}


def _rows(facts, tags, units, duration=False):
    """Select one semantic tag/unit, annual periods, and latest restatement."""
    from datetime import date
    from math import isfinite
    gaap = facts.get("facts", {}).get("us-gaap", {})
    for tag in tags:
        for unit in units:
            periods = {}
            for row in gaap.get(tag, {}).get("units", {}).get(unit, []):
                if row.get("form") not in ANNUAL_FORMS or not row.get("end") or not row.get("filed"):
                    continue
                try:
                    value = float(row["val"])
                    end = date.fromisoformat(row["end"])
                    date.fromisoformat(row["filed"])
                    start = row.get("start")
                    if duration:
                        if not start or not 330 <= (end - date.fromisoformat(start)).days <= 380:
                            continue
                    elif start:
                        continue
                    if not isfinite(value):
                        continue
                except (ValueError, TypeError, KeyError):
                    continue
                key = (start if duration else None, row["end"])
                if key not in periods or row["filed"] > periods[key]["filed"]:
                    periods[key] = dict(row, val=value)
            if periods:
                return sorted(periods.values(), key=lambda r: (r["end"], r.get("start", "")))
    return []


def latest_fact(facts, tag_names, units=("USD", "shares")):
    rows = _rows(facts, tag_names, units, duration=tag_names not in (TAGS["cash"], TAGS["debt"]))
    return rows[-1]["val"] if rows else None


def latest_and_prior(facts, tag_names, units=("USD", "shares")):
    from datetime import date
    rows = _rows(facts, tag_names, units, duration=True)
    if not rows:
        return None, None
    latest = rows[-1]
    prior = [r for r in rows[:-1] if 330 <= (date.fromisoformat(latest["end"]) - date.fromisoformat(r["end"])).days <= 400]
    return latest["val"], prior[-1]["val"] if prior else None


def snapshot_metrics(facts: dict[str, Any]) -> dict[str, float | None]:
    shares_latest, shares_prior = latest_and_prior(facts, TAGS["diluted_shares"], ("shares",))
    revenue_latest, revenue_prior = latest_and_prior(facts, TAGS["revenue"], ("USD",))
    ocf_rows = _rows(facts, TAGS["operating_cash_flow"], ("USD",), duration=True)
    capex_rows = _rows(facts, TAGS["capex"], ("USD",), duration=True)
    fcf = None
    if ocf_rows:
        ocf = ocf_rows[-1]
        matching = [r for r in capex_rows if (r["start"], r["end"]) == (ocf["start"], ocf["end"])]
        if matching:
            fcf = ocf["val"] - abs(matching[-1]["val"])
    # Sum current + noncurrent components at the same balance-sheet date.
    current = _rows(facts, TAGS["debt"][:3], ("USD",))
    noncurrent = _rows(facts, TAGS["debt"][3:], ("USD",))
    debt = None
    if current and noncurrent and current[-1]["end"] == noncurrent[-1]["end"]:
        debt = current[-1]["val"] + noncurrent[-1]["val"]
    cash_rows = _rows(facts, TAGS["cash"], ("USD",))
    cash = cash_rows[-1]["val"] if cash_rows else None
    if debt is not None and cash_rows and cash_rows[-1]["end"] != current[-1]["end"]:
        debt = None
    return {
        "diluted_shares_latest": shares_latest,
        "diluted_shares_prior": shares_prior,
        "revenue_latest": revenue_latest,
        "revenue_prior": revenue_prior,
        "free_cash_flow_latest": fcf,
        "debt_latest": debt,
        "cash_latest": cash,
    }
