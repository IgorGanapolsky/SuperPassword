"""TDD for Perplexity-inspired ROSE-lite agent embed/recall stack (zero-cost)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "memory"))

from agent_rose_lite.embeddings import (  # noqa: E402
    LazyTensor,
    MatryoshkaEmbedder,
    cosine_similarity,
)
from agent_rose_lite.tulip_batch import TokenBudgetBatcher  # noqa: E402
from agent_rose_lite.day0 import Day0BringupReport, run_day0_bringup  # noqa: E402
from memory_manager import MemoryManager  # noqa: E402


class EmbedderTests(unittest.TestCase):
    def test_matryoshka_truncation_preserves_prefix(self) -> None:
        emb = MatryoshkaEmbedder(dims=(64, 32, 16))
        full = emb.embed("targetSdk 36 requires Robolectric 4.16 and JDK 21")
        mid = emb.embed("targetSdk 36 requires Robolectric 4.16 and JDK 21", dim=32)
        small = emb.embed("targetSdk 36 requires Robolectric 4.16 and JDK 21", dim=16)
        self.assertEqual(len(full), 64)
        self.assertEqual(mid, full[:32])
        self.assertEqual(small, full[:16])

    def test_similar_texts_score_higher_than_unrelated(self) -> None:
        emb = MatryoshkaEmbedder(dims=(64,))
        a = emb.embed("Play Console target API level 36 deadline August 2026")
        b = emb.embed("Google Play requires targetSdkVersion 36 for app updates")
        c = emb.embed("iOS animation timing parity cosine period")
        self.assertGreater(cosine_similarity(a, b), cosine_similarity(a, c))

    def test_lazy_cache_second_hit_reuses_capture(self) -> None:
        emb = MatryoshkaEmbedder(dims=(32,))
        first = emb.embed_lazy("store publishing fastlane deliver")
        self.assertIsInstance(first, LazyTensor)
        self.assertFalse(first.captured)
        v1 = first.resolve()
        self.assertTrue(first.captured)
        second = emb.embed_lazy("store publishing fastlane deliver")
        self.assertTrue(second.captured)
        self.assertEqual(second.resolve(), v1)


class TulipBatcherTests(unittest.TestCase):
    def test_batches_by_token_budget_not_sequence_count(self) -> None:
        batcher = TokenBudgetBatcher(token_budget=20)
        items = [
            ("short", 2),
            ("a bit longer text here", 8),
            ("another chunk of tokens roughly", 7),
            ("tiny", 1),
            ("overflow that must start a new batch because budget is tight", 18),
        ]
        batches = batcher.pack(items)
        self.assertGreaterEqual(len(batches), 2)
        for batch in batches:
            self.assertLessEqual(sum(t for _, t in batch), 20)


class HybridRecallTests(unittest.TestCase):
    def test_query_recall_ranks_semantic_match_above_salience_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mgr = MemoryManager(memory_dir=root)
            cells = [
                {
                    "id": "c_high",
                    "scene": "general",
                    "cell_type": "fact",
                    "salience": 0.95,
                    "content": "Prefer cream backgrounds for marketing pages",
                    "evidence_count": 1,
                    "first_seen": "2026-09-01T00:00:00Z",
                    "last_seen": "2026-09-01T00:00:00Z",
                    "source_ids": ["a"],
                },
                {
                    "id": "c_sdk",
                    "scene": "store-publishing",
                    "cell_type": "risk",
                    "salience": 0.55,
                    "content": "targetSdk 36 blocked by Robolectric maxSdk 35 until 4.16 + JDK 21",
                    "evidence_count": 3,
                    "first_seen": "2026-09-01T00:00:00Z",
                    "last_seen": "2026-09-06T00:00:00Z",
                    "source_ids": ["b"],
                },
            ]
            mgr.save_cells(cells)
            ranked = mgr.recall(query="Android Play API 36 Robolectric JDK", limit=2)
            self.assertEqual(ranked[0]["id"], "c_sdk")


class Day0BringupTests(unittest.TestCase):
    def test_day0_report_includes_stages_and_cost_cap(self) -> None:
        report = run_day0_bringup(
            model_id="gpt-oss-20b",
            probes={"harmony_tokenizer": True, "local_mlx_or_ollama": False, "fp8_or_int4": True},
            monthly_budget_usd=20.0,
        )
        self.assertIsInstance(report, Day0BringupReport)
        self.assertIn("weight_map", report.stages)
        self.assertIn("tp1_smoke", report.stages)
        self.assertTrue(report.within_budget)
        self.assertLessEqual(report.estimated_monthly_usd, 20.0)


if __name__ == "__main__":
    unittest.main()
