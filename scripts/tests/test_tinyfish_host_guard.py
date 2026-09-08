"""TinyFish is optional. Host guard must fail closed before any cloud call."""

from __future__ import annotations

import unittest

from scripts.tinyfish_host_guard import (
    ALLOWED_FETCH_HOSTS,
    MAX_AGENT_STEPS,
    MONTHLY_CAP_USD,
    decide_tinyfish_use,
)


class TinyfishHostGuardTests(unittest.TestCase):
    def test_monthly_cap_is_twenty(self) -> None:
        self.assertEqual(MONTHLY_CAP_USD, 20)

    def test_play_listing_uses_existing_script_not_tinyfish(self) -> None:
        decision = decide_tinyfish_use(
            goal="verify Random Timer Play public listing",
            url="https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer",
            operation="fetch",
            api_key_present=True,
            auto_reload_configured=False,
            remaining_credit=10.0,
        )
        self.assertEqual(decision.action, "use_local_play_script")
        self.assertFalse(decision.allow_cloud_call)

    def test_add_credit_is_blocked(self) -> None:
        decision = decide_tinyfish_use(
            goal="add credit",
            url="https://agent.tinyfish.ai/home",
            operation="top_up",
            api_key_present=True,
            auto_reload_configured=False,
            remaining_credit=10.0,
        )
        self.assertEqual(decision.action, "block_add_credit")
        self.assertFalse(decision.allow_cloud_call)

    def test_auto_refill_is_blocked(self) -> None:
        decision = decide_tinyfish_use(
            goal="Broward auction fetch",
            url="https://broward.deedauction.net/",
            operation="fetch",
            api_key_present=True,
            auto_reload_configured=True,
            remaining_credit=10.0,
        )
        self.assertEqual(decision.action, "block_auto_refill")
        self.assertFalse(decision.allow_cloud_call)

    def test_zero_credit_skips(self) -> None:
        decision = decide_tinyfish_use(
            goal="Broward auction fetch",
            url="https://broward.deedauction.net/",
            operation="fetch",
            api_key_present=True,
            auto_reload_configured=False,
            remaining_credit=0.0,
        )
        self.assertEqual(decision.action, "skip_no_credit")
        self.assertFalse(decision.allow_cloud_call)

    def test_missing_key_skips(self) -> None:
        decision = decide_tinyfish_use(
            goal="Broward auction fetch",
            url="https://broward.deedauction.net/",
            operation="fetch",
            api_key_present=False,
            auto_reload_configured=False,
            remaining_credit=10.0,
        )
        self.assertEqual(decision.action, "skip_no_key")
        self.assertFalse(decision.allow_cloud_call)

    def test_agent_run_on_unknown_host_is_blocked(self) -> None:
        decision = decide_tinyfish_use(
            goal="checkout",
            url="https://checkout.stripe.com/c/pay/cs_test",
            operation="agent",
            api_key_present=True,
            auto_reload_configured=False,
            remaining_credit=10.0,
        )
        self.assertEqual(decision.action, "block_host")
        self.assertFalse(decision.allow_cloud_call)

    def test_fetch_allowlisted_county_host(self) -> None:
        decision = decide_tinyfish_use(
            goal="Broward tax deed auction list",
            url="https://broward.deedauction.net/",
            operation="fetch",
            api_key_present=True,
            auto_reload_configured=False,
            remaining_credit=10.0,
        )
        self.assertEqual(decision.action, "allow_fetch")
        self.assertTrue(decision.allow_cloud_call)
        self.assertIn("broward.deedauction.net", ALLOWED_FETCH_HOSTS)

    def test_agent_steps_are_clamped(self) -> None:
        decision = decide_tinyfish_use(
            goal="Broward tax deed structured extract",
            url="https://broward.deedauction.net/",
            operation="agent",
            api_key_present=True,
            auto_reload_configured=False,
            remaining_credit=10.0,
            max_steps=999,
        )
        self.assertEqual(decision.action, "allow_agent")
        self.assertTrue(decision.allow_cloud_call)
        self.assertEqual(decision.max_steps, MAX_AGENT_STEPS)


if __name__ == "__main__":
    unittest.main()
