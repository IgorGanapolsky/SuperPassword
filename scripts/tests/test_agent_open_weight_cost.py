"""Open-weight cost episode steal: unit economics + routing. Fail closed."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_open_weight_cost import (
    evaluate_apples_to_apples,
    evaluate_baseline,
    evaluate_claim,
    evaluate_exploration_vs_commit,
    evaluate_fully_loaded_cost,
    evaluate_pilot,
    evaluate_platform,
    evaluate_routing,
    evaluate_strategic_leverage,
    evaluate_workload_fit,
    fully_loaded_cost_per_success,
    pick_workload,
    rank_work,
    require_open_weight_cost_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_open_weight_cost.json"


class PlatformTests(unittest.TestCase):
    def test_local_passes(self) -> None:
        self.assertTrue(evaluate_platform(platform="hybrid_model_routing").ok)

    def test_ideology_spend_fails(self) -> None:
        d = evaluate_platform(platform="gpu_fleet_ideology_spend")
        self.assertFalse(d.ok)


class BaselineTests(unittest.TestCase):
    def test_complete_baseline_passes(self) -> None:
        d = evaluate_baseline(
            monthly_api_spend_known=True,
            tokens_by_task_known=True,
            latency_known=True,
            error_retry_known=True,
            human_review_known=True,
        )
        self.assertTrue(d.ok)

    def test_incomplete_fails(self) -> None:
        d = evaluate_baseline(
            monthly_api_spend_known=True,
            tokens_by_task_known=False,
            latency_known=True,
            error_retry_known=True,
            human_review_known=True,
        )
        self.assertFalse(d.ok)


class FitTests(unittest.TestCase):
    def test_stable_volume_passes(self) -> None:
        d = evaluate_workload_fit(
            stable_high_volume=True,
            quality_bar_measurable=True,
            sporadic_low_volume=False,
        )
        self.assertTrue(d.ok)

    def test_sporadic_fails(self) -> None:
        d = evaluate_workload_fit(
            stable_high_volume=False,
            quality_bar_measurable=True,
            sporadic_low_volume=True,
        )
        self.assertFalse(d.ok)


class EvalTests(unittest.TestCase):
    def test_real_eval_passes(self) -> None:
        d = evaluate_apples_to_apples(
            real_prompts=True,
            real_failure_cases=True,
            measured_task_success=True,
            measured_schema_adherence=True,
            measured_human_intervention=True,
            benchmark_only=False,
        )
        self.assertTrue(d.ok)

    def test_benchmark_only_fails(self) -> None:
        d = evaluate_apples_to_apples(
            real_prompts=False,
            real_failure_cases=False,
            measured_task_success=False,
            measured_schema_adherence=False,
            measured_human_intervention=False,
            benchmark_only=True,
        )
        self.assertFalse(d.ok)


class TcoTests(unittest.TestCase):
    def test_unit_cost_math(self) -> None:
        self.assertEqual(
            fully_loaded_cost_per_success(
                monthly_operating_cost_usd=10.0, successful_tasks_per_month=100.0
            ),
            0.1,
        )

    def test_tco_passes_under_cap(self) -> None:
        d = evaluate_fully_loaded_cost(
            monthly_operating_cost_usd=5.0,
            successful_tasks_per_month=50.0,
            includes_hosting_ops_review=True,
            utilization_adequate=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.value, 0.1)

    def test_over_cap_fails(self) -> None:
        d = evaluate_fully_loaded_cost(
            monthly_operating_cost_usd=50.0,
            successful_tasks_per_month=50.0,
            includes_hosting_ops_review=True,
            utilization_adequate=True,
        )
        self.assertFalse(d.ok)

    def test_low_util_fails(self) -> None:
        d = evaluate_fully_loaded_cost(
            monthly_operating_cost_usd=5.0,
            successful_tasks_per_month=50.0,
            includes_hosting_ops_review=True,
            utilization_adequate=False,
        )
        self.assertFalse(d.ok)


class RoutingTests(unittest.TestCase):
    def test_hybrid_passes(self) -> None:
        d = evaluate_routing(
            cheap_first_pass=True,
            escalate_low_confidence=True,
            all_open_forced=False,
            all_proprietary_forced=False,
        )
        self.assertTrue(d.ok)

    def test_monoculture_fails(self) -> None:
        d = evaluate_routing(
            cheap_first_pass=True,
            escalate_low_confidence=True,
            all_open_forced=True,
            all_proprietary_forced=False,
        )
        self.assertFalse(d.ok)


class LeverageTests(unittest.TestCase):
    def test_locality_passes(self) -> None:
        d = evaluate_strategic_leverage(
            data_locality=True,
            custom_finetune=False,
            offline_edge=False,
            predictable_marginal_cost=False,
            vendor_independence_only=False,
        )
        self.assertTrue(d.ok)

    def test_vendor_only_fails(self) -> None:
        d = evaluate_strategic_leverage(
            data_locality=False,
            custom_finetune=False,
            offline_edge=False,
            predictable_marginal_cost=False,
            vendor_independence_only=True,
        )
        self.assertFalse(d.ok)


class PilotTests(unittest.TestCase):
    def test_pilot_passes(self) -> None:
        d = evaluate_pilot(
            quality_within_tolerance=True,
            latency_meets_ux=True,
            savings_exceed_ops_cost=True,
            review_window_days=45,
            api_fallback=True,
        )
        self.assertTrue(d.ok)

    def test_no_fallback_fails(self) -> None:
        d = evaluate_pilot(
            quality_within_tolerance=True,
            latency_meets_ux=True,
            savings_exceed_ops_cost=True,
            review_window_days=45,
            api_fallback=False,
        )
        self.assertFalse(d.ok)


class PhaseTests(unittest.TestCase):
    def test_api_first_exploration(self) -> None:
        d = evaluate_exploration_vs_commit(
            exploration_phase=True,
            utilization_justifies=False,
            tco_justifies=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_api_first")

    def test_commit_when_justified(self) -> None:
        d = evaluate_exploration_vs_commit(
            exploration_phase=False,
            utilization_justifies=True,
            tco_justifies=True,
        )
        self.assertTrue(d.ok)


class RankTests(unittest.TestCase):
    def test_iap_beats_independence_vanity(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "vendor-independence-vanity",
                    "metric": "vendor_independence_score",
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "iap-extract-routing",
                    "metric": "iap_attempt",
                    "expected_iap_attempts": 2,
                    "effort": 1,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "iap-extract-routing")
        self.assertEqual(ranked[1]["score"], 0.0)


class PickClaimTests(unittest.TestCase):
    def test_picks_local_workload(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        d = pick_workload(workloads=payload["workloads"])
        self.assertTrue(d.ok)
        self.assertIn("owc:iap-extract-routing", d.addresses)

    def test_cite_must_match(self) -> None:
        d = evaluate_claim(
            cite="owc:iap-extract-routing",
            addresses=("owc:iap-extract-routing",),
        )
        self.assertTrue(d.ok)


class CompletenessTests(unittest.TestCase):
    def test_incomplete_fails(self) -> None:
        d = require_open_weight_cost_controls(
            has_platform=True, has_workloads=False, has_cite=True
        )
        self.assertFalse(d.ok)


class CliTests(unittest.TestCase):
    def test_cli_allows_hybrid(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_open_weight_cost.py"),
            "--platform",
            "hybrid_model_routing",
            "--workloads",
            str(FIXTURE),
            "--cite",
            "owc:iap-extract-routing",
            "--monthly-api-spend-known",
            "1",
            "--tokens-by-task-known",
            "1",
            "--latency-known",
            "1",
            "--error-retry-known",
            "1",
            "--human-review-known",
            "1",
            "--stable-high-volume",
            "1",
            "--quality-bar-measurable",
            "1",
            "--real-prompts",
            "1",
            "--real-failure-cases",
            "1",
            "--measured-task-success",
            "1",
            "--measured-schema-adherence",
            "1",
            "--measured-human-intervention",
            "1",
            "--monthly-operating-cost-usd",
            "5",
            "--successful-tasks-per-month",
            "50",
            "--includes-hosting-ops-review",
            "1",
            "--utilization-adequate",
            "1",
            "--cheap-first-pass",
            "1",
            "--escalate-low-confidence",
            "1",
            "--data-locality",
            "1",
            "--quality-within-tolerance",
            "1",
            "--latency-meets-ux",
            "1",
            "--savings-exceed-ops-cost",
            "1",
            "--review-window-days",
            "45",
            "--api-fallback",
            "1",
            "--exploration-phase",
            "0",
            "--utilization-justifies",
            "1",
            "--tco-justifies",
            "1",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_cli_blocks_ideology(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_open_weight_cost.py"),
            "--platform",
            "gpu_fleet_ideology_spend",
            "--workloads",
            str(FIXTURE),
            "--cite",
            "owc:iap-extract-routing",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["platform"]["ok"])


if __name__ == "__main__":
    unittest.main()
