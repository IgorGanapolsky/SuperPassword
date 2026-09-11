"""TDD for local ops context (Era Context ideas, zero external cost)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_era_context import (  # noqa: E402
    MONTHLY_CAP_USD,
    apply_increase_rules,
    assistant_prompt_recipes,
    compare_categories,
    evaluate_platform,
    inventory_recurring,
    remaining_cap,
    summarize_ledger,
)


class PlatformGateTests(unittest.TestCase):
    def test_local_ops_context_allowed(self) -> None:
        self.assertTrue(evaluate_platform(platform="local_ops_context").ok)

    def test_external_context_vendor_denied(self) -> None:
        decision = evaluate_platform(platform="era_app_context_cloud")
        self.assertFalse(decision.ok)
        self.assertEqual(decision.action, "block_external_ops_context_vendor")


class CapTests(unittest.TestCase):
    def test_monthly_cap_is_twenty(self) -> None:
        self.assertEqual(MONTHLY_CAP_USD, 20.0)

    def test_remaining_cap(self) -> None:
        self.assertEqual(remaining_cap(mtd_usd=7.5), 12.5)

    def test_over_cap_clamps_at_zero(self) -> None:
        self.assertEqual(remaining_cap(mtd_usd=25.0), 0.0)


class MonthOverMonthTests(unittest.TestCase):
    def test_surfaces_categories_that_moved_up(self) -> None:
        report = compare_categories(
            previous={"ads": 2.0, "tooling": 5.0, "cloud": 1.0},
            current={"ads": 8.0, "tooling": 5.0, "cloud": 0.5},
        )
        names = {row.category: row for row in report.deltas}
        self.assertGreater(names["ads"].delta_usd, 0)
        self.assertLess(names["cloud"].delta_usd, 0)
        self.assertIn("ads", report.up_categories)
        self.assertTrue(report.total_delta_usd > 0)

    def test_explains_why_category_moved(self) -> None:
        report = compare_categories(
            previous={"ads": 2.0},
            current={"ads": 8.0},
        )
        ads = next(row for row in report.deltas if row.category == "ads")
        self.assertIn("up", ads.why.lower())


class RecurringInventoryTests(unittest.TestCase):
    def test_lists_recurring_and_monthly_total(self) -> None:
        report = inventory_recurring(
            items=[
                {"name": "apple_ads", "monthly_usd": 5.0, "active": True, "last_seen_days": 3},
                {"name": "forgotten_saas", "monthly_usd": 9.0, "active": True, "last_seen_days": 45},
                {"name": "cancelled", "monthly_usd": 4.0, "active": False, "last_seen_days": 2},
            ]
        )
        self.assertEqual(report.active_count, 2)
        self.assertEqual(report.monthly_total_usd, 14.0)
        self.assertIn("forgotten_saas", report.forgotten_names)

    def test_flags_when_recurring_exceeds_cap(self) -> None:
        report = inventory_recurring(
            items=[
                {"name": "a", "monthly_usd": 12.0, "active": True, "last_seen_days": 1},
                {"name": "b", "monthly_usd": 10.0, "active": True, "last_seen_days": 1},
            ]
        )
        self.assertFalse(report.within_cap)
        self.assertEqual(report.over_cap_usd, 2.0)


class IncreaseRuleTests(unittest.TestCase):
    def test_flags_silent_price_increase(self) -> None:
        alerts = apply_increase_rules(
            previous={"apple_ads": 5.0, "posthog": 0.0},
            current={"apple_ads": 7.5, "posthog": 0.0},
            watched=("apple_ads", "posthog"),
        )
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].name, "apple_ads")
        self.assertEqual(alerts[0].delta_usd, 2.5)

    def test_no_alert_when_flat(self) -> None:
        alerts = apply_increase_rules(
            previous={"apple_ads": 5.0},
            current={"apple_ads": 5.0},
            watched=("apple_ads",),
        )
        self.assertEqual(alerts, [])


class PromptRecipeTests(unittest.TestCase):
    def test_ships_three_era_style_prompts(self) -> None:
        recipes = assistant_prompt_recipes()
        self.assertGreaterEqual(len(recipes), 3)
        joined = " ".join(r.prompt for r in recipes).lower()
        self.assertIn("month", joined)
        self.assertTrue("subscription" in joined or "recurring" in joined)
        self.assertTrue("rule" in joined or "increased" in joined)


class LedgerSummaryTests(unittest.TestCase):
    def test_summarize_ledger_months(self) -> None:
        ledger = {
            "cap_usd": 20.0,
            "months": {
                "2026-08": {"ads": 2.0, "tooling": 3.0},
                "2026-09": {"ads": 4.0, "tooling": 3.0, "cloud": 1.0},
            },
            "recurring": [
                {"name": "apple_ads", "monthly_usd": 4.0, "active": True, "last_seen_days": 2},
            ],
        }
        summary = summarize_ledger(ledger, current_month="2026-09", previous_month="2026-08")
        self.assertEqual(summary.mtd_usd, 8.0)
        self.assertEqual(summary.remaining_usd, 12.0)
        self.assertTrue(summary.mom.within_cap or summary.remaining_usd >= 0)
        self.assertIn("ads", summary.mom.up_categories)


if __name__ == "__main__":
    unittest.main()
