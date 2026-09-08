"""InfoQ steal: agent delivery control plane. Fail closed. No paid products."""

from __future__ import annotations

import unittest

from scripts.infoq_agent_control_plane import (
    evaluate_context_store,
    evaluate_gateway_fitness,
    evaluate_identity,
    evaluate_review_lane,
    evaluate_token_spend,
    gist_context,
)


class GatewayFitnessTests(unittest.TestCase):
    def test_independent_fallbacks_pass(self) -> None:
        d = evaluate_gateway_fitness(
            primary_model="hermes-main",
            fallback_models=["nous-deepseek", "glm-5.3"],
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_route")

    def test_empty_fallbacks_fail(self) -> None:
        d = evaluate_gateway_fitness(
            primary_model="hermes-main",
            fallback_models=[],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_no_fallback")

    def test_same_model_fallback_is_spof(self) -> None:
        d = evaluate_gateway_fitness(
            primary_model="hermes-main",
            fallback_models=["hermes-main"],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_spof")

    def test_weak_3b_fallback_fails(self) -> None:
        d = evaluate_gateway_fitness(
            primary_model="hermes-main",
            fallback_models=["qwen2.5:3b-hermes-64k"],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_weak_fallback")


class ContextEngineeringTests(unittest.TestCase):
    def test_in_out_and_two_acs_pass(self) -> None:
        d = evaluate_context_store(
            sections={"in_scope": "pin Desktop", "out_scope": "Ori login"},
            acceptance_criteria=["tests pass", "CLI fail-closed"],
        )
        self.assertTrue(d.ok)

    def test_missing_out_scope_fails(self) -> None:
        d = evaluate_context_store(
            sections={"in_scope": "pin Desktop"},
            acceptance_criteria=["tests pass", "CLI fail-closed"],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_context")

    def test_one_ac_fails(self) -> None:
        d = evaluate_context_store(
            sections={"in_scope": "pin Desktop", "out_scope": "Ori login"},
            acceptance_criteria=["tests pass"],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_context")

    def test_gist_drops_fluff(self) -> None:
        gisted = gist_context(
            {
                "in_scope": "pin Desktop",
                "out_scope": "Ori login",
                "newsletter_dump": "A" * 4000,
                "acceptance_criteria": ["tests pass", "CLI fail-closed"],
            }
        )
        self.assertNotIn("newsletter_dump", gisted)
        self.assertIn("in_scope", gisted)
        self.assertLess(len(str(gisted)), 4000)


class TokenSpendTests(unittest.TestCase):
    def test_local_pytest_allowed(self) -> None:
        d = evaluate_token_spend(service="local_pytest")
        self.assertTrue(d.ok)

    def test_billed_copilot_review_blocked(self) -> None:
        d = evaluate_token_spend(service="copilot_code_review")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_billed_review")

    def test_ori_blocked(self) -> None:
        d = evaluate_token_spend(service="ori")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")


class ReviewLaneTests(unittest.TestCase):
    def test_scripts_only_allows_ai_approve(self) -> None:
        d = evaluate_review_lane(
            changed_paths=[
                "scripts/infoq_agent_control_plane.py",
                "scripts/tests/test_infoq_agent_control_plane.py",
            ]
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_ai_approve")

    def test_android_requires_device_e2e(self) -> None:
        d = evaluate_review_lane(
            changed_paths=["native-android/app/src/main/java/Foo.kt"]
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "require_device_e2e")


class WorkloadIdentityTests(unittest.TestCase):
    def test_github_oidc_allowed(self) -> None:
        d = evaluate_identity(credential_kind="github_oidc")
        self.assertTrue(d.ok)

    def test_long_lived_sa_json_blocked(self) -> None:
        d = evaluate_identity(credential_kind="gcp_sa_json")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_long_lived_key")


if __name__ == "__main__":
    unittest.main()
