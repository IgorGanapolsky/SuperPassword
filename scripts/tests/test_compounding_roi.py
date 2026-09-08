"""PlayerZero steal: compounding ROI control plane. Fail closed. No SaaS."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.compounding_roi import (
    LIFECYCLE_STAGES,
    evaluate_compounding_cycle,
    evaluate_hawk_metrics,
    evaluate_judgment_handoff,
    evaluate_lifecycle_handoff,
    evaluate_prevention_recipe,
    evaluate_world_model,
    rank_work,
    require_compounding_controls,
)


REPO = Path(__file__).resolve().parents[2]


class LifecycleHandoffTests(unittest.TestCase):
    def test_seven_stages_are_mapped(self) -> None:
        self.assertEqual(
            LIFECYCLE_STAGES,
            (
                "planning",
                "coding",
                "review",
                "docs",
                "quality",
                "triage",
                "sre",
            ),
        )

    def test_incident_that_feeds_quality_and_review_passes(self) -> None:
        d = evaluate_lifecycle_handoff(
            source_stage="sre",
            target_stages=["quality", "review", "planning"],
            shared_context_id="incident-paywall-dismiss-20260908",
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_multiplayer")

    def test_reset_at_handoff_fails(self) -> None:
        d = evaluate_lifecycle_handoff(
            source_stage="sre",
            target_stages=[],
            shared_context_id="",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_single_player")

    def test_unknown_stage_fails(self) -> None:
        d = evaluate_lifecycle_handoff(
            source_stage="newsletter",
            target_stages=["quality"],
            shared_context_id="x",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unknown_stage")


class HawkMetricsTests(unittest.TestCase):
    def test_velocity_only_dashboard_fails(self) -> None:
        d = evaluate_hawk_metrics(
            metrics=["pr_velocity", "tokens_consumed", "deploy_frequency"]
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_velocity_proxy")

    def test_prevention_metrics_pass(self) -> None:
        d = evaluate_hawk_metrics(
            metrics=[
                "wqtu",
                "paywall_attempt_success",
                "incident_recurrence",
                "defect_escape_rate",
            ]
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_hawk_metrics")

    def test_empty_metrics_fail_closed(self) -> None:
        d = evaluate_hawk_metrics(metrics=[])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_velocity_proxy")


class PreventionRecipeTests(unittest.TestCase):
    def test_local_fix_without_watch_fails(self) -> None:
        d = evaluate_prevention_recipe(
            resolved=True,
            pattern="",
            gate="",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_recovery_only")

    def test_encoded_watch_passes(self) -> None:
        d = evaluate_prevention_recipe(
            resolved=True,
            pattern="paywall_view with zero purchase_attempt",
            gate="scripts/compounding_roi.py --require-prevention",
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_prevention")

    def test_unresolved_incident_cannot_claim_prevention(self) -> None:
        d = evaluate_prevention_recipe(
            resolved=False,
            pattern="catalog empty",
            gate="play catalog readback",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unresolved")


class CompoundingCycleTests(unittest.TestCase):
    def test_full_cycle_passes(self) -> None:
        d = evaluate_compounding_cycle(
            links={
                "quality_to_simulation": True,
                "simulation_to_prevention": True,
                "prevention_to_triage": True,
                "triage_to_knowledge": True,
                "knowledge_to_simulation": True,
            }
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_compounding")

    def test_broken_cycle_fails(self) -> None:
        d = evaluate_compounding_cycle(
            links={
                "quality_to_simulation": True,
                "simulation_to_prevention": False,
                "prevention_to_triage": True,
                "triage_to_knowledge": True,
                "knowledge_to_simulation": True,
            }
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_linear_gains")


class WorldModelTests(unittest.TestCase):
    def test_session_only_memory_fails(self) -> None:
        d = evaluate_world_model(
            sources=["session_chat"],
            persists=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_session_reset")

    def test_code_telemetry_deploys_and_resolutions_pass(self) -> None:
        d = evaluate_world_model(
            sources=["code", "telemetry", "deploys", "resolution_history"],
            persists=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_world_model")


class JudgmentHandoffTests(unittest.TestCase):
    def test_cleanup_request_fails(self) -> None:
        d = evaluate_judgment_handoff(
            root_cause="unknown",
            blast_radius="",
            decision="",
            human_role="cleanup",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_human_cleanup")

    def test_assembled_judgment_passes(self) -> None:
        d = evaluate_judgment_handoff(
            root_cause="paywall_view with no catalog SKU",
            blast_radius="free users on Android 1.3.56+",
            decision="keep catalog readback before claim live",
            human_role="judgment",
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_judgment")


class RankWorkTests(unittest.TestCase):
    def test_paywall_leak_outranks_pr_velocity(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "faster-prs",
                    "metric": "pr_velocity",
                    "expected_wqtu_delta": 0,
                    "expected_paywall_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "paywall-attempt-path",
                    "metric": "paywall_attempt_success",
                    "expected_wqtu_delta": 0,
                    "expected_paywall_attempts": 6,
                    "effort": 2,
                },
                {
                    "id": "activation-to-wqtu",
                    "metric": "wqtu",
                    "expected_wqtu_delta": 2,
                    "expected_paywall_attempts": 0,
                    "effort": 3,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "paywall-attempt-path")
        self.assertNotEqual(ranked[0]["id"], "faster-prs")

    def test_rejects_empty_candidate_list(self) -> None:
        ranked = rank_work(candidates=[])
        self.assertEqual(ranked, [])


class CompletenessTests(unittest.TestCase):
    def test_missing_inputs_fail_closed(self) -> None:
        d = require_compounding_controls(
            has_lifecycle=False,
            has_metrics=False,
            has_prevention=False,
            has_cycle=False,
            has_world_model=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")

    def test_all_inputs_pass(self) -> None:
        d = require_compounding_controls(
            has_lifecycle=True,
            has_metrics=True,
            has_prevention=True,
            has_cycle=True,
            has_world_model=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "controls_complete")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "compounding_roi.py")],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["completeness"]["ok"])


if __name__ == "__main__":
    unittest.main()
