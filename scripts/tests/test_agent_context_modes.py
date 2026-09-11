"""LangChain multi-agent context-mode steal: isolated vs fork. Fail closed."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_context_modes import (
    evaluate_claim,
    evaluate_context_mode,
    evaluate_monoculture,
    evaluate_parallel_research,
    evaluate_permissions,
    evaluate_platform,
    evaluate_return_shape,
    evaluate_waste,
    pick_harness,
    rank_work,
    require_context_mode_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_context_modes.json"


class PlatformTests(unittest.TestCase):
    def test_local_passes(self) -> None:
        self.assertTrue(evaluate_platform(platform="supervisor_subagent_harness").ok)

    def test_langsmith_fails(self) -> None:
        d = evaluate_platform(platform="langsmith_paid_seat")
        self.assertFalse(d.ok)


class PairingTests(unittest.TestCase):
    def test_worker_fork_passes(self) -> None:
        d = evaluate_context_mode(role="fixer", mode="fork")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_worker_fork")

    def test_worker_isolated_fails(self) -> None:
        d = evaluate_context_mode(role="worker", mode="isolated")
        self.assertFalse(d.ok)

    def test_verifier_isolated_passes(self) -> None:
        d = evaluate_context_mode(role="reviewer", mode="isolated")
        self.assertTrue(d.ok)

    def test_verifier_fork_fails(self) -> None:
        d = evaluate_context_mode(role="verifier", mode="fork")
        self.assertFalse(d.ok)

    def test_researcher_isolated_passes(self) -> None:
        d = evaluate_context_mode(role="researcher", mode="isolated")
        self.assertTrue(d.ok)

    def test_memory_fork_passes(self) -> None:
        d = evaluate_context_mode(role="memorizer", mode="fork")
        self.assertTrue(d.ok)

    def test_memory_isolated_fails(self) -> None:
        d = evaluate_context_mode(role="memory", mode="isolated")
        self.assertFalse(d.ok)


class WasteTests(unittest.TestCase):
    def test_isolated_worker_waste_fails(self) -> None:
        d = evaluate_waste(
            supervisor_already_gathered_context=True,
            mode="isolated",
            role="fixer",
        )
        self.assertFalse(d.ok)

    def test_fork_worker_ok(self) -> None:
        d = evaluate_waste(
            supervisor_already_gathered_context=True,
            mode="fork",
            role="fixer",
        )
        self.assertTrue(d.ok)


class ReturnShapeTests(unittest.TestCase):
    def test_outcome_only_passes(self) -> None:
        d = evaluate_return_shape(
            supervisor_receives_final_only=True,
            intermediate_reasoning_leaked=False,
        )
        self.assertTrue(d.ok)

    def test_leak_fails(self) -> None:
        d = evaluate_return_shape(
            supervisor_receives_final_only=False,
            intermediate_reasoning_leaked=True,
        )
        self.assertFalse(d.ok)


class ParallelTests(unittest.TestCase):
    def test_parallel_isolated_passes(self) -> None:
        d = evaluate_parallel_research(parallel_count=3, mode="isolated")
        self.assertTrue(d.ok)

    def test_parallel_fork_fails(self) -> None:
        d = evaluate_parallel_research(parallel_count=3, mode="fork")
        self.assertFalse(d.ok)


class PermissionTests(unittest.TestCase):
    def test_memory_restricted_passes(self) -> None:
        d = evaluate_permissions(write_paths_restricted=True, role="memorizer")
        self.assertTrue(d.ok)

    def test_memory_unrestricted_fails(self) -> None:
        d = evaluate_permissions(write_paths_restricted=False, role="memorizer")
        self.assertFalse(d.ok)


class MonocultureTests(unittest.TestCase):
    def test_by_role_passes(self) -> None:
        self.assertTrue(
            evaluate_monoculture(force_all_fork=False, force_all_isolated=False).ok
        )

    def test_all_fork_fails(self) -> None:
        self.assertFalse(
            evaluate_monoculture(force_all_fork=True, force_all_isolated=False).ok
        )


class RankTests(unittest.TestCase):
    def test_iap_beats_span_vanity(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "langsmith-span-vanity",
                    "metric": "langsmith_spans",
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "iap-fixer-fork",
                    "metric": "iap_attempt",
                    "expected_iap_attempts": 2,
                    "effort": 1,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "iap-fixer-fork")
        self.assertEqual(ranked[1]["score"], 0.0)


class PickClaimTests(unittest.TestCase):
    def test_picks_local(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        d = pick_harness(harnesses=payload["harnesses"])
        self.assertTrue(d.ok)
        self.assertIn("acm:iap-fixer-fork", d.addresses)

    def test_cite_must_match(self) -> None:
        d = evaluate_claim(
            cite="acm:iap-fixer-fork", addresses=("acm:iap-fixer-fork",)
        )
        self.assertTrue(d.ok)


class CompletenessTests(unittest.TestCase):
    def test_incomplete_fails(self) -> None:
        d = require_context_mode_controls(
            has_platform=True, has_harnesses=False, has_cite=True
        )
        self.assertFalse(d.ok)


class CliTests(unittest.TestCase):
    def test_cli_allows_worker_fork(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_context_modes.py"),
            "--platform",
            "supervisor_subagent_harness",
            "--harnesses",
            str(FIXTURE),
            "--cite",
            "acm:iap-fixer-fork",
            "--role",
            "fixer",
            "--mode",
            "fork",
            "--supervisor-already-gathered-context",
            "1",
            "--supervisor-receives-final-only",
            "1",
            "--write-paths-restricted",
            "1",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_cli_blocks_langsmith(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_context_modes.py"),
            "--platform",
            "langsmith_paid_seat",
            "--harnesses",
            str(FIXTURE),
            "--cite",
            "acm:iap-fixer-fork",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["platform"]["ok"])


if __name__ == "__main__":
    unittest.main()
