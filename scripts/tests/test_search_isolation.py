"""ArcticSwarm steal: isolate search before review. Fail closed. No ArcticSwarm."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.search_isolation import (
    evaluate_claim,
    evaluate_consensus,
    evaluate_evidence,
    evaluate_isolation,
    evaluate_platform,
    pick_path,
    rank_work,
    require_isolation_controls,
)


REPO = Path(__file__).resolve().parents[2]

IAP_PATH = {
    "id": "iap-attempt-path",
    "peer_reads_during_search": False,
    "findings": ["paywall_viewed=20", "iap_attempt=0"],
    "reviewed": True,
}
EARLY_CONSENSUS = {
    "id": "more-agents-chat-early",
    "peer_reads_during_search": True,
    "findings": [],
    "reviewed": False,
}


class PlatformTests(unittest.TestCase):
    def test_local_isolation_passes(self) -> None:
        d = evaluate_platform(platform="local_isolation")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_isolation")

    def test_arctic_swarm_fails(self) -> None:
        d = evaluate_platform(platform="arctic_swarm")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")

    def test_more_agents_fails(self) -> None:
        d = evaluate_platform(platform="more_agents")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")


class IsolationTests(unittest.TestCase):
    def test_blocked_peer_reads_pass(self) -> None:
        d = evaluate_isolation(peer_reads_during_search=False)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_isolated_search")

    def test_peer_reads_during_search_fail(self) -> None:
        d = evaluate_isolation(peer_reads_during_search=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_premature_consensus")


class EvidenceTests(unittest.TestCase):
    def test_findings_before_review_pass(self) -> None:
        d = evaluate_evidence(findings=["paywall_viewed=20", "iap_attempt=0"])
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_evidence_ready")

    def test_empty_findings_fail(self) -> None:
        d = evaluate_evidence(findings=[])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_no_evidence")


class ConsensusTests(unittest.TestCase):
    def test_reviewed_after_isolation_passes(self) -> None:
        d = evaluate_consensus(reviewed=True, peer_reads_during_search=False)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_deferred_review")

    def test_agree_without_review_fails(self) -> None:
        d = evaluate_consensus(reviewed=False, peer_reads_during_search=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unreviewed_consensus")


class PickTests(unittest.TestCase):
    def test_picks_isolated_iap_path(self) -> None:
        d = pick_path(paths=[EARLY_CONSENSUS, IAP_PATH])
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("path:iap-attempt-path",))

    def test_only_early_consensus_fails(self) -> None:
        d = pick_path(paths=[EARLY_CONSENSUS])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_no_isolated_path")


class ClaimTests(unittest.TestCase):
    def test_cite_picked_passes(self) -> None:
        d = evaluate_claim(cite="path:iap-attempt-path", addresses=["path:iap-attempt-path"])
        self.assertTrue(d.ok)

    def test_invented_cite_fails(self) -> None:
        d = evaluate_claim(cite="path:arctic-swarm", addresses=["path:iap-attempt-path"])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_isolation")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_agents(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "spawn-more-agents",
                    "metric": "agent_count",
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
        d = require_isolation_controls(
            has_platform=False,
            has_paths=False,
            has_cite=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "search_isolation.py")],
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
                str(REPO / "scripts" / "search_isolation.py"),
                "--platform",
                "local_isolation",
                "--paths",
                "scripts/tests/fixtures/search_isolation.json",
                "--cite",
                "path:iap-attempt-path",
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
