"""IBM STAIR steal: TOC-addressed retrieval. Fail closed. No fine-tune."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.stair_toc import (
    evaluate_chunking,
    evaluate_grounding,
    extract_toc,
    rank_work,
    require_stair_controls,
    retrieve_by_toc,
)


REPO = Path(__file__).resolve().parents[2]

SAMPLE = """# Agent work

## Live evidence

WQTU is three.

## Fail-closed CLI

Incomplete inputs exit two.
"""


class ExtractTocTests(unittest.TestCase):
    def test_headings_become_addresses(self) -> None:
        toc = extract_toc(markdown=SAMPLE, source="docs/AGENT_WORK_WITHIN_REACH.md")
        addresses = [row["address"] for row in toc]
        self.assertIn("docs/AGENT_WORK_WITHIN_REACH.md#live-evidence", addresses)
        self.assertIn("docs/AGENT_WORK_WITHIN_REACH.md#fail-closed-cli", addresses)

    def test_empty_markdown_fails_closed(self) -> None:
        toc = extract_toc(markdown="", source="docs/empty.md")
        self.assertEqual(toc, [])


class ChunkingTests(unittest.TestCase):
    def test_toc_mode_passes(self) -> None:
        d = evaluate_chunking(mode="toc")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_toc")

    def test_length_chunks_fail(self) -> None:
        d = evaluate_chunking(mode="length")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_length_chunk")


class RetrieveTests(unittest.TestCase):
    def test_query_hits_heading(self) -> None:
        toc = extract_toc(markdown=SAMPLE, source="docs/AGENT_WORK_WITHIN_REACH.md")
        hit = retrieve_by_toc(query="live evidence WQTU", toc=toc)
        self.assertTrue(hit.ok)
        self.assertIn("live-evidence", str(hit.reason))

    def test_empty_toc_fails(self) -> None:
        hit = retrieve_by_toc(query="anything", toc=[])
        self.assertFalse(hit.ok)
        self.assertEqual(hit.action, "block_no_structure")


class GroundingTests(unittest.TestCase):
    def test_real_address_passes(self) -> None:
        toc = extract_toc(markdown=SAMPLE, source="docs/AGENT_WORK_WITHIN_REACH.md")
        d = evaluate_grounding(
            cited="docs/AGENT_WORK_WITHIN_REACH.md#live-evidence",
            toc=toc,
        )
        self.assertTrue(d.ok)

    def test_invented_address_fails(self) -> None:
        toc = extract_toc(markdown=SAMPLE, source="docs/AGENT_WORK_WITHIN_REACH.md")
        d = evaluate_grounding(cited="docs/AGENT_WORK_WITHIN_REACH.md#made-up", toc=toc)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_hallucinated_address")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_chunks(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "more-length-chunks",
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
        d = require_stair_controls(
            has_toc=False,
            has_chunking=False,
            has_retrieve=False,
            has_grounding=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")

    def test_all_inputs_pass(self) -> None:
        d = require_stair_controls(
            has_toc=True,
            has_chunking=True,
            has_retrieve=True,
            has_grounding=True,
        )
        self.assertTrue(d.ok)


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "stair_toc.py")],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["completeness"]["ok"])

    def test_complete_cli_exits_zero(self) -> None:
        markdown = REPO / "docs" / "AGENT_WORK_WITHIN_REACH.md"
        self.assertTrue(markdown.is_file())
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "stair_toc.py"),
                "--source",
                "docs/AGENT_WORK_WITHIN_REACH.md",
                "--markdown-file",
                str(markdown),
                "--mode",
                "toc",
                "--query",
                "live evidence WQTU",
                "--cite",
                "docs/AGENT_WORK_WITHIN_REACH.md#live-evidence",
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
