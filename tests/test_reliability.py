import unittest
from dataclasses import asdict
from copy import deepcopy

from dilution_dashboard.agent import evaluate
from dilution_dashboard.facts import latest_and_prior, snapshot_metrics, TAGS
from dilution_dashboard.models import CompanySnapshot
from dilution_dashboard.scoring import score_company


def row(value, start, end, filed="2026-03-01", form="10-K"):
    return dict(val=value, start=start, end=end, filed=filed, form=form)


def facts(tags):
    return {"facts": {"us-gaap": {tag: {"units": {"USD": values}} for tag, values in tags.items()}}}


class ReliabilityTests(unittest.TestCase):
    def test_restatements_and_quarters_do_not_change_period_selection(self):
        f = facts({"Revenues": [row(100, "2024-01-01", "2024-12-31"),
            row(120, "2025-01-01", "2025-12-31"),
            row(110, "2024-01-01", "2024-12-31", "2026-04-01"),
            row(40, "2026-01-01", "2026-03-31", "2026-05-01", "10-Q")]})
        self.assertEqual(latest_and_prior(f, TAGS["revenue"], ("USD",)), (120, 110))

    def test_missing_year_is_not_a_growth_baseline(self):
        f = facts({"Revenues": [row(50, "2022-01-01", "2022-12-31"), row(120, "2025-01-01", "2025-12-31")]})
        self.assertEqual(latest_and_prior(f, TAGS["revenue"], ("USD",)), (120, None))

    def test_cash_flow_requires_identical_period(self):
        f = facts({"NetCashProvidedByUsedInOperatingActivities": [row(100, "2025-01-01", "2025-12-31")],
            "PaymentsToAcquirePropertyPlantAndEquipment": [row(20, "2024-01-01", "2024-12-31")]})
        self.assertIsNone(snapshot_metrics(f)["free_cash_flow_latest"])

    def test_debt_components_sum_without_alias_double_count(self):
        r = dict(val=10, end="2025-12-31", filed="2026-03-01", form="10-K")
        f = facts({"DebtCurrent": [r], "LongTermDebtCurrent": [r],
            "LongTermDebtNoncurrent": [dict(r, val=90)],
            "CashAndCashEquivalentsAtCarryingValue": [dict(r, val=40)]})
        self.assertEqual(snapshot_metrics(f)["debt_latest"], 100)

    def test_missing_input_is_reviewable_and_scoring_is_pure(self):
        s = CompanySnapshot("TEST", "0", "Test", "", *([None] * 8), [])
        before = deepcopy(s)
        a = score_company(s)
        self.assertEqual(s, before)
        self.assertEqual(a, score_company(s))
        out = evaluate(asdict(s))
        self.assertEqual(out["status"], "needs_review")
        self.assertTrue(out["requires_human_review"])

    def test_populated_filings_do_not_accumulate_flags(self):
        from dilution_dashboard.cli import demo_scores
        from dilution_dashboard.models import FilingSignal
        filing = FilingSignal("TEST", "0", "Test", "S-3", "2026-01-01", "test", "", "ATM", 600, "unclear")
        s = CompanySnapshot("TEST", "0", "Test", "", 1000, 130, 100, 110, 100, -10, 80, 20, [filing])
        before = deepcopy(s)
        self.assertEqual(score_company(s), score_company(s))
        self.assertEqual(s, before)

    def test_invalid_numeric_input_rejected(self):
        with self.assertRaises(ValueError):
            evaluate({"market_cap_usd": float("nan")})


if __name__ == "__main__":
    unittest.main()
