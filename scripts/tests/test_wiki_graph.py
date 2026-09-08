"""Karpathy/Neo4j wiki-graph steal: navigate links. Fail closed. No Aura."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.wiki_graph import (
    build_graph,
    evaluate_index,
    evaluate_walk,
    navigate,
    rank_work,
    require_wiki_controls,
)


REPO = Path(__file__).resolve().parents[2]

HUB = """# Token shunt

See the [live evidence](AGENT_STAIR_TOC.md#live-evidence) and [[AGENT_STAIR_TOC]].

## Hook rewrite
Untargeted reads get sliced.
"""

SPOKE = """# STAIR ToC

## Live evidence (project 299775)
WQTU is 3 in the trailing week.
"""


class IndexModeTests(unittest.TestCase):
    def test_local_graph_passes(self) -> None:
        d = evaluate_index(engine="local_graph")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_graph")

    def test_vector_only_fails(self) -> None:
        d = evaluate_index(engine="vector_only")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_vector_only")

    def test_aura_fails(self) -> None:
        d = evaluate_index(engine="neo4j_aura")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")


class GraphBuildTests(unittest.TestCase):
    def test_markdown_and_wiki_links_become_edges(self) -> None:
        graph = build_graph(
            pages=[
                {"path": "docs/AGENT_TOKEN_SHUNT.md", "markdown": HUB},
                {"path": "docs/AGENT_STAIR_TOC.md", "markdown": SPOKE},
            ]
        )
        targets = {edge["target"] for edge in graph["edges"] if edge["kind"] == "LINKS_TO"}
        self.assertIn("docs/AGENT_STAIR_TOC.md#live-evidence", targets)
        self.assertIn("docs/AGENT_STAIR_TOC.md", targets)


class NavigateTests(unittest.TestCase):
    def test_walk_reaches_linked_spoke(self) -> None:
        graph = build_graph(
            pages=[
                {"path": "docs/AGENT_TOKEN_SHUNT.md", "markdown": HUB},
                {"path": "docs/AGENT_STAIR_TOC.md", "markdown": SPOKE},
            ]
        )
        d = navigate(query="token shunt evidence", graph=graph, max_hops=2)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_walk")
        self.assertIn("docs/AGENT_STAIR_TOC.md#live-evidence", d.addresses)

    def test_vector_dump_without_links_fails(self) -> None:
        graph = build_graph(pages=[{"path": "docs/orphan.md", "markdown": "# Orphan\nno links\n"}])
        d = navigate(query="token shunt evidence", graph=graph, max_hops=2)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_no_walk")


class WalkGroundingTests(unittest.TestCase):
    def test_cite_on_walk_passes(self) -> None:
        d = evaluate_walk(
            cite="docs/AGENT_STAIR_TOC.md#live-evidence",
            addresses=["docs/AGENT_TOKEN_SHUNT.md", "docs/AGENT_STAIR_TOC.md#live-evidence"],
        )
        self.assertTrue(d.ok)

    def test_invented_cite_fails(self) -> None:
        d = evaluate_walk(
            cite="docs/missing.md#hallucination",
            addresses=["docs/AGENT_STAIR_TOC.md#live-evidence"],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_graph")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_graph_hops(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "more-neo4j-hops",
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
        d = require_wiki_controls(has_index=False, has_walk=False, has_cite=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "wiki_graph.py")],
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
                str(REPO / "scripts" / "wiki_graph.py"),
                "--engine",
                "local_graph",
                "--pages",
                "docs/AGENT_TOKEN_SHUNT.md,docs/AGENT_STAIR_TOC.md",
                "--query",
                "token shunt live evidence WQTU",
                "--cite",
                "docs/AGENT_TOKEN_SHUNT.md#live-evidence",
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
