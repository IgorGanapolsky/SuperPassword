"""TDD: intelligent ROSE-lite intent routing, scoring, and briefs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_rose_lite.intent import (  # noqa: E402
    IntentDecision,
    classify_intent,
    rank_cells,
    render_brief,
    should_reuse_prior,
    synthesize_query,
)


class ClassifyIntentTests(unittest.TestCase):
    def test_debug_beats_generic_when_crash_language_present(self) -> None:
        d = classify_intent("CI failed: Robolectric crash on targetSdk 36")
        self.assertEqual(d.intent, "debug")
        self.assertEqual(d.scene, "debugging")
        self.assertGreater(d.confidence, 0.4)

    def test_ship_intent_from_store_language(self) -> None:
        d = classify_intent("submit Play production listing and TestFlight")
        self.assertEqual(d.intent, "ship")
        self.assertEqual(d.scene, "store-publishing")

    def test_monetize_intent_from_paywall_language(self) -> None:
        d = classify_intent("paywall attempt to success is zero WQTU")
        self.assertEqual(d.intent, "monetize")

    def test_empty_query_is_general_with_low_confidence(self) -> None:
        d = classify_intent("")
        self.assertEqual(d.intent, "general")
        self.assertLess(d.confidence, 0.4)


class SynthesizeQueryTests(unittest.TestCase):
    def test_keeps_signal_tokens_and_drops_stopwords(self) -> None:
        q = synthesize_query("Please make it more intelligent and fix the Robolectric JDK crash")
        self.assertIn("robolectric", q.lower())
        self.assertIn("jdk", q.lower())
        self.assertNotIn("please", q.lower())

    def test_merges_branch_hint_when_prompt_is_thin(self) -> None:
        q = synthesize_query("make it", branch_hint="feat play api36 robolectric")
        self.assertIn("api36", q.lower())
        self.assertIn("robolectric", q.lower())


class RankCellsTests(unittest.TestCase):
    def _cells(self) -> list[dict]:
        return [
            {
                "id": "risk_sdk",
                "scene": "debugging",
                "cell_type": "risk",
                "salience": 0.4,
                "content": "Play targetSdk 36 needs Robolectric 4.16 and JDK 21",
                "evidence_count": 4,
                "last_seen": "2026-09-07T00:00:00Z",
            },
            {
                "id": "ui_old",
                "scene": "animation-parity",
                "cell_type": "fact",
                "salience": 0.95,
                "content": "iOS cosine period equals full cycle time",
                "evidence_count": 1,
                "last_seen": "2026-01-01T00:00:00Z",
            },
            {
                "id": "cream",
                "scene": "general",
                "cell_type": "preference",
                "salience": 0.9,
                "content": "Prefer cream backgrounds for marketing pages",
                "evidence_count": 1,
                "last_seen": "2026-09-01T00:00:00Z",
            },
        ]

    def test_debug_intent_ranks_risk_over_high_salience_unrelated(self) -> None:
        decision = IntentDecision(
            intent="debug", scene="debugging", confidence=0.8, query="Robolectric JDK crash"
        )
        ranked = rank_cells(self._cells(), decision, now_iso="2026-09-07T12:00:00Z")
        self.assertEqual(ranked[0]["id"], "risk_sdk")
        self.assertGreater(ranked[0]["score"], ranked[1]["score"])

    def test_low_top_score_marks_not_verified(self) -> None:
        decision = IntentDecision(
            intent="general", scene=None, confidence=0.1, query="unrelated xyzzy"
        )
        cells = [
            {
                "id": "noise",
                "scene": "general",
                "cell_type": "fact",
                "salience": 0.2,
                "content": "cream background",
                "evidence_count": 1,
                "last_seen": "2026-01-01T00:00:00Z",
            }
        ]
        ranked = rank_cells(cells, decision, now_iso="2026-09-07T12:00:00Z")
        brief = render_brief(decision, ranked)
        self.assertIn("not verified", brief.lower())
        self.assertLessEqual(len(ranked), 2)


class BriefAndReuseTests(unittest.TestCase):
    def test_brief_names_intent_and_next_action(self) -> None:
        decision = IntentDecision(
            intent="debug", scene="debugging", confidence=0.7, query="sdk crash"
        )
        ranked = [
            {
                "id": "risk_sdk",
                "scene": "debugging",
                "cell_type": "risk",
                "salience": 0.6,
                "content": "JDK 21 required for targetSdk 36",
                "score": 0.81,
                "evidence_count": 3,
            }
        ]
        brief = render_brief(decision, ranked)
        self.assertIn("intent=debug", brief)
        self.assertIn("JDK 21", brief)
        self.assertIn("next:", brief.lower())

    def test_reuse_prior_when_query_is_near_duplicate(self) -> None:
        prior = {"query": "Fix Play targetSdk 36 Robolectric failures", "context": "old"}
        self.assertTrue(
            should_reuse_prior(prior, "fix play targetsdk 36 robolectric failures")
        )
        self.assertFalse(should_reuse_prior(prior, "iOS TestFlight metadata keywords"))
