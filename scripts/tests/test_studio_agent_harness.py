"""AI Studio Agents steal: local harness. Fail closed. No Gemini API."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.studio_agent_harness import (
    evaluate_harness_files,
    evaluate_network_allowlist,
    evaluate_sandbox,
    evaluate_termination,
    evaluate_tool_allowlist,
    evaluate_verified_execution,
    rank_work,
    require_harness_controls,
)


REPO = Path(__file__).resolve().parents[2]


class HarnessFilesTests(unittest.TestCase):
    def test_agents_and_skill_pass(self) -> None:
        d = evaluate_harness_files(has_agents_md=True, has_skill_md=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_harness")

    def test_missing_skill_fails(self) -> None:
        d = evaluate_harness_files(has_agents_md=True, has_skill_md=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_harness")


class ToolAllowlistTests(unittest.TestCase):
    def test_declared_subset_passes(self) -> None:
        d = evaluate_tool_allowlist(
            requested=("local_pytest", "gh"),
            allowed=("local_pytest", "gh", "posthog_sql"),
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_tools")

    def test_undeclared_tool_fails(self) -> None:
        d = evaluate_tool_allowlist(
            requested=("open_network",),
            allowed=("local_pytest", "gh"),
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_tool")

    def test_empty_request_fails_closed(self) -> None:
        d = evaluate_tool_allowlist(requested=(), allowed=("local_pytest",))
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_undeclared_tools")


class NetworkAllowlistTests(unittest.TestCase):
    def test_explicit_domains_pass(self) -> None:
        d = evaluate_network_allowlist(
            domains=("api.github.com",),
            open_network=False,
            needs_network=True,
        )
        self.assertTrue(d.ok)

    def test_open_network_fails(self) -> None:
        d = evaluate_network_allowlist(
            domains=(),
            open_network=True,
            needs_network=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_open_network")


class TerminationTests(unittest.TestCase):
    def test_stop_condition_passes(self) -> None:
        d = evaluate_termination(stop_condition="write GSD json then stop")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_bounded")

    def test_empty_stop_fails(self) -> None:
        d = evaluate_termination(stop_condition="")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unbounded")


class SandboxTests(unittest.TestCase):
    def test_worktree_passes(self) -> None:
        d = evaluate_sandbox(isolation="worktree")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_sandbox")

    def test_checkout_fails(self) -> None:
        d = evaluate_sandbox(isolation="checkout")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_checkout")


class VerifiedExecutionTests(unittest.TestCase):
    def test_tests_and_readback_pass(self) -> None:
        d = evaluate_verified_execution(tests_passed=True, read_back=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_verified")

    def test_claim_without_readback_fails(self) -> None:
        d = evaluate_verified_execution(tests_passed=True, read_back=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unverified")


class RankWorkTests(unittest.TestCase):
    def test_iap_path_outranks_hosted_sandbox(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "hosted-antigravity",
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
        d = require_harness_controls(
            has_harness=False,
            has_tools=False,
            has_network=False,
            has_termination=False,
            has_sandbox=False,
            has_verified=False,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")

    def test_all_inputs_pass(self) -> None:
        d = require_harness_controls(
            has_harness=True,
            has_tools=True,
            has_network=True,
            has_termination=True,
            has_sandbox=True,
            has_verified=True,
        )
        self.assertTrue(d.ok)


class CliFailClosedTests(unittest.TestCase):
    def test_incomplete_cli_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "studio_agent_harness.py")],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["completeness"]["ok"])

    def test_complete_cli_exits_zero(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "studio_agent_harness.py"),
                "--agents-md",
                "--skill-md",
                "--tools",
                "local_pytest,gh",
                "--allowed-tools",
                "local_pytest,gh,posthog_sql",
                "--domains",
                "api.github.com",
                "--stop",
                "write GSD json then stop",
                "--isolation",
                "worktree",
                "--tests-passed",
                "--read-back",
            ],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["completeness"]["ok"])


if __name__ == "__main__":
    unittest.main()
