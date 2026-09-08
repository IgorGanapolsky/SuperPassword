"""Metabigor steal: owned public surfaces only. Fail closed. No recon binary."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.public_footprint import (
    compose_footprint,
    evaluate_claim,
    evaluate_engine,
    evaluate_target,
    rank_work,
    require_footprint_controls,
)


REPO = Path(__file__).resolve().parents[2]

OWNED_SOURCES = [
    {
        "kind": "play",
        "identity": "com.iganapolsky.randomtimer",
        "status": 200,
        "body": 'id=com.iganapolsky.randomtimer" og:title="Random Tactical Timer"',
    },
    {
        "kind": "itunes",
        "identity": "6758355312",
        "status": 200,
        "result_count": 1,
    },
    {
        "kind": "github",
        "identity": "IgorGanapolsky/Random-Timer",
        "status": 200,
    },
]


class EngineModeTests(unittest.TestCase):
    def test_public_owned_passes(self) -> None:
        d = evaluate_engine(engine="public_owned")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_public_owned")

    def test_metabigor_binary_fails(self) -> None:
        d = evaluate_engine(engine="metabigor")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_recon")

    def test_shodan_fails(self) -> None:
        d = evaluate_engine(engine="shodan_internetdb")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_recon")

    def test_virustotal_fails(self) -> None:
        d = evaluate_engine(engine="virustotal")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_metered")


class TargetScopeTests(unittest.TestCase):
    def test_owned_package_passes(self) -> None:
        d = evaluate_target(target="com.iganapolsky.randomtimer")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_owned")

    def test_owned_itunes_id_passes(self) -> None:
        d = evaluate_target(target="6758355312")
        self.assertTrue(d.ok)

    def test_third_party_domain_fails(self) -> None:
        d = evaluate_target(target="tesla.com")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_scope")


class ComposeTests(unittest.TestCase):
    def test_owned_public_hits_compose_addresses(self) -> None:
        d = compose_footprint(sources=OWNED_SOURCES)
        self.assertTrue(d.ok)
        self.assertIn("play:com.iganapolsky.randomtimer", d.addresses)
        self.assertIn("itunes:6758355312", d.addresses)
        self.assertIn("github:IgorGanapolsky/Random-Timer", d.addresses)

    def test_empty_public_hits_fail(self) -> None:
        d = compose_footprint(sources=[{"kind": "play", "identity": "x", "status": 404}])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_empty_footprint")


class ClaimTests(unittest.TestCase):
    def test_cite_on_footprint_passes(self) -> None:
        d = evaluate_claim(
            cite="play:com.iganapolsky.randomtimer",
            addresses=["play:com.iganapolsky.randomtimer", "itunes:6758355312"],
        )
        self.assertTrue(d.ok)

    def test_invented_surface_fails(self) -> None:
        d = evaluate_claim(
            cite="shodan:1.1.1.1",
            addresses=["play:com.iganapolsky.randomtimer"],
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_off_footprint")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_more_recon(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "more-metabigor-hops",
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
        d = require_footprint_controls(
            has_engine=False, has_target=False, has_sources=False, has_cite=False
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "public_footprint.py")],
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
                str(REPO / "scripts" / "public_footprint.py"),
                "--engine",
                "public_owned",
                "--target",
                "com.iganapolsky.randomtimer",
                "--sources",
                "scripts/tests/fixtures/public_footprint_owned.json",
                "--cite",
                "play:com.iganapolsky.randomtimer",
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
