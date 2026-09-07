#!/usr/bin/env python3
"""Tests for the Self-Organizing Agent Memory System."""

import json
import tempfile
import unittest
from pathlib import Path

from memory_manager import (
    MemoryManager,
    classify_cell_type,
    classify_scene,
    compress_content,
    extract_text,
    word_overlap,
)


class TestClassifyScene(unittest.TestCase):
    def test_store_publishing(self):
        self.assertEqual(classify_scene("publish to Google Play Store"), "store-publishing")

    def test_testing(self):
        self.assertEqual(classify_scene("run the Maestro tests"), "testing")

    def test_git(self):
        self.assertEqual(classify_scene("commit and push to branch"), "git-operations")

    def test_debugging(self):
        self.assertEqual(classify_scene("debug the crash in stack trace"), "debugging")

    def test_animation(self):
        self.assertEqual(classify_scene("shimmer animation parity circle"), "animation-parity")

    def test_general_fallback(self):
        self.assertEqual(classify_scene("hello world"), "general")

    def test_credentials(self):
        self.assertEqual(classify_scene("password and 2fa token"), "credentials")


class TestClassifyCellType(unittest.TestCase):
    def test_risk_on_lying(self):
        self.assertEqual(classify_cell_type("you are lying", is_negative=True), "risk")

    def test_risk_on_false_claim(self):
        self.assertEqual(classify_cell_type("false claim without verification", is_negative=True), "risk")

    def test_risk_default_for_negative(self):
        self.assertEqual(classify_cell_type("something went bad", is_negative=True), "risk")

    def test_pattern_type(self):
        self.assertEqual(classify_cell_type("this pattern keeps repeating", is_negative=False), "pattern")

    def test_decision_type(self):
        self.assertEqual(classify_cell_type("we decided on this approach", is_negative=False), "decision")

    def test_preference_type(self):
        self.assertEqual(classify_cell_type("user wants this mandate", is_negative=False), "preference")

    def test_fact_default_for_positive(self):
        self.assertEqual(classify_cell_type("works great today", is_negative=False), "fact")


class TestWordOverlap(unittest.TestCase):
    def test_identical(self):
        self.assertAlmostEqual(word_overlap("hello world foo", "hello world foo"), 1.0)

    def test_disjoint(self):
        self.assertEqual(word_overlap("apple banana cherry", "dog elephant frog"), 0.0)

    def test_partial(self):
        score = word_overlap("publish store google play", "publish app store console")
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_empty(self):
        self.assertEqual(word_overlap("", "hello world"), 0.0)

    def test_short_words_ignored(self):
        self.assertEqual(word_overlap("a b c", "a b c"), 0.0)


class TestExtractText(unittest.TestCase):
    def test_context_field(self):
        entry = {"context": "publish failed"}
        self.assertIn("publish failed", extract_text(entry))

    def test_user_message_field(self):
        entry = {"user_message": "thumbs down"}
        self.assertIn("thumbs down", extract_text(entry))

    def test_multiple_fields(self):
        entry = {"context": "store error", "user_message": "fix it"}
        text = extract_text(entry)
        self.assertIn("store error", text)
        self.assertIn("fix it", text)

    def test_truncation(self):
        entry = {"context": "x" * 500}
        self.assertLessEqual(len(extract_text(entry)), 400)


class TestCompressContent(unittest.TestCase):
    def test_strips_urls(self):
        result = compress_content("check https://example.com/foo please")
        self.assertNotIn("https://", result)

    def test_strips_json_blobs(self):
        result = compress_content("data {key: value} here")
        self.assertNotIn("key", result)

    def test_max_length(self):
        result = compress_content("x" * 500)
        self.assertLessEqual(len(result), 200)


class TestMemoryManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.memory_dir = Path(self.tmpdir)
        (self.memory_dir / "feedback").mkdir(parents=True)
        self.mgr = MemoryManager(self.memory_dir)

    def test_empty_load(self):
        self.assertEqual(self.mgr.load_cells(), [])

    def test_ingest_creates_cell(self):
        entry = {
            "timestamp": "2026-02-05T18:37:12Z",
            "feedback": "negative",
            "reward": -1,
            "context": "publish to Google Play Store failed",
            "id": "fb_1",
        }
        cell = self.mgr.ingest(entry)
        self.assertEqual(cell["scene"], "store-publishing")
        self.assertEqual(cell["cell_type"], "risk")
        self.assertGreater(cell["salience"], 0)
        self.assertEqual(cell["evidence_count"], 1)
        self.assertEqual(self.mgr.load_cells(), [cell])

    def test_ingest_consolidates_similar(self):
        e1 = {"feedback": "negative", "reward": -1, "context": "publish Google Play Store failed", "id": "fb_1"}
        e2 = {"feedback": "negative", "reward": -1, "context": "publish Google Play Store error again", "id": "fb_2"}
        self.mgr.ingest(e1)
        self.mgr.ingest(e2)
        cells = self.mgr.load_cells()
        self.assertEqual(len(cells), 1)
        self.assertEqual(cells[0]["evidence_count"], 2)
        self.assertIn("fb_1", cells[0]["source_ids"])
        self.assertIn("fb_2", cells[0]["source_ids"])

    def test_ingest_creates_separate_cells_for_different_scenes(self):
        e1 = {"feedback": "negative", "context": "publish to store", "id": "1"}
        e2 = {"feedback": "negative", "context": "run the tests failed", "id": "2"}
        self.mgr.ingest(e1)
        self.mgr.ingest(e2)
        cells = self.mgr.load_cells()
        self.assertEqual(len(cells), 2)
        scenes = {c["scene"] for c in cells}
        self.assertIn("store-publishing", scenes)
        self.assertIn("testing", scenes)

    def test_recall_returns_all_by_default(self):
        self.mgr.ingest({"feedback": "negative", "context": "publish store error", "id": "1"})
        self.mgr.ingest({"feedback": "negative", "context": "test failed badly", "id": "2"})
        cells = self.mgr.recall()
        self.assertEqual(len(cells), 2)

    def test_recall_filters_by_scene(self):
        self.mgr.ingest({"feedback": "negative", "context": "publish store error", "id": "1"})
        self.mgr.ingest({"feedback": "negative", "context": "test failed badly", "id": "2"})
        cells = self.mgr.recall(scene="store-publishing")
        self.assertEqual(len(cells), 1)
        self.assertEqual(cells[0]["scene"], "store-publishing")

    def test_recall_filters_by_salience(self):
        self.mgr.ingest({"feedback": "positive", "reward": 0.5, "context": "minor positive thing", "id": "1"})
        cells = self.mgr.recall(min_salience=0.9)
        self.assertEqual(len(cells), 0)

    def test_recall_sorted_by_salience(self):
        self.mgr.ingest({"feedback": "negative", "intensity": 2, "context": "low priority publish store listing", "id": "1"})
        self.mgr.ingest({"feedback": "negative", "intensity": 5, "context": "critical crash debug stack trace investigate", "id": "2"})
        cells = self.mgr.recall()
        self.assertEqual(len(cells), 2)
        self.assertGreaterEqual(cells[0]["salience"], cells[1]["salience"])

    def test_recall_respects_limit(self):
        for i in range(20):
            self.mgr.ingest({"feedback": "negative", "context": f"unique_error_{i} crash debug investigate", "id": str(i)})
        cells = self.mgr.recall(limit=5)
        self.assertLessEqual(len(cells), 5)

    def test_decay_reduces_salience(self):
        self.mgr.ingest({"feedback": "negative", "context": "old error crash debug", "id": "1"})
        cells = self.mgr.load_cells()
        original = cells[0]["salience"]
        from datetime import datetime, timezone, timedelta
        cells[0]["last_seen"] = (datetime.now(tz=timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.mgr.save_cells(cells)
        self.mgr.decay(half_life_days=14.0)
        cells = self.mgr.load_cells()
        self.assertLess(cells[0]["salience"], original)

    def test_decay_prunes_very_old(self):
        self.mgr.ingest({"feedback": "negative", "context": "ancient error debug crash", "id": "1"})
        cells = self.mgr.load_cells()
        cells[0]["last_seen"] = "2020-01-01T00:00:00Z"
        cells[0]["salience"] = 0.1
        self.mgr.save_cells(cells)
        pruned = self.mgr.decay(half_life_days=14.0)
        self.assertEqual(pruned, 1)
        self.assertEqual(len(self.mgr.load_cells()), 0)

    def test_consolidate_merges_similar(self):
        cells = [
            {
                "id": "c1", "scene": "testing", "cell_type": "risk", "salience": 0.5,
                "content": "test failed on android device emulator",
                "evidence_count": 1, "first_seen": "2026-02-01", "last_seen": "2026-02-01",
                "source_ids": ["1"],
            },
            {
                "id": "c2", "scene": "testing", "cell_type": "risk", "salience": 0.4,
                "content": "test failed on android emulator device run",
                "evidence_count": 1, "first_seen": "2026-02-02", "last_seen": "2026-02-02",
                "source_ids": ["2"],
            },
        ]
        self.mgr.save_cells(cells)
        merged = self.mgr.consolidate()
        self.assertEqual(merged, 1)
        result = self.mgr.load_cells()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["evidence_count"], 2)

    def test_consolidate_keeps_different_scenes(self):
        cells = [
            {
                "id": "c1", "scene": "testing", "cell_type": "risk", "salience": 0.5,
                "content": "error on device", "evidence_count": 1,
                "first_seen": "2026-02-01", "last_seen": "2026-02-01", "source_ids": ["1"],
            },
            {
                "id": "c2", "scene": "debugging", "cell_type": "risk", "salience": 0.5,
                "content": "error on device", "evidence_count": 1,
                "first_seen": "2026-02-02", "last_seen": "2026-02-02", "source_ids": ["2"],
            },
        ]
        self.mgr.save_cells(cells)
        merged = self.mgr.consolidate()
        self.assertEqual(merged, 0)
        self.assertEqual(len(self.mgr.load_cells()), 2)

    def test_seed_from_lessons(self):
        lessons = self.memory_dir / "lessons-learned.md"
        lessons.write_text(
            "# Lessons\n\n"
            "## CRITICAL - Publishing Failures\n"
            "Never claim publish success without verification.\n\n"
            "## Pattern: False Claims\n"
            "Lying is not allowed. Always verify.\n"
        )
        count = self.mgr.seed_from_lessons(lessons)
        self.assertEqual(count, 2)
        cells = self.mgr.load_cells()
        self.assertEqual(len(cells), 2)
        critical_cells = [c for c in cells if c["salience"] >= 0.8]
        self.assertGreaterEqual(len(critical_cells), 1)

    def test_seed_missing_file(self):
        count = self.mgr.seed_from_lessons(self.memory_dir / "nonexistent.md")
        self.assertEqual(count, 0)

    def test_round_trip_persistence(self):
        entry = {"feedback": "negative", "context": "store publish fail error", "id": "rt_1"}
        self.mgr.ingest(entry)
        mgr2 = MemoryManager(self.memory_dir)
        cells = mgr2.load_cells()
        self.assertEqual(len(cells), 1)
        self.assertEqual(cells[0]["scene"], "store-publishing")

    def test_ingest_all_unprocessed(self):
        log = self.memory_dir / "feedback" / "feedback-log.jsonl"
        entries = [
            {"timestamp": "2026-02-05T18:00:00Z", "feedback": "negative", "context": "store publish fail", "id": "a"},
            {"timestamp": "2026-02-05T19:00:00Z", "feedback": "positive", "context": "test passed great", "id": "b"},
        ]
        with open(log, "w") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        count = self.mgr.ingest_all_unprocessed()
        self.assertEqual(count, 2)
        count2 = self.mgr.ingest_all_unprocessed()
        self.assertEqual(count2, 0)

    def test_stats(self):
        self.mgr.ingest({"feedback": "negative", "context": "publish store error", "id": "1"})
        self.mgr.ingest({"feedback": "negative", "context": "test failed check", "id": "2"})
        s = self.mgr.stats()
        self.assertEqual(s["total_cells"], 2)
        self.assertIn("store-publishing", s["by_scene"])
        self.assertIn("testing", s["by_scene"])

    def test_atomic_save(self):
        self.mgr.ingest({"feedback": "negative", "context": "crash debug error", "id": "1"})
        tmp_file = self.mgr.cells_file.with_suffix(".tmp")
        self.assertFalse(tmp_file.exists())
        self.assertTrue(self.mgr.cells_file.exists())


if __name__ == "__main__":
    unittest.main()
