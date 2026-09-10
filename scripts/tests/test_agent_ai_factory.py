"""NVIDIA/Palantir AI-factory steal: sovereign local ops ontology. Fail closed."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_ai_factory import (
    evaluate_claim,
    evaluate_decision_log_training,
    evaluate_ontology,
    evaluate_proving_ground,
    evaluate_scarce_allocation,
    evaluate_sovereignty,
    evaluate_specialization,
    evaluate_specialization_honesty,
    pick_factory,
    rank_work,
    require_ai_factory_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_ai_factory.json"


class SovereigntyTests(unittest.TestCase):
    def test_local_sovereign_passes(self) -> None:
        d = evaluate_sovereignty(
            data_local=True,
            weights_local=True,
            inference_local=True,
            proprietary_exported=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_sovereign_local")

    def test_proprietary_export_fails(self) -> None:
        d = evaluate_sovereignty(
            data_local=False,
            weights_local=False,
            inference_local=False,
            proprietary_exported=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_proprietary_export")


class OntologyTests(unittest.TestCase):
    def test_live_ontology_passes(self) -> None:
        d = evaluate_ontology(
            ontology_live=True,
            entities=("wqtu", "paywall", "release", "agent_slot"),
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_live_ontology")

    def test_empty_ontology_fails(self) -> None:
        d = evaluate_ontology(ontology_live=False, entities=())
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_missing_ontology")


class SpecializationTests(unittest.TestCase):
    def test_domain_specialized_beats_general_passes(self) -> None:
        d = evaluate_specialization(
            domain_post_trained=True,
            domain_eval_beats_general=True,
            chose_bigger_without_domain_eval=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_domain_specialization")

    def test_bigger_without_domain_eval_fails(self) -> None:
        d = evaluate_specialization(
            domain_post_trained=False,
            domain_eval_beats_general=False,
            chose_bigger_without_domain_eval=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_size_over_domain")


class DecisionLogTests(unittest.TestCase):
    def test_ops_decision_log_passes(self) -> None:
        d = evaluate_decision_log_training(
            trained_on_ops_decisions=True,
            generic_chat_only=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_decision_log_training")

    def test_generic_chat_only_fails(self) -> None:
        d = evaluate_decision_log_training(
            trained_on_ops_decisions=False,
            generic_chat_only=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_generic_chat_training")


class ScarceAllocationTests(unittest.TestCase):
    def test_budgeted_allocation_passes(self) -> None:
        d = evaluate_scarce_allocation(
            budget_remaining_usd=12.0,
            concurrent_slots=2,
            max_slots=3,
            allocation_evidenced=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_scarce_allocation")

    def test_over_cap_fails(self) -> None:
        d = evaluate_scarce_allocation(
            budget_remaining_usd=0.0,
            concurrent_slots=5,
            max_slots=3,
            allocation_evidenced=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unbounded_allocation")


class ProvingGroundTests(unittest.TestCase):
    def test_own_ops_first_passes(self) -> None:
        d = evaluate_proving_ground(own_ops_validated=True, export_before_proof=False)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_proving_ground")

    def test_export_before_proof_fails(self) -> None:
        d = evaluate_proving_ground(own_ops_validated=False, export_before_proof=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_export_before_proof")


class HonestyTests(unittest.TestCase):
    def test_scoped_task_claim_passes(self) -> None:
        d = evaluate_specialization_honesty(
            scoped_task_claim=True,
            claims_universal_capability=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_scoped_specialization_claim")

    def test_universal_claim_fails(self) -> None:
        d = evaluate_specialization_honesty(
            scoped_task_claim=False,
            claims_universal_capability=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_universal_specialization_claim")


class RankTests(unittest.TestCase):
    def test_domain_specialized_beats_frontier_vanity(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "frontier-550b",
                    "metric": "model_parameter_count",
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "local-domain-30b",
                    "metric": "domain_allocation_accuracy",
                    "expected_iap_attempts": 3,
                    "effort": 1,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "local-domain-30b")
        self.assertEqual(ranked[1]["score"], 0.0)


class PickClaimTests(unittest.TestCase):
    def test_picks_local_factory(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        d = pick_factory(factories=payload["factories"])
        self.assertTrue(d.ok)
        self.assertIn("aif:local-ops-ontology", d.addresses)

    def test_cite_must_match(self) -> None:
        d = evaluate_claim(
            cite="aif:local-ops-ontology",
            addresses=("aif:local-ops-ontology",),
        )
        self.assertTrue(d.ok)
        bad = evaluate_claim(cite="aif:foundry-cloud", addresses=("aif:local-ops-ontology",))
        self.assertFalse(bad.ok)


class CompletenessTests(unittest.TestCase):
    def test_incomplete_controls_fail(self) -> None:
        d = require_ai_factory_controls(
            has_platform=False,
            has_factories=True,
            has_cite=True,
        )
        self.assertFalse(d.ok)


class CliTests(unittest.TestCase):
    def test_cli_allows_local_factory(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_ai_factory.py"),
            "--platform",
            "local_ai_factory",
            "--factories",
            str(FIXTURE),
            "--cite",
            "aif:local-ops-ontology",
            "--data-local",
            "1",
            "--weights-local",
            "1",
            "--inference-local",
            "1",
            "--ontology-live",
            "1",
            "--entities",
            "wqtu,paywall,release,agent_slot",
            "--domain-post-trained",
            "1",
            "--domain-eval-beats-general",
            "1",
            "--trained-on-ops-decisions",
            "1",
            "--budget-remaining-usd",
            "12",
            "--concurrent-slots",
            "2",
            "--max-slots",
            "3",
            "--allocation-evidenced",
            "1",
            "--own-ops-validated",
            "1",
            "--scoped-task-claim",
            "1",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["completeness"]["ok"])

    def test_cli_blocks_foundry_export(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_ai_factory.py"),
            "--platform",
            "palantir_foundry_cloud",
            "--factories",
            str(FIXTURE),
            "--cite",
            "aif:local-ops-ontology",
            "--proprietary-exported",
            "1",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2, proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["platform"]["ok"])


if __name__ == "__main__":
    unittest.main()
