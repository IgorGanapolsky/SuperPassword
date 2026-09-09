"""Dataiku collection steal: owned catalog + 3-question skip. Fail closed."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.use_case_collection import (
    evaluate_agent_need,
    evaluate_claim,
    evaluate_family,
    evaluate_source,
    pick_owned,
    rank_work,
    require_collection_controls,
)


REPO = Path(__file__).resolve().parents[2]

IAP_CASE = {
    "id": "iap-attempt-path",
    "family": "iap_attempt",
    "owned": True,
}
DEMO_CASE = {
    "id": "dataiku-predictive-maintenance",
    "family": "expertise",
    "owned": False,
}


class SourceTests(unittest.TestCase):
    def test_local_catalog_passes(self) -> None:
        d = evaluate_source(source="local_catalog")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_catalog")

    def test_dataiku_fails(self) -> None:
        d = evaluate_source(source="dataiku")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_gated_pdf")

    def test_content_host_fails(self) -> None:
        d = evaluate_source(source="content.dataiku.com")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_gated_pdf")


class FamilyTests(unittest.TestCase):
    def test_iap_family_passes(self) -> None:
        d = evaluate_family(family="iap_attempt")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_owned_family")

    def test_expertise_family_fails(self) -> None:
        d = evaluate_family(family="expertise")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_collection_family")

    def test_clinical_trial_fails(self) -> None:
        d = evaluate_family(family="clinical_trial")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_collection_family")


class AgentNeedTests(unittest.TestCase):
    def test_simple_path_skips_agent(self) -> None:
        d = evaluate_agent_need(
            complexity="simple_if_then",
            data="single_clean",
            process="static",
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "skip_agent")

    def test_agent_worthy_claim_fails(self) -> None:
        d = evaluate_agent_need(
            complexity="reasoning",
            data="multi_source",
            process="adaptive",
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_agent_theater")


class CatalogTests(unittest.TestCase):
    def test_picks_owned_iap_case(self) -> None:
        d = pick_owned(cases=[DEMO_CASE, IAP_CASE], family="iap_attempt")
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("case:iap-attempt-path",))

    def test_collection_only_fails(self) -> None:
        d = pick_owned(cases=[DEMO_CASE], family="iap_attempt")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_catalog")


class ClaimTests(unittest.TestCase):
    def test_cite_owned_case_passes(self) -> None:
        d = evaluate_claim(cite="case:iap-attempt-path", addresses=["case:iap-attempt-path"])
        self.assertTrue(d.ok)

    def test_invented_collection_cite_fails(self) -> None:
        d = evaluate_claim(
            cite="case:clinical-trial-agent",
            addresses=["case:iap-attempt-path"],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_catalog")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_agents(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "more-collection-agents",
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
        d = require_collection_controls(
            has_source=False,
            has_family=False,
            has_need=False,
            has_cases=False,
            has_cite=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "use_case_collection.py")],
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
                str(REPO / "scripts" / "use_case_collection.py"),
                "--source",
                "local_catalog",
                "--family",
                "iap_attempt",
                "--complexity",
                "simple_if_then",
                "--data",
                "single_clean",
                "--process",
                "static",
                "--cases",
                "scripts/tests/fixtures/use_case_collection.json",
                "--cite",
                "case:iap-attempt-path",
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
