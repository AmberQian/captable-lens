"""Offline, read-only JSON interface for an Agent or future API adapter."""
from __future__ import annotations

import json
import math
import sys
from dataclasses import asdict

from .models import CompanySnapshot, FilingSignal
from .scoring import score_company


def evaluate(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("snapshot must be a JSON object")
    data = dict(payload)
    filings = data.pop("filings", [])
    if not isinstance(filings, list):
        raise ValueError("filings must be an array")
    numeric = {"market_cap_usd", "diluted_shares_latest", "diluted_shares_prior",
               "revenue_latest", "revenue_prior", "free_cash_flow_latest",
               "debt_latest", "cash_latest"}
    for key in numeric:
        value = data.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)):
            raise ValueError(f"{key} must be a finite number or null")
        if value is not None and key != "free_cash_flow_latest" and value < 0:
            raise ValueError(f"{key} cannot be negative")
    for filing in filings:
        if not isinstance(filing, dict):
            raise ValueError("each filing must be an object")
        value = filing.get("offering_amount_usd")
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
            raise ValueError("offering_amount_usd must be finite and nonnegative")
    snapshot = CompanySnapshot(**data, filings=[FilingSignal(**f) for f in filings])
    missing = sorted(k for k in numeric if data.get(k) is None)
    warnings = [f"missing metric: {key}" for key in missing]
    if not filings:
        warnings.append("no filing evidence supplied")
    return {"schema_version": "1.0", "status": "needs_review" if warnings else "screened",
            "requires_human_review": True, "warnings": warnings,
            "result": asdict(score_company(snapshot))}


def main() -> int:
    try:
        output = evaluate(json.load(sys.stdin))
    except (ValueError, TypeError) as exc:
        print(json.dumps({"schema_version": "1.0", "status": "invalid_input", "error": str(exc)}))
        return 2
    print(json.dumps(output, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
