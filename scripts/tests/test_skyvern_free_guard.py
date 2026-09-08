"""Skyvern is optional. Free-tier guard must fail closed before any cloud run."""

from __future__ import annotations

import unittest

from scripts.skyvern_free_guard import (
    ALLOWED_PUBLIC_HOSTS,
    HOBBY_PLAN_USD,
    MONTHLY_CAP_USD,
    decide_skyvern_use,
)


class SkyvernFreeGuardTests(unittest.TestCase):
    def test_hobby_plan_exceeds_monthly_cap(self) -> None:
        self.assertGreater(HOBBY_PLAN_USD, MONTHLY_CAP_USD)

    def test_play_listing_uses_existing_script_not_skyvern(self) -> None:
        decision = decide_skyvern_use(
            goal="verify Random Timer Play public listing",
            url="https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer",
            api_key_present=True,
            plan="free",
        )
        self.assertEqual(decision.action, "use_local_play_script")
        self.assertFalse(decision.allow_cloud_run)

    def test_missing_api_key_skips_cloud(self) -> None:
        decision = decide_skyvern_use(
            goal="lookup Delaware entity",
            url="https://icis.corp.delaware.gov/Ecorp/EntitySearch/NameSearch.aspx",
            api_key_present=False,
            plan="free",
        )
        self.assertEqual(decision.action, "skip_no_key")
        self.assertFalse(decision.allow_cloud_run)

    def test_paid_plan_is_blocked(self) -> None:
        decision = decide_skyvern_use(
            goal="lookup Delaware entity",
            url="https://icis.corp.delaware.gov/Ecorp/EntitySearch/NameSearch.aspx",
            api_key_present=True,
            plan="hobby",
        )
        self.assertEqual(decision.action, "block_paid_plan")
        self.assertFalse(decision.allow_cloud_run)

    def test_unknown_host_is_blocked(self) -> None:
        decision = decide_skyvern_use(
            goal="buy something",
            url="https://checkout.stripe.com/c/pay/cs_test",
            api_key_present=True,
            plan="free",
        )
        self.assertEqual(decision.action, "block_host")
        self.assertFalse(decision.allow_cloud_run)

    def test_legacy_government_host_allowed_on_free_with_key(self) -> None:
        decision = decide_skyvern_use(
            goal="Sunbiz managing member lookup",
            url="https://search.sunbiz.org/Inquiry/CorporationSearch/ByName",
            api_key_present=True,
            plan="free",
            max_steps=8,
        )
        self.assertEqual(decision.action, "allow_cloud_run")
        self.assertTrue(decision.allow_cloud_run)
        self.assertLessEqual(decision.max_steps, 8)
        self.assertIn("search.sunbiz.org", ALLOWED_PUBLIC_HOSTS)

    def test_max_steps_is_clamped(self) -> None:
        decision = decide_skyvern_use(
            goal="Sunbiz lookup",
            url="https://search.sunbiz.org/Inquiry/CorporationSearch/ByName",
            api_key_present=True,
            plan="free",
            max_steps=999,
        )
        self.assertEqual(decision.max_steps, 8)


if __name__ == "__main__":
    unittest.main()
