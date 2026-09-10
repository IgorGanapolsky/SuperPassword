"""alphaXiv OpenResearch + HoH steal: local autoresearch loops. Fail closed. No managed compute."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_openresearch import (
    evaluate_autoresearch_loop,
    evaluate_claim,
    evaluate_compute,
    evaluate_declarative_attention,
    evaluate_eval_artifact,
    evaluate_hoh_loop,
    evaluate_platform,
    evaluate_worktree_isolation,
    pick_experiment,
    rank_work,
    require_openresearch_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_openresearch.json"


class PlatformTests(unittest.TestCase):
    def test_local_openresearch_passes(self) -> None:
        d = evaluate_platform(platform="local_openresearch")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_openresearch")

    def test_managed_compute_fails(self) -> None:
        d = evaluate_platform(platform="openresearch_managed_compute")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_managed_openresearch")


class ComputeTests(unittest.TestCase):
    def test_local_compute_passes(self) -> None:
        d = evaluate_compute(compute="local")
        self.assertTrue(d.ok)

    def test_tinker_cloud_fails(self) -> None:
        d = evaluate_compute(compute="tinker_cloud")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_paid_compute")


class WorktreeTests(unittest.TestCase):
    def test_isolated_worktree_passes(self) -> None:
        d = evaluate_worktree_isolation(isolated=True, on_shared_checkout=False)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_isolated_worktree")

    def test_shared_checkout_fails(self) -> None:
        d = evaluate_worktree_isolation(isolated=False, on_shared_checkout=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_shared_checkout")


class EvalArtifactTests(unittest.TestCase):
    def test_eval_md_with_domain_kpi_passes(self) -> None:
        d = evaluate_eval_artifact(has_eval_md=True, metric="iap_attempt")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_eval_artifact")

    def test_missing_eval_md_fails(self) -> None:
        d = evaluate_eval_artifact(has_eval_md=False, metric="iap_attempt")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_missing_eval")

    def test_proxy_metric_fails(self) -> None:
        d = evaluate_eval_artifact(has_eval_md=True, metric="paper_views")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_proxy_eval")


class AutoresearchLoopTests(unittest.TestCase):
    def test_full_loop_passes(self) -> None:
        d = evaluate_autoresearch_loop(
            hypothesized=True,
            changed_code=True,
            ran_experiment=True,
            inspected_evidence=True,
            decided_next=True,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_autoresearch_loop")

    def test_change_without_evidence_fails(self) -> None:
        d = evaluate_autoresearch_loop(
            hypothesized=True,
            changed_code=True,
            ran_experiment=False,
            inspected_evidence=False,
            decided_next=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_autoresearch")


class HohLoopTests(unittest.TestCase):
    def test_plan_code_test_with_independent_eval_passes(self) -> None:
        d = evaluate_hoh_loop(
            planned=True,
            coded=True,
            tested=True,
            independent_eval=True,
            reused_skills=True,
            repair_only=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_hoh_loop")

    def test_impl_test_as_sole_eval_fails(self) -> None:
        d = evaluate_hoh_loop(
            planned=True,
            coded=True,
            tested=True,
            independent_eval=False,
            reused_skills=True,
            repair_only=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_impl_eval_only")

    def test_repair_only_without_growth_fails(self) -> None:
        d = evaluate_hoh_loop(
            planned=True,
            coded=True,
            tested=True,
            independent_eval=True,
            reused_skills=False,
            repair_only=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_repair_only")


class DeclarativeAttentionTests(unittest.TestCase):
    def test_scoped_attention_passes(self) -> None:
        d = evaluate_declarative_attention(declared_scope=True, unbounded_context=False)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_declarative_attention")

    def test_unbounded_context_fails(self) -> None:
        d = evaluate_declarative_attention(declared_scope=False, unbounded_context=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unbounded_attention")


class PickClaimTests(unittest.TestCase):
    def test_picks_local_experiment(self) -> None:
        d = pick_experiment(
            experiments=[
                {"id": "cloud-tinker", "platform": "openresearch_managed_compute"},
                {"id": "iap-autoresearch", "platform": "local_openresearch"},
            ]
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("orx:iap-autoresearch",))

    def test_cite_must_match(self) -> None:
        picked = pick_experiment(
            experiments=[{"id": "iap-autoresearch", "platform": "local_openresearch"}]
        )
        self.assertTrue(
            evaluate_claim(cite="orx:iap-autoresearch", addresses=picked.addresses).ok
        )
        self.assertFalse(evaluate_claim(cite="orx:missing", addresses=picked.addresses).ok)


class RankTests(unittest.TestCase):
    def test_iap_beats_paper_views_proxy(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "alphaxiv-digest",
                    "metric": "paper_views",
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
        d = require_openresearch_controls(
            has_platform=True,
            has_experiments=False,
            has_cite=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliTests(unittest.TestCase):
    def test_cli_allows_local_loop(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/agent_openresearch.py"),
                "--platform",
                "local_openresearch",
                "--experiments",
                str(FIXTURE),
                "--cite",
                "orx:iap-autoresearch",
                "--compute",
                "local",
                "--isolated",
                "1",
                "--has-eval-md",
                "1",
                "--metric",
                "iap_attempt",
                "--hypothesized",
                "1",
                "--changed-code",
                "1",
                "--ran-experiment",
                "1",
                "--inspected-evidence",
                "1",
                "--decided-next",
                "1",
                "--planned",
                "1",
                "--coded",
                "1",
                "--tested",
                "1",
                "--independent-eval",
                "1",
                "--reused-skills",
                "1",
                "--declared-scope",
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
        self.assertTrue(payload["hoh"]["ok"])

    def test_cli_blocks_managed_compute(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/agent_openresearch.py"),
                "--platform",
                "openresearch_managed_compute",
                "--experiments",
                str(FIXTURE),
                "--cite",
                "orx:iap-autoresearch",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
