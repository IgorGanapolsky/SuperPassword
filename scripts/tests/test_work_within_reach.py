"""OpenAI Friar steal: completed-task ROI. Fail closed. No SaaS."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.work_within_reach import (
    evaluate_attempt_efficiency,
    evaluate_capital_discipline,
    evaluate_completed_task,
    evaluate_discovery_to_paid,
    evaluate_human_judgment,
    evaluate_workload_fit,
    rank_work,
    require_reach_controls,
)


REPO = Path(__file__).resolve().parents[2]


class CompletedTaskTests(unittest.TestCase):
    def test_wqtu_is_a_completed_task(self) -> None:
        d = evaluate_completed_task(metric="wqtu")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_completed_task")

    def test_tokens_are_not_the_result(self) -> None:
        d = evaluate_completed_task(metric="tokens")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_proxy_output")


class AttemptEfficiencyTests(unittest.TestCase):
    def test_finished_task_passes(self) -> None:
        d = evaluate_attempt_efficiency(attempts=3, completed=1)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_efficient")

    def test_attempts_without_a_finish_fail(self) -> None:
        d = evaluate_attempt_efficiency(attempts=12, completed=0)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_attempts_without_finish")


class CapitalDisciplineTests(unittest.TestCase):
    def test_local_route_passes(self) -> None:
        d = evaluate_capital_discipline(
            service="hermes_main",
            monthly_usd=0,
            month_to_date_usd=0,
            demand="tool turns",
            days_to_productive=0,
        )
        self.assertTrue(d.ok)

    def test_new_metered_model_fails(self) -> None:
        d = evaluate_capital_discipline(
            service="gpt6_astra",
            monthly_usd=0,
            month_to_date_usd=0,
            demand="smarter chat",
            days_to_productive=1,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")

    def test_over_cap_fails(self) -> None:
        d = evaluate_capital_discipline(
            service="local_pytest",
            monthly_usd=21,
            month_to_date_usd=0,
            demand="tests",
            days_to_productive=0,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_over_cap")


class WorkloadFitTests(unittest.TestCase):
    def test_tool_turn_on_hermes_main_passes(self) -> None:
        d = evaluate_workload_fit(task_kind="tool_turn", model="hermes-main")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_fit")

    def test_tool_turn_on_3b_fails(self) -> None:
        d = evaluate_workload_fit(task_kind="tool_turn", model="qwen2.5:3b-hermes-64k")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_weak_route")


class DiscoveryToPaidTests(unittest.TestCase):
    def test_wall_after_a_completed_session_passes(self) -> None:
        d = evaluate_discovery_to_paid(timer_completed=1, paywall_shown=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_earned_wall")

    def test_wall_before_any_finish_fails(self) -> None:
        d = evaluate_discovery_to_paid(timer_completed=0, paywall_shown=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_premature_wall")


class HumanJudgmentTests(unittest.TestCase):
    def test_human_sets_priority_and_judges(self) -> None:
        d = evaluate_human_judgment(
            human_role="judgment",
            priority_set=True,
            result_judged=True,
        )
        self.assertTrue(d.ok)

    def test_human_cleanup_fails(self) -> None:
        d = evaluate_human_judgment(
            human_role="cleanup",
            priority_set=False,
            result_judged=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_human_cleanup")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_tokens(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "more-tokens",
                    "metric": "tokens",
                    "expected_completed_tasks": 0,
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "iap-attempt-path",
                    "metric": "iap_attempt",
                    "expected_completed_tasks": 0,
                    "expected_iap_attempts": 6,
                    "effort": 2,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "iap-attempt-path")


class CompletenessTests(unittest.TestCase):
    def test_missing_inputs_fail_closed(self) -> None:
        d = require_reach_controls(
            has_task=False,
            has_efficiency=False,
            has_capital=False,
            has_fit=False,
            has_discovery=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")

    def test_all_inputs_pass(self) -> None:
        d = require_reach_controls(
            has_task=True,
            has_efficiency=True,
            has_capital=True,
            has_fit=True,
            has_discovery=True,
        )
        self.assertTrue(d.ok)


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "work_within_reach.py")],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["completeness"]["ok"])

    def test_complete_cli_exits_zero(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "work_within_reach.py"),
                "--metric",
                "wqtu",
                "--attempts",
                "3",
                "--completed",
                "1",
                "--service",
                "hermes_main",
                "--demand",
                "tool turns",
                "--monthly-usd",
                "0",
                "--mtd-usd",
                "0",
                "--task-kind",
                "tool_turn",
                "--model",
                "hermes-main",
                "--timer-completed",
                "1",
                "--paywall-shown",
            ],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["completeness"]["ok"])


if __name__ == "__main__":
    unittest.main()
