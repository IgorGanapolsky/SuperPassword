"""Meko steal: local datapack + decision traces. Fail closed. No mekodata cloud."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_datapack import (
    evaluate_claim,
    evaluate_layer,
    evaluate_platform,
    evaluate_promote,
    evaluate_recall,
    pick_pack,
    rank_work,
    require_datapack_controls,
)


REPO = Path(__file__).resolve().parents[2]

IAP_PACK = {
    "id": "iap-attempt-path",
    "layer": "knowledge",
    "storage": "local_json",
    "promoted": True,
    "verified": True,
}
MEKO_CLOUD = {
    "id": "meko-collective-memory",
    "layer": "memory",
    "storage": "mcp_mekodata_ai",
    "promoted": False,
    "verified": False,
}


class PlatformTests(unittest.TestCase):
    def test_local_datapack_passes(self) -> None:
        d = evaluate_platform(platform="local_datapack")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_datapack")

    def test_meko_cloud_fails(self) -> None:
        d = evaluate_platform(platform="meko_cloud")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_meko_cloud")

    def test_mcp_mekodata_fails(self) -> None:
        d = evaluate_platform(platform="mcp_mekodata_ai")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_meko_cloud")


class LayerTests(unittest.TestCase):
    def test_local_knowledge_passes(self) -> None:
        d = evaluate_layer(layer="knowledge", storage="local_json")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_layer")

    def test_remote_mcp_memory_fails(self) -> None:
        d = evaluate_layer(layer="memory", storage="mcp_mekodata_ai")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_remote_layer")


class PromoteTests(unittest.TestCase):
    def test_verified_knowledge_passes(self) -> None:
        d = evaluate_promote(promoted=True, verified=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_promote_verified")

    def test_unverified_memory_fails(self) -> None:
        d = evaluate_promote(promoted=True, verified=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_promote_unverified")


class RecallTests(unittest.TestCase):
    def test_local_recall_before_reprocess_passes(self) -> None:
        d = evaluate_recall(queried_local=True, reprocess_frontier=False)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_recall")

    def test_reprocess_without_local_query_fails(self) -> None:
        d = evaluate_recall(queried_local=False, reprocess_frontier=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_reprocess_without_recall")


class PickTests(unittest.TestCase):
    def test_picks_iap_local_pack(self) -> None:
        d = pick_pack(packs=[MEKO_CLOUD, IAP_PACK])
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("pack:iap-attempt-path",))

    def test_only_meko_cloud_fails(self) -> None:
        d = pick_pack(packs=[MEKO_CLOUD])
        self.assertFalse(d.ok)


class RankTests(unittest.TestCase):
    def test_iap_beats_token_savings_proxy(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "meko-15x-tokens",
                    "metric": "tokens",
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
        d = require_datapack_controls(
            has_platform=True, has_packs=False, has_cite=True
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliTests(unittest.TestCase):
    def test_cli_allows_local_pack(self) -> None:
        fixture = REPO / "scripts/tests/fixtures/agent_datapack.json"
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/agent_datapack.py"),
                "--platform",
                "local_datapack",
                "--packs",
                str(fixture),
                "--cite",
                "pack:iap-attempt-path",
                "--queried-local",
                "1",
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

    def test_cli_blocks_meko_cloud(self) -> None:
        fixture = REPO / "scripts/tests/fixtures/agent_datapack.json"
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/agent_datapack.py"),
                "--platform",
                "meko_cloud",
                "--packs",
                str(fixture),
                "--cite",
                "pack:iap-attempt-path",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
