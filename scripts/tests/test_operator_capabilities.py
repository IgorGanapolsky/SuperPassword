"""Astra capabilities steal: local operator, medium effort. Fail closed. No Astra Pro."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.operator_capabilities import (
    evaluate_claim,
    evaluate_effort,
    evaluate_harness,
    evaluate_platform,
    evaluate_surface,
    pick_capability,
    rank_work,
    require_operator_controls,
)


REPO = Path(__file__).resolve().parents[2]

IAP_CAP = {
    "id": "iap-attempt-path",
    "surface": "local_cli",
    "harness": "browseros",
    "effort": "medium",
}
ASTRA_PRO = {
    "id": "chatgpt-pro-computer-use",
    "surface": "chatgpt_pro",
    "harness": "astra_desktop",
    "effort": "max",
}


class PlatformTests(unittest.TestCase):
    def test_local_operator_passes(self) -> None:
        d = evaluate_platform(platform="local_operator")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_operator")

    def test_gpt6_astra_api_fails(self) -> None:
        d = evaluate_platform(platform="gpt6_astra")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")

    def test_chatgpt_pro_fails(self) -> None:
        d = evaluate_platform(platform="chatgpt_pro")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")


class SurfaceTests(unittest.TestCase):
    def test_local_cli_passes(self) -> None:
        d = evaluate_surface(surface="local_cli")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_reusable_cli")

    def test_codex_app_fails(self) -> None:
        d = evaluate_surface(surface="chatgpt_codex")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_surface")


class HarnessTests(unittest.TestCase):
    def test_browseros_passes(self) -> None:
        d = evaluate_harness(harness="browseros")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_computer_use")

    def test_astra_desktop_fails(self) -> None:
        d = evaluate_harness(harness="astra_desktop")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_harness")


class EffortTests(unittest.TestCase):
    def test_medium_passes(self) -> None:
        d = evaluate_effort(effort="medium")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_medium_effort")

    def test_max_default_fails(self) -> None:
        d = evaluate_effort(effort="max")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_max_by_default")


class PickTests(unittest.TestCase):
    def test_picks_iap_local_cap(self) -> None:
        d = pick_capability(capabilities=[ASTRA_PRO, IAP_CAP])
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("cap:iap-attempt-path",))

    def test_only_astra_pro_fails(self) -> None:
        d = pick_capability(capabilities=[ASTRA_PRO])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_no_local_cap")


class ClaimTests(unittest.TestCase):
    def test_cite_picked_passes(self) -> None:
        d = evaluate_claim(cite="cap:iap-attempt-path", addresses=["cap:iap-attempt-path"])
        self.assertTrue(d.ok)

    def test_invented_cite_fails(self) -> None:
        d = evaluate_claim(cite="cap:astra-pro", addresses=["cap:iap-attempt-path"])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_operator")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_astra_upgrade(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "chatgpt-pro-upgrade",
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
        d = require_operator_controls(
            has_platform=False,
            has_capabilities=False,
            has_cite=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "operator_capabilities.py")],
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
                str(REPO / "scripts" / "operator_capabilities.py"),
                "--platform",
                "local_operator",
                "--capabilities",
                "scripts/tests/fixtures/operator_capabilities.json",
                "--cite",
                "cap:iap-attempt-path",
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
