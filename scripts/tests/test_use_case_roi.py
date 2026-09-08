"""Dataiku steal: score use cases, pick one. Fail closed. No Dataiku."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.use_case_roi import (
    evaluate_claim,
    evaluate_platform,
    evaluate_problem,
    pick_one,
    rank_work,
    require_use_case_controls,
    score_use_case,
)


REPO = Path(__file__).resolve().parents[2]

IAP_CASE = {
    "id": "iap-attempt-path",
    "roi": 3,
    "complexity": 1,
    "readiness": 3,
}
DEMO_CASE = {
    "id": "dataiku-predictive-maintenance",
    "roi": 1,
    "complexity": 3,
    "readiness": 1,
}


class PlatformTests(unittest.TestCase):
    def test_local_score_passes(self) -> None:
        d = evaluate_platform(platform="local_score")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_score")

    def test_dataiku_fails(self) -> None:
        d = evaluate_platform(platform="dataiku")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")

    def test_llm_mesh_fails(self) -> None:
        d = evaluate_platform(platform="llm_mesh")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")


class ProblemTests(unittest.TestCase):
    def test_iap_problem_passes(self) -> None:
        d = evaluate_problem(problem="iap_attempt")
        self.assertTrue(d.ok)

    def test_demo_problem_fails(self) -> None:
        d = evaluate_problem(problem="agent_demo")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_tech_first")


class ScoreTests(unittest.TestCase):
    def test_sweet_spot_passes(self) -> None:
        d = score_use_case(case=IAP_CASE)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_sweet_spot")
        self.assertIn("case:iap-attempt-path", d.addresses)

    def test_low_value_hard_case_fails(self) -> None:
        d = score_use_case(case=DEMO_CASE)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_low_roi")


class PickOneTests(unittest.TestCase):
    def test_picks_sweet_spot_only(self) -> None:
        d = pick_one(cases=[DEMO_CASE, IAP_CASE])
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("case:iap-attempt-path",))

    def test_no_sweet_spot_fails(self) -> None:
        d = pick_one(cases=[DEMO_CASE])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_no_pick")


class ClaimTests(unittest.TestCase):
    def test_cite_picked_case_passes(self) -> None:
        d = evaluate_claim(cite="case:iap-attempt-path", addresses=["case:iap-attempt-path"])
        self.assertTrue(d.ok)

    def test_invented_case_fails(self) -> None:
        d = evaluate_claim(cite="case:clinical-trial-agent", addresses=["case:iap-attempt-path"])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_score")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_agents(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "more-dataiku-agents",
                    "metric": "tokens",
                    "expected_iap_attempts": 0,
                    "expected_completed_tasks": 0,
                    "effort": 1,
                },
                {
                    "id": "iap-attempt-path",
                    "metric": "iap_attempt",
                    "expected_iap_attempts": 6,
                    "expected_completed_tasks": 0,
                    "effort": 2,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "iap-attempt-path")


class CompletenessTests(unittest.TestCase):
    def test_missing_inputs_fail_closed(self) -> None:
        d = require_use_case_controls(
            has_platform=False, has_problem=False, has_cases=False, has_cite=False
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "use_case_roi.py")],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(json.loads(proc.stdout)["completeness"]["ok"])

    def test_complete_cli_exits_zero(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "use_case_roi.py"),
                "--platform",
                "local_score",
                "--problem",
                "iap_attempt",
                "--cases",
                "scripts/tests/fixtures/use_case_roi.json",
                "--cite",
                "case:iap-attempt-path",
            ],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertTrue(json.loads(proc.stdout)["completeness"]["ok"])


if __name__ == "__main__":
    unittest.main()
