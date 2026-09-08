"""Spotify shunt steal: intercept large reads. Fail closed. No Portal."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.token_shunt import (
    evaluate_context_return,
    evaluate_read_intercept,
    evaluate_task_route,
    rank_work,
    require_shunt_controls,
)


REPO = Path(__file__).resolve().parents[2]


class ReadInterceptTests(unittest.TestCase):
    def test_small_file_passes(self) -> None:
        d = evaluate_read_intercept(line_count=40, targeted=False)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_read")

    def test_large_untargeted_fails(self) -> None:
        d = evaluate_read_intercept(line_count=800, targeted=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_full_read")

    def test_large_targeted_passes(self) -> None:
        d = evaluate_read_intercept(line_count=800, targeted=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_read")


class TaskRouteTests(unittest.TestCase):
    def test_reasoning_on_hermes_main_passes(self) -> None:
        d = evaluate_task_route(task_kind="reasoning", model="hermes-main")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_frontier")

    def test_reasoning_on_flash_fails(self) -> None:
        d = evaluate_task_route(task_kind="debug", model="gemini-2.5-flash")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_delegate_reason")

    def test_boilerplate_on_local_slice_passes(self) -> None:
        d = evaluate_task_route(task_kind="boilerplate", model="local_slice")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_delegate")


class ContextReturnTests(unittest.TestCase):
    def test_slice_passes(self) -> None:
        d = evaluate_context_return(source_lines=800, returned_lines=40)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_slice")

    def test_full_dump_fails(self) -> None:
        d = evaluate_context_return(source_lines=800, returned_lines=800)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_full_dump")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_tokens(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "more-frontier-tokens",
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
        d = require_shunt_controls(
            has_read=False,
            has_route=False,
            has_return=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")

    def test_all_inputs_pass(self) -> None:
        d = require_shunt_controls(has_read=True, has_route=True, has_return=True)
        self.assertTrue(d.ok)


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "token_shunt.py")],
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
                str(REPO / "scripts" / "token_shunt.py"),
                "--lines",
                "800",
                "--targeted",
                "--task-kind",
                "reasoning",
                "--model",
                "hermes-main",
                "--source-lines",
                "800",
                "--returned-lines",
                "40",
            ],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["completeness"]["ok"])


if __name__ == "__main__":
    unittest.main()
