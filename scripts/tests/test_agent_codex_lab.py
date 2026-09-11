"""OpenAI Codex / MIT EQuS lab steal: calibration loops for ops. Fail closed."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_codex_lab import (
    evaluate_claim,
    evaluate_human_focus,
    evaluate_interdependent_chain,
    evaluate_measurement_skill,
    evaluate_platform,
    evaluate_routine_vs_novel,
    evaluate_signal_quality,
    evaluate_unattended_run,
    pick_loop,
    rank_work,
    require_codex_lab_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_codex_lab.json"


class PlatformTests(unittest.TestCase):
    def test_local_passes(self) -> None:
        d = evaluate_platform(platform="ops_calibration_loop")
        self.assertTrue(d.ok)

    def test_quantum_spend_fails(self) -> None:
        d = evaluate_platform(platform="quantum_hardware_spend")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_quantum_spend")


class SkillTests(unittest.TestCase):
    def test_complete_skill_passes(self) -> None:
        d = evaluate_measurement_skill(
            has_skill=True,
            has_prerequisites=True,
            has_success_fail_criteria=True,
            has_template=True,
        )
        self.assertTrue(d.ok)

    def test_incomplete_skill_fails(self) -> None:
        d = evaluate_measurement_skill(
            has_skill=True,
            has_prerequisites=False,
            has_success_fail_criteria=True,
            has_template=True,
        )
        self.assertFalse(d.ok)


class ChainTests(unittest.TestCase):
    def test_persisted_chain_passes(self) -> None:
        d = evaluate_interdependent_chain(
            prerequisites_complete=True,
            result_persisted=True,
            skipped_step=False,
        )
        self.assertTrue(d.ok)

    def test_skip_fails(self) -> None:
        d = evaluate_interdependent_chain(
            prerequisites_complete=True,
            result_persisted=False,
            skipped_step=True,
        )
        self.assertFalse(d.ok)


class SignalTests(unittest.TestCase):
    def test_clear_autonomous_passes(self) -> None:
        d = evaluate_signal_quality(
            signal_clear=True, signal_noisy=False, human_escalated=False
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_autonomous_measurement")

    def test_noisy_without_escalation_fails(self) -> None:
        d = evaluate_signal_quality(
            signal_clear=False, signal_noisy=True, human_escalated=False
        )
        self.assertFalse(d.ok)

    def test_noisy_with_escalation_passes(self) -> None:
        d = evaluate_signal_quality(
            signal_clear=False, signal_noisy=True, human_escalated=True
        )
        self.assertTrue(d.ok)


class ModeTests(unittest.TestCase):
    def test_routine_passes(self) -> None:
        d = evaluate_routine_vs_novel(
            routine_workflow=True, novel_experiment=False, narrow_goal=False
        )
        self.assertTrue(d.ok)

    def test_novel_without_narrow_fails(self) -> None:
        d = evaluate_routine_vs_novel(
            routine_workflow=False, novel_experiment=True, narrow_goal=False
        )
        self.assertFalse(d.ok)

    def test_novel_narrow_passes(self) -> None:
        d = evaluate_routine_vs_novel(
            routine_workflow=False, novel_experiment=True, narrow_goal=True
        )
        self.assertTrue(d.ok)


class UnattendedTests(unittest.TestCase):
    def test_steer_hooks_pass(self) -> None:
        d = evaluate_unattended_run(
            progress_log=True, check_in_possible=True, steer_hook=True
        )
        self.assertTrue(d.ok)

    def test_blind_fails(self) -> None:
        d = evaluate_unattended_run(
            progress_log=False, check_in_possible=False, steer_hook=False
        )
        self.assertFalse(d.ok)


class PairingTests(unittest.TestCase):
    def test_pairing_passes(self) -> None:
        d = evaluate_human_focus(
            agent_owns_routine=True, human_owns_design_analysis=True
        )
        self.assertTrue(d.ok)

    def test_role_inversion_fails(self) -> None:
        d = evaluate_human_focus(
            agent_owns_routine=False, human_owns_design_analysis=False
        )
        self.assertFalse(d.ok)


class RankTests(unittest.TestCase):
    def test_iap_beats_qubit_vanity(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "qubit-press",
                    "metric": "qubit_count",
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "iap-calibration",
                    "metric": "iap_attempt",
                    "expected_iap_attempts": 2,
                    "effort": 1,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "iap-calibration")
        self.assertEqual(ranked[1]["score"], 0.0)


class PickClaimTests(unittest.TestCase):
    def test_picks_local_loop(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        d = pick_loop(loops=payload["loops"])
        self.assertTrue(d.ok)
        self.assertIn("cxl:play-release-calibration", d.addresses)

    def test_cite_must_match(self) -> None:
        d = evaluate_claim(
            cite="cxl:play-release-calibration",
            addresses=("cxl:play-release-calibration",),
        )
        self.assertTrue(d.ok)


class CompletenessTests(unittest.TestCase):
    def test_incomplete_fails(self) -> None:
        d = require_codex_lab_controls(
            has_platform=True, has_loops=False, has_cite=True
        )
        self.assertFalse(d.ok)


class CliTests(unittest.TestCase):
    def test_cli_allows_local_loop(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_codex_lab.py"),
            "--platform",
            "ops_calibration_loop",
            "--loops",
            str(FIXTURE),
            "--cite",
            "cxl:play-release-calibration",
            "--has-skill",
            "1",
            "--has-prerequisites",
            "1",
            "--has-success-fail-criteria",
            "1",
            "--has-template",
            "1",
            "--prerequisites-complete",
            "1",
            "--result-persisted",
            "1",
            "--signal-clear",
            "1",
            "--routine-workflow",
            "1",
            "--progress-log",
            "1",
            "--check-in-possible",
            "1",
            "--steer-hook",
            "1",
            "--agent-owns-routine",
            "1",
            "--human-owns-design-analysis",
            "1",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_cli_blocks_quantum(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_codex_lab.py"),
            "--platform",
            "quantum_hardware_spend",
            "--loops",
            str(FIXTURE),
            "--cite",
            "cxl:play-release-calibration",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["platform"]["ok"])


if __name__ == "__main__":
    unittest.main()
