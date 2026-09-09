"""Databricks steal: local eval + governance before production. Fail closed."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_eval_governance import (
    evaluate_claim,
    evaluate_evaluation,
    evaluate_governance,
    evaluate_platform,
    evaluate_stage,
    pick_path,
    rank_work,
    require_eval_gov_controls,
)


REPO = Path(__file__).resolve().parents[2]

IAP_PATH = {
    "id": "iap-attempt-path",
    "evaluation": "domain_kpi",
    "governance": "local_fail_closed",
    "stage": "production",
}
DATABRICKS_PILOT = {
    "id": "databricks-agent-bricks",
    "evaluation": "generic_benchmark",
    "governance": "ai_gateway",
    "stage": "pilot",
}


class PlatformTests(unittest.TestCase):
    def test_local_eval_gov_passes(self) -> None:
        d = evaluate_platform(platform="local_eval_governance")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_eval_gov")

    def test_databricks_platform_fails(self) -> None:
        d = evaluate_platform(platform="databricks")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_databricks_cloud")

    def test_ai_gateway_fails(self) -> None:
        d = evaluate_platform(platform="ai_gateway")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_databricks_cloud")


class EvaluationTests(unittest.TestCase):
    def test_domain_kpi_passes(self) -> None:
        d = evaluate_evaluation(evaluation="domain_kpi")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_domain_eval")

    def test_generic_benchmark_fails(self) -> None:
        d = evaluate_evaluation(evaluation="generic_benchmark")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_generic_benchmark")


class GovernanceTests(unittest.TestCase):
    def test_local_fail_closed_passes(self) -> None:
        d = evaluate_governance(governance="local_fail_closed")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_governance")

    def test_ai_gateway_fails(self) -> None:
        d = evaluate_governance(governance="ai_gateway")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_governance")


class StageTests(unittest.TestCase):
    def test_production_with_controls_passes(self) -> None:
        d = evaluate_stage(
            stage="production",
            evaluation_ok=True,
            governance_ok=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_production")

    def test_production_without_eval_fails(self) -> None:
        d = evaluate_stage(
            stage="production",
            evaluation_ok=False,
            governance_ok=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_production_without_controls")

    def test_pilot_without_controls_fails(self) -> None:
        d = evaluate_stage(
            stage="pilot",
            evaluation_ok=False,
            governance_ok=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_pilot_without_controls")


class PickTests(unittest.TestCase):
    def test_picks_iap_path(self) -> None:
        d = pick_path(paths=[DATABRICKS_PILOT, IAP_PATH])
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("path:iap-attempt-path",))

    def test_only_databricks_fails(self) -> None:
        d = pick_path(paths=[DATABRICKS_PILOT])
        self.assertFalse(d.ok)


class RankTests(unittest.TestCase):
    def test_iap_beats_multi_agent_proxy(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "multi-agent-count",
                    "metric": "multi_agent_count",
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "iap-attempt-path",
                    "metric": "iap_attempt",
                    "expected_iap_attempts": 3,
                    "effort": 1,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "iap-attempt-path")
        self.assertEqual(ranked[1]["score"], 0.0)


class CompletenessTests(unittest.TestCase):
    def test_incomplete_controls_fail(self) -> None:
        d = require_eval_gov_controls(
            has_platform=True, has_paths=False, has_cite=True
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliTests(unittest.TestCase):
    def test_cli_allows_local_path(self) -> None:
        fixture = REPO / "scripts/tests/fixtures/agent_eval_governance.json"
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/agent_eval_governance.py"),
                "--platform",
                "local_eval_governance",
                "--paths",
                str(fixture),
                "--cite",
                "path:iap-attempt-path",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["platform"]["ok"])
        self.assertTrue(payload["pick"]["ok"])
        self.assertTrue(payload["cite"]["ok"])

    def test_cli_blocks_databricks(self) -> None:
        fixture = REPO / "scripts/tests/fixtures/agent_eval_governance.json"
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/agent_eval_governance.py"),
                "--platform",
                "databricks",
                "--paths",
                str(fixture),
                "--cite",
                "path:iap-attempt-path",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
