"""Decisions Universal Orchestration steal: control layer for multi-agent ops."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_universal_orchestration import (
    evaluate_agent_cost_telemetry,
    evaluate_audit_trail,
    evaluate_capability_pillars,
    evaluate_claim,
    evaluate_control_layer,
    evaluate_five_outcomes,
    evaluate_guardrails,
    evaluate_handoff,
    evaluate_hard_permissioning,
    evaluate_human_in_loop,
    evaluate_platform,
    evaluate_process_state,
    evaluate_readiness,
    evaluate_rules_first,
    evaluate_shadow_ai,
    evaluate_shadow_test,
    evaluate_visibility,
    pick_flow,
    rank_work,
    require_universal_orchestration_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_universal_orchestration.json"


class PlatformTests(unittest.TestCase):
    def test_local_passes(self) -> None:
        self.assertTrue(evaluate_platform(platform="ops_control_layer").ok)

    def test_vendor_spend_fails(self) -> None:
        d = evaluate_platform(platform="decisions_saas_paid")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_vendor_spend")


class ControlLayerTests(unittest.TestCase):
    def test_governed_passes(self) -> None:
        d = evaluate_control_layer(has_control_layer=True, agent_sprawl=False)
        self.assertTrue(d.ok)

    def test_sprawl_fails(self) -> None:
        d = evaluate_control_layer(has_control_layer=False, agent_sprawl=True)
        self.assertFalse(d.ok)


class RulesFirstTests(unittest.TestCase):
    def test_policy_passes(self) -> None:
        d = evaluate_rules_first(deterministic_policy=True, prompt_only=False)
        self.assertTrue(d.ok)

    def test_prompt_only_fails(self) -> None:
        d = evaluate_rules_first(deterministic_policy=False, prompt_only=True)
        self.assertFalse(d.ok)


class GuardrailTests(unittest.TestCase):
    def test_guardrails_pass(self) -> None:
        d = evaluate_guardrails(
            authorized_actions_defined=True, unauthorized_blocked=True
        )
        self.assertTrue(d.ok)

    def test_unguarded_fails(self) -> None:
        d = evaluate_guardrails(
            authorized_actions_defined=False, unauthorized_blocked=False
        )
        self.assertFalse(d.ok)


class HitlTests(unittest.TestCase):
    def test_reversible_passes(self) -> None:
        d = evaluate_human_in_loop(
            irreversible_action=False, approval_point=False, escalated=False
        )
        self.assertTrue(d.ok)

    def test_irreversible_without_gate_fails(self) -> None:
        d = evaluate_human_in_loop(
            irreversible_action=True, approval_point=False, escalated=False
        )
        self.assertFalse(d.ok)

    def test_irreversible_with_approval_passes(self) -> None:
        d = evaluate_human_in_loop(
            irreversible_action=True, approval_point=True, escalated=False
        )
        self.assertTrue(d.ok)


class AuditTests(unittest.TestCase):
    def test_complete_audit_passes(self) -> None:
        d = evaluate_audit_trail(
            rules_logged=True,
            inputs_logged=True,
            outputs_logged=True,
            handoffs_logged=True,
        )
        self.assertTrue(d.ok)

    def test_gap_fails(self) -> None:
        d = evaluate_audit_trail(
            rules_logged=True,
            inputs_logged=True,
            outputs_logged=False,
            handoffs_logged=True,
        )
        self.assertFalse(d.ok)


class HandoffTests(unittest.TestCase):
    def test_routed_passes(self) -> None:
        d = evaluate_handoff(next_step_routed=True, result_persisted=True)
        self.assertTrue(d.ok)

    def test_black_hole_fails(self) -> None:
        d = evaluate_handoff(next_step_routed=False, result_persisted=False)
        self.assertFalse(d.ok)


class ReadinessTests(unittest.TestCase):
    def test_focused_start_passes(self) -> None:
        d = evaluate_readiness(
            complexity_signals=True,
            readiness_assessed=True,
            focused_first_use_case=True,
        )
        self.assertTrue(d.ok)

    def test_boil_ocean_fails(self) -> None:
        d = evaluate_readiness(
            complexity_signals=True,
            readiness_assessed=True,
            focused_first_use_case=False,
        )
        self.assertFalse(d.ok)


class ShadowTests(unittest.TestCase):
    def test_live_without_shadow_fails(self) -> None:
        d = evaluate_shadow_test(shadow_tested=False, going_live=True)
        self.assertFalse(d.ok)

    def test_shadow_then_live_passes(self) -> None:
        d = evaluate_shadow_test(shadow_tested=True, going_live=True)
        self.assertTrue(d.ok)


class VisibilityTests(unittest.TestCase):
    def test_visible_passes(self) -> None:
        d = evaluate_visibility(
            real_time_observability=True, exceptions_surfaced=True
        )
        self.assertTrue(d.ok)

    def test_blind_fails(self) -> None:
        d = evaluate_visibility(
            real_time_observability=False, exceptions_surfaced=False
        )
        self.assertFalse(d.ok)


class CapabilityPillarTests(unittest.TestCase):
    def test_three_pillars_pass(self) -> None:
        d = evaluate_capability_pillars(
            runtime_coordination=True,
            state_context_intelligence=True,
            control_policy_observability=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_three_pillars")

    def test_missing_state_pillar_fails(self) -> None:
        d = evaluate_capability_pillars(
            runtime_coordination=True,
            state_context_intelligence=False,
            control_policy_observability=True,
        )
        self.assertFalse(d.ok)
        self.assertIn("state_context", d.reason)


class HardPermissioningTests(unittest.TestCase):
    def test_instructions_only_blocked_for_production(self) -> None:
        d = evaluate_hard_permissioning(
            reaches_production=True,
            hard_permissioning=False,
            approval_gate=False,
            intervention_control=False,
            prompt_instructions_only=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_instructions_only_control")

    def test_hard_gates_allow_production(self) -> None:
        d = evaluate_hard_permissioning(
            reaches_production=True,
            hard_permissioning=True,
            approval_gate=True,
            intervention_control=True,
        )
        self.assertTrue(d.ok)


class ProcessStateTests(unittest.TestCase):
    def test_external_state_passes(self) -> None:
        d = evaluate_process_state(
            state_outside_agent_context=True,
            authoritative_process_record=True,
        )
        self.assertTrue(d.ok)

    def test_agent_only_state_fails(self) -> None:
        d = evaluate_process_state(
            state_outside_agent_context=False,
            authoritative_process_record=False,
        )
        self.assertFalse(d.ok)


class ShadowAiTests(unittest.TestCase):
    def test_outside_approved_process_fails(self) -> None:
        d = evaluate_shadow_ai(
            tool_outside_approved_process=True,
            security_model_aligned=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_shadow_ai")

    def test_approved_surface_passes(self) -> None:
        d = evaluate_shadow_ai(
            tool_outside_approved_process=False,
            security_model_aligned=True,
        )
        self.assertTrue(d.ok)


class AgentCostTelemetryTests(unittest.TestCase):
    def test_opaque_cost_fails(self) -> None:
        d = evaluate_agent_cost_telemetry(
            token_calls=10,
            retries=1,
            human_review_volume=0,
            estimated_usd=1.0,
            telemetry_visible=False,
        )
        self.assertFalse(d.ok)

    def test_over_cap_fails(self) -> None:
        d = evaluate_agent_cost_telemetry(
            token_calls=1000,
            retries=50,
            human_review_volume=20,
            estimated_usd=25.0,
            operating_cap_usd=20.0,
            telemetry_visible=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_over_operating_cap")

    def test_visible_under_cap_passes(self) -> None:
        d = evaluate_agent_cost_telemetry(
            token_calls=5,
            retries=0,
            human_review_volume=1,
            estimated_usd=0.0,
            telemetry_visible=True,
        )
        self.assertTrue(d.ok)


class FiveOutcomesTests(unittest.TestCase):
    def test_all_five_pass(self) -> None:
        d = evaluate_five_outcomes(
            governance_at_runtime=True,
            interoperability=True,
            observability_and_control=True,
            cost_and_performance=True,
            business_outcomes=True,
        )
        self.assertTrue(d.ok)

    def test_incomplete_fails(self) -> None:
        d = evaluate_five_outcomes(
            governance_at_runtime=True,
            interoperability=True,
            observability_and_control=True,
            cost_and_performance=False,
            business_outcomes=True,
        )
        self.assertFalse(d.ok)


class RankTests(unittest.TestCase):
    def test_iap_beats_agent_count_vanity(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "agent-count-vanity",
                    "metric": "agent_count",
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "iap-control",
                    "metric": "iap_attempt",
                    "expected_iap_attempts": 2,
                    "effort": 1,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "iap-control")
        self.assertEqual(ranked[1]["score"], 0.0)


class PickClaimTests(unittest.TestCase):
    def test_picks_local_flow(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        d = pick_flow(flows=payload["flows"])
        self.assertTrue(d.ok)
        self.assertIn("uor:play-publish-control-layer", d.addresses)

    def test_cite_must_match(self) -> None:
        d = evaluate_claim(
            cite="uor:play-publish-control-layer",
            addresses=("uor:play-publish-control-layer",),
        )
        self.assertTrue(d.ok)


class CompletenessTests(unittest.TestCase):
    def test_incomplete_fails(self) -> None:
        d = require_universal_orchestration_controls(
            has_platform=True, has_flows=False, has_cite=True
        )
        self.assertFalse(d.ok)


class CliTests(unittest.TestCase):
    def test_cli_allows_local_flow(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_universal_orchestration.py"),
            "--platform",
            "ops_control_layer",
            "--flows",
            str(FIXTURE),
            "--cite",
            "uor:play-publish-control-layer",
            "--has-control-layer",
            "1",
            "--deterministic-policy",
            "1",
            "--authorized-actions-defined",
            "1",
            "--unauthorized-blocked",
            "1",
            "--irreversible-action",
            "1",
            "--approval-point",
            "1",
            "--rules-logged",
            "1",
            "--inputs-logged",
            "1",
            "--outputs-logged",
            "1",
            "--handoffs-logged",
            "1",
            "--next-step-routed",
            "1",
            "--result-persisted",
            "1",
            "--complexity-signals",
            "1",
            "--readiness-assessed",
            "1",
            "--focused-first-use-case",
            "1",
            "--shadow-tested",
            "1",
            "--going-live",
            "1",
            "--real-time-observability",
            "1",
            "--exceptions-surfaced",
            "1",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_cli_blocks_vendor(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_universal_orchestration.py"),
            "--platform",
            "decisions_saas_paid",
            "--flows",
            str(FIXTURE),
            "--cite",
            "uor:play-publish-control-layer",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["platform"]["ok"])


if __name__ == "__main__":
    unittest.main()
