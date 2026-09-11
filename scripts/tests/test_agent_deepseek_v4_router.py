"""TDD for DeepSeek V4 peak/off-peak router + Pro continuation (budget-capped)."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_deepseek_v4_router import (  # noqa: E402
    DEEPSEEK_MONTHLY_CAP_USD,
    estimate_cost_usd,
    is_peak_utc,
    next_off_peak_utc,
    resolve_model_after_pro_continuation,
    route_request,
)


class PeakWindowTests(unittest.TestCase):
    def test_peak_weekday_windows(self) -> None:
        # Monday 02:00 UTC peak
        self.assertTrue(is_peak_utc(datetime(2026, 9, 14, 2, 0, tzinfo=timezone.utc)))
        # Monday 07:00 UTC peak
        self.assertTrue(is_peak_utc(datetime(2026, 9, 14, 7, 0, tzinfo=timezone.utc)))
        # Monday 12:00 UTC off-peak
        self.assertFalse(is_peak_utc(datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)))
        # Saturday during weekday peak hours is off-peak (Mon-Fri only)
        self.assertFalse(is_peak_utc(datetime(2026, 9, 12, 2, 0, tzinfo=timezone.utc)))

    def test_next_off_peak_after_morning_peak(self) -> None:
        now = datetime(2026, 9, 14, 7, 30, tzinfo=timezone.utc)
        nxt = next_off_peak_utc(now)
        self.assertEqual(nxt, datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc))


class ProContinuationTests(unittest.TestCase):
    def test_before_cutoff_pro_stays_pro(self) -> None:
        r = resolve_model_after_pro_continuation(
            requested="deepseek-v4-pro",
            now_utc=datetime(2026, 9, 14, 3, 59, tzinfo=timezone.utc),
        )
        self.assertEqual(r.api_model, "deepseek-v4-pro")
        self.assertEqual(r.bill_as, "pro")
        self.assertFalse(r.routed_to_flash)

    def test_after_cutoff_pro_alias_bills_as_flash(self) -> None:
        # 12:00 Beijing = 04:00 UTC on Sep 14, 2026
        r = resolve_model_after_pro_continuation(
            requested="deepseek-v4-pro",
            now_utc=datetime(2026, 9, 14, 4, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(r.api_model, "deepseek-flash")
        self.assertEqual(r.bill_as, "flash")
        self.assertTrue(r.routed_to_flash)
        self.assertIn("continuation", r.reason.lower())


class RoutingTests(unittest.TestCase):
    def test_interactive_prefers_flash_even_if_pro_requested(self) -> None:
        d = route_request(
            task="interactive refactor",
            requested_model="deepseek-v4-pro",
            interactive=True,
            now_utc=datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc),
            month_spend_usd=0.0,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_now")
        self.assertEqual(d.api_model, "deepseek-flash")
        self.assertEqual(d.bill_as, "flash")

    def test_background_defers_during_peak(self) -> None:
        d = route_request(
            task="nightly eval suite",
            requested_model="deepseek-flash",
            interactive=False,
            now_utc=datetime(2026, 9, 14, 2, 15, tzinfo=timezone.utc),
            month_spend_usd=1.0,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "defer_off_peak")
        self.assertEqual(d.resume_at_utc, datetime(2026, 9, 14, 4, 0, tzinfo=timezone.utc))

    def test_budget_exhausted_fails_closed_to_local(self) -> None:
        d = route_request(
            task="batch embed",
            requested_model="deepseek-flash",
            interactive=False,
            now_utc=datetime(2026, 9, 11, 18, 0, tzinfo=timezone.utc),
            month_spend_usd=DEEPSEEK_MONTHLY_CAP_USD,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "failover_local")
        self.assertEqual(d.api_model, "local/hermes-cheap")


class CostEstimateTests(unittest.TestCase):
    def test_off_peak_flash_cheaper_than_peak(self) -> None:
        off = estimate_cost_usd(
            bill_as="flash",
            peak=False,
            input_tokens=1_000_000,
            output_tokens=0,
            cache_hit=False,
        )
        peak = estimate_cost_usd(
            bill_as="flash",
            peak=True,
            input_tokens=1_000_000,
            output_tokens=0,
            cache_hit=False,
        )
        self.assertAlmostEqual(off, 0.15, places=4)
        self.assertAlmostEqual(peak, 0.30, places=4)
        self.assertLess(off, peak)

    def test_pro_rates_higher_than_flash_before_cutoff(self) -> None:
        flash = estimate_cost_usd(bill_as="flash", peak=False, input_tokens=1_000_000, output_tokens=0, cache_hit=False)
        pro = estimate_cost_usd(bill_as="pro", peak=False, input_tokens=1_000_000, output_tokens=0, cache_hit=False)
        self.assertGreater(pro, flash)


if __name__ == "__main__":
    unittest.main()
