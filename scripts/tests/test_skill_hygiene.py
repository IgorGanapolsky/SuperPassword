"""pvncher/Astra steal: skill + prompt hygiene. Fail closed. No GPT-6 Astra."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.skill_hygiene import (
    evaluate_always_on,
    evaluate_claim,
    evaluate_completion,
    evaluate_description,
    evaluate_disclosure,
    evaluate_platform,
    pick_hygiene,
    rank_work,
    require_hygiene_controls,
)


REPO = Path(__file__).resolve().parents[2]

SHORT_SKILL = {
    "id": "iap-attempt-path",
    "description": "Use when diagnosing zero IAP attempts on the paywall.",
    "disclosure": "router",
    "always_on_bloat": False,
    "completion_defined": True,
}
BLOATED_SKILL = {
    "id": "pick-me-database-everything",
    "description": (
        "Use for any database work, migrations, schema changes, queries, indexes, "
        "ORMs, backups, and anything remotely related to data storage or SQL."
    ),
    "disclosure": "itinerary",
    "always_on_bloat": True,
    "completion_defined": False,
}


class PlatformTests(unittest.TestCase):
    def test_local_hygiene_passes(self) -> None:
        d = evaluate_platform(platform="local_hygiene")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_hygiene")

    def test_gpt6_astra_fails(self) -> None:
        d = evaluate_platform(platform="gpt6_astra")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")

    def test_openai_primary_fails(self) -> None:
        d = evaluate_platform(platform="openai_primary")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")


class DescriptionTests(unittest.TestCase):
    def test_short_trigger_passes(self) -> None:
        d = evaluate_description(description=SHORT_SKILL["description"])
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_short_description")

    def test_pick_me_long_description_fails(self) -> None:
        d = evaluate_description(description=BLOATED_SKILL["description"])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_bloated_description")


class DisclosureTests(unittest.TestCase):
    def test_router_passes(self) -> None:
        d = evaluate_disclosure(disclosure="router")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_progressive_disclosure")

    def test_itinerary_fails(self) -> None:
        d = evaluate_disclosure(disclosure="itinerary")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_over_specific")


class AlwaysOnTests(unittest.TestCase):
    def test_lean_always_on_passes(self) -> None:
        d = evaluate_always_on(bloat=False)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_lean_always_on")

    def test_repo_map_every_edit_fails(self) -> None:
        d = evaluate_always_on(bloat=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_always_on_bloat")


class CompletionTests(unittest.TestCase):
    def test_defined_completion_passes(self) -> None:
        d = evaluate_completion(defined=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_defined_completion")

    def test_stop_after_first_impl_fails(self) -> None:
        d = evaluate_completion(defined=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_early_stop")


class PickTests(unittest.TestCase):
    def test_picks_hygienic_skill(self) -> None:
        d = pick_hygiene(skills=[BLOATED_SKILL, SHORT_SKILL])
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("skill:iap-attempt-path",))

    def test_only_bloated_fails(self) -> None:
        d = pick_hygiene(skills=[BLOATED_SKILL])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_no_hygienic_skill")


class ClaimTests(unittest.TestCase):
    def test_cite_picked_passes(self) -> None:
        d = evaluate_claim(cite="skill:iap-attempt-path", addresses=["skill:iap-attempt-path"])
        self.assertTrue(d.ok)

    def test_invented_cite_fails(self) -> None:
        d = evaluate_claim(cite="skill:astra-audit", addresses=["skill:iap-attempt-path"])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_hygiene")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_skills(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "download-more-skills",
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
        d = require_hygiene_controls(
            has_platform=False,
            has_skills=False,
            has_cite=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "skill_hygiene.py")],
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
                str(REPO / "scripts" / "skill_hygiene.py"),
                "--platform",
                "local_hygiene",
                "--skills",
                "scripts/tests/fixtures/skill_hygiene.json",
                "--cite",
                "skill:iap-attempt-path",
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
