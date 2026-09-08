"""GitHub canvas steal: persist workflow state. Fail closed. No Copilot app."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.durable_canvas import (
    evaluate_claim,
    evaluate_source,
    evaluate_surface,
    persist_canvas,
    rank_work,
    require_canvas_controls,
)


REPO = Path(__file__).resolve().parents[2]

CANVAS = {
    "stages": [
        {"id": "paywall-view", "status": "observed"},
        {"id": "iap-attempt-path", "status": "open"},
    ],
    "drafts": {
        "iap-attempt-path": "19 viewed, 12 view, 9 dismiss, 0 attempts",
    },
    "approvals": ["human_gate"],
}


class SurfaceTests(unittest.TestCase):
    def test_local_canvas_passes(self) -> None:
        d = evaluate_surface(surface="local_canvas")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_canvas")

    def test_chat_only_fails(self) -> None:
        d = evaluate_surface(surface="chat_only")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_chat_scroll")

    def test_copilot_app_fails(self) -> None:
        d = evaluate_surface(surface="copilot_app")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")


class PersistTests(unittest.TestCase):
    def test_named_stages_and_drafts_pass(self) -> None:
        d = persist_canvas(canvas=CANVAS)
        self.assertTrue(d.ok)
        self.assertIn("stage:iap-attempt-path", d.addresses)
        self.assertIn("draft:iap-attempt-path", d.addresses)

    def test_empty_canvas_fails(self) -> None:
        d = persist_canvas(canvas={"stages": [], "drafts": {}})
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_empty_canvas")


class SourceTests(unittest.TestCase):
    def test_canvas_source_passes(self) -> None:
        d = evaluate_source(source="canvas")
        self.assertTrue(d.ok)

    def test_transcript_source_fails(self) -> None:
        d = evaluate_source(source="chat_transcript")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_chat_scroll")


class ClaimTests(unittest.TestCase):
    def test_cite_on_canvas_passes(self) -> None:
        d = evaluate_claim(
            cite="stage:iap-attempt-path",
            addresses=["stage:paywall-view", "stage:iap-attempt-path"],
        )
        self.assertTrue(d.ok)

    def test_invented_cite_fails(self) -> None:
        d = evaluate_claim(
            cite="stage:hallucinated-from-chat",
            addresses=["stage:iap-attempt-path"],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_canvas")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_canvas_ux(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "more-copilot-canvas",
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
        d = require_canvas_controls(
            has_surface=False, has_canvas=False, has_source=False, has_cite=False
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "durable_canvas.py")],
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
                str(REPO / "scripts" / "durable_canvas.py"),
                "--surface",
                "local_canvas",
                "--canvas",
                "scripts/tests/fixtures/durable_canvas_iap.json",
                "--source",
                "canvas",
                "--cite",
                "stage:iap-attempt-path",
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
