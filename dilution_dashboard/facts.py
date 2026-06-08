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


def latest_fact(facts: dict[str, Any], tag_names: list[str], units: tuple[str, ...] = ("USD", "shares")) -> float | None:
    gaap = facts.get("facts", {}).get("us-gaap", {})
    candidates: list[tuple[str, float]] = []
    for tag in tag_names:
        fact = gaap.get(tag)
        if not fact:
            continue
        for unit in units:
            for row in fact.get("units", {}).get(unit, []):
                if "val" not in row or not row.get("filed"):
                    continue
                frame = row.get("frame", "")
                form = row.get("form", "")
                if form not in {"10-K", "10-Q", "20-F", "40-F"}:
                    continue
                weight = row["filed"]
                if frame:
                    weight += f"-{frame}"
                candidates.append((weight, float(row["val"])))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def latest_and_prior(facts: dict[str, Any], tag_names: list[str], units: tuple[str, ...] = ("USD", "shares")) -> tuple[float | None, float | None]:
    gaap = facts.get("facts", {}).get("us-gaap", {})
    candidates: list[tuple[str, float]] = []
    for tag in tag_names:
        fact = gaap.get(tag)
        if not fact:
            continue
        for unit in units:
            for row in fact.get("units", {}).get(unit, []):
                if "val" not in row or not row.get("filed"):
                    continue
                if row.get("form") not in {"10-K", "10-Q", "20-F", "40-F"}:
                    continue
                candidates.append((row["filed"], float(row["val"])))
    dedup = []
    seen = set()
    for filed, val in sorted(candidates, key=lambda item: item[0]):
        key = (filed, val)
        if key not in seen:
            dedup.append((filed, val))
            seen.add(key)
    if not dedup:
        return None, None
    latest = dedup[-1][1]
    prior = dedup[-5][1] if len(dedup) >= 5 else (dedup[0][1] if len(dedup) > 1 else None)
    return latest, prior


def snapshot_metrics(facts: dict[str, Any]) -> dict[str, float | None]:
    shares_latest, shares_prior = latest_and_prior(facts, TAGS["diluted_shares"], ("shares",))
    revenue_latest, revenue_prior = latest_and_prior(facts, TAGS["revenue"], ("USD",))
    ocf = latest_fact(facts, TAGS["operating_cash_flow"], ("USD",))
    capex = latest_fact(facts, TAGS["capex"], ("USD",))
    debt_current = latest_fact(facts, TAGS["debt"], ("USD",))
    cash = latest_fact(facts, TAGS["cash"], ("USD",))
    fcf = None
    if ocf is not None and capex is not None:
        fcf = ocf - abs(capex)
    return {
        "diluted_shares_latest": shares_latest,
        "diluted_shares_prior": shares_prior,
        "revenue_latest": revenue_latest,
        "revenue_prior": revenue_prior,
        "free_cash_flow_latest": fcf,
        "debt_latest": debt_current,
        "cash_latest": cash,
    }

