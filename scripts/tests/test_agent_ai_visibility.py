"""Semrush AI Visibility Index steal: mentions vs citations. Fail closed."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_ai_visibility import (
    brand_appears_subject_first,
    evaluate_brand_consistency,
    evaluate_citation_core,
    evaluate_claim,
    evaluate_mention_citation_split,
    evaluate_platform,
    evaluate_platform_split_tracking,
    evaluate_structured_summary,
    evaluate_third_party_narrative,
    evaluate_universal_36_ambition,
    pick_pack,
    rank_work,
    require_ai_visibility_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_ai_visibility.json"


class PlatformTests(unittest.TestCase):
    def test_local_passes(self) -> None:
        d = evaluate_platform(platform="manual_prompt_pack")
        self.assertTrue(d.ok)

    def test_semrush_aio_fails(self) -> None:
        d = evaluate_platform(platform="semrush_enterprise_aio")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_aio")


class MentionCitationTests(unittest.TestCase):
    def test_split_passes(self) -> None:
        d = evaluate_mention_citation_split(
            tracks_mentions=True,
            tracks_citations=True,
            conflates_metrics=False,
        )
        self.assertTrue(d.ok)

    def test_conflated_fails(self) -> None:
        d = evaluate_mention_citation_split(
            tracks_mentions=True,
            tracks_citations=False,
            conflates_metrics=True,
        )
        self.assertFalse(d.ok)


class BrandTests(unittest.TestCase):
    def test_subject_first_passes(self) -> None:
        d = evaluate_brand_consistency(
            canonical_name_used=True,
            subject_first=True,
            pronoun_only=False,
        )
        self.assertTrue(d.ok)

    def test_pronoun_only_fails(self) -> None:
        d = evaluate_brand_consistency(
            canonical_name_used=False,
            subject_first=False,
            pronoun_only=True,
        )
        self.assertFalse(d.ok)

    def test_helper_detects_subject_first(self) -> None:
        self.assertTrue(
            brand_appears_subject_first(
                text="Random Tactical Timer is a random interval timer for boxing."
            )
        )
        self.assertFalse(
            brand_appears_subject_first(text="I built an app for boxing drills.")
        )


class CitationCoreTests(unittest.TestCase):
    def test_reddit_owned_passes(self) -> None:
        d = evaluate_citation_core(surfaces=("reddit", "owned_site", "play_store"))
        self.assertTrue(d.ok)

    def test_random_blog_only_fails(self) -> None:
        d = evaluate_citation_core(surfaces=("obscure_forum",))
        self.assertFalse(d.ok)


class ThirdPartyTests(unittest.TestCase):
    def test_third_party_passes(self) -> None:
        d = evaluate_third_party_narrative(third_party_named=True, owned_only=False)
        self.assertTrue(d.ok)

    def test_owned_only_fails(self) -> None:
        d = evaluate_third_party_narrative(third_party_named=False, owned_only=True)
        self.assertFalse(d.ok)


class StructuredTests(unittest.TestCase):
    def test_summary_and_faq_pass(self) -> None:
        d = evaluate_structured_summary(has_structured_summary=True, has_faq_block=True)
        self.assertTrue(d.ok)

    def test_missing_faq_fails(self) -> None:
        d = evaluate_structured_summary(
            has_structured_summary=True, has_faq_block=False
        )
        self.assertFalse(d.ok)


class PlatformSplitTests(unittest.TestCase):
    def test_split_passes(self) -> None:
        d = evaluate_platform_split_tracking(
            tracks_per_platform=True, single_score_only=False
        )
        self.assertTrue(d.ok)

    def test_single_score_fails(self) -> None:
        d = evaluate_platform_split_tracking(
            tracks_per_platform=False, single_score_only=True
        )
        self.assertFalse(d.ok)


class AmbitionTests(unittest.TestCase):
    def test_category_focus_passes(self) -> None:
        d = evaluate_universal_36_ambition(chasing_universal_36=False)
        self.assertTrue(d.ok)

    def test_universal_36_fails(self) -> None:
        d = evaluate_universal_36_ambition(chasing_universal_36=True)
        self.assertFalse(d.ok)


class RankTests(unittest.TestCase):
    def test_citation_pack_beats_semrush_proxy(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "semrush-tool",
                    "metric": "semrush_aio_score",
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "owned-faq",
                    "metric": "owned_citation",
                    "expected_citations": 2,
                    "expected_iap_attempts": 1,
                    "effort": 1,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "owned-faq")
        self.assertEqual(ranked[1]["score"], 0.0)


class PickClaimTests(unittest.TestCase):
    def test_picks_local_pack(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        d = pick_pack(packs=payload["packs"])
        self.assertTrue(d.ok)
        self.assertIn("aiv:category-prompt-pack", d.addresses)

    def test_cite_must_match(self) -> None:
        d = evaluate_claim(
            cite="aiv:category-prompt-pack",
            addresses=("aiv:category-prompt-pack",),
        )
        self.assertTrue(d.ok)


class CompletenessTests(unittest.TestCase):
    def test_incomplete_fails(self) -> None:
        d = require_ai_visibility_controls(
            has_platform=True, has_packs=False, has_cite=True
        )
        self.assertFalse(d.ok)


class CliTests(unittest.TestCase):
    def test_cli_allows_local_pack(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_ai_visibility.py"),
            "--platform",
            "manual_prompt_pack",
            "--packs",
            str(FIXTURE),
            "--cite",
            "aiv:category-prompt-pack",
            "--tracks-mentions",
            "1",
            "--tracks-citations",
            "1",
            "--canonical-name-used",
            "1",
            "--subject-first",
            "1",
            "--surfaces",
            "reddit,owned_site,play_store,app_store",
            "--third-party-named",
            "1",
            "--has-structured-summary",
            "1",
            "--has-faq-block",
            "1",
            "--tracks-per-platform",
            "1",
            "--chasing-universal-36",
            "0",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_cli_blocks_semrush(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_ai_visibility.py"),
            "--platform",
            "semrush_aio",
            "--packs",
            str(FIXTURE),
            "--cite",
            "aiv:category-prompt-pack",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["platform"]["ok"])


if __name__ == "__main__":
    unittest.main()
