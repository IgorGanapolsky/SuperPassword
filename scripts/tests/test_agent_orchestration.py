"""TDD for local agent orchestration patterns."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_orchestration import (  # noqa: E402
    choose_pattern,
    evaluate_platform,
    plan_workflow,
    reconcile_concurrent,
    validate_group_chat,
    validate_handoff,
    validate_step_gate,
)


class PlatformGateTests(unittest.TestCase):
    def test_local_allowed(self) -> None:
        self.assertTrue(evaluate_platform(platform="local_agent_orchestration").ok)

    def test_external_vendor_denied(self) -> None:
        decision = evaluate_platform(platform="enterprise_agent_cloud_mesh")
        self.assertFalse(decision.ok)
        self.assertEqual(decision.action, "block_external_orchestration_vendor")


class PatternSelectionTests(unittest.TestCase):
    def test_linear_pipeline_is_sequential(self) -> None:
        self.assertEqual(
            choose_pattern(
                intent="store_release_pipeline",
                needs_parallel=False,
                unknown_route=False,
            ),
            "sequential",
        )

    def test_independent_analyses_are_concurrent(self) -> None:
        self.assertEqual(
            choose_pattern(
                intent="north_star_plus_paywall_plus_store",
                needs_parallel=True,
                unknown_route=False,
            ),
            "concurrent",
        )

    def test_unknown_triage_is_handoff(self) -> None:
        self.assertEqual(
            choose_pattern(
                intent="incoming_ops_request",
                needs_parallel=False,
                unknown_route=True,
            ),
            "handoff",
        )

    def test_debate_is_group_chat(self) -> None:
        self.assertEqual(
            choose_pattern(intent="policy_review", needs_debate=True),
            "group_chat",
        )

    def test_supervisor_is_hierarchical(self) -> None:
        self.assertEqual(
            choose_pattern(intent="fleet_ops", needs_supervisor=True),
            "hierarchical",
        )


class SequentialGateTests(unittest.TestCase):
    def test_low_confidence_blocks_next_step(self) -> None:
        gate = validate_step_gate(confidence=0.4, min_confidence=0.7, output_ok=True)
        self.assertFalse(gate.ok)
        self.assertEqual(gate.action, "escalate_human_or_supervisor")

    def test_bad_output_blocks_propagation(self) -> None:
        gate = validate_step_gate(confidence=0.95, min_confidence=0.7, output_ok=False)
        self.assertFalse(gate.ok)
        self.assertEqual(gate.action, "block_error_propagation")

    def test_passing_gate_allows_next(self) -> None:
        gate = validate_step_gate(confidence=0.9, min_confidence=0.7, output_ok=True)
        self.assertTrue(gate.ok)
        self.assertEqual(gate.action, "allow_next_step")


class HandoffGuardTests(unittest.TestCase):
    def test_max_handoffs_escalates(self) -> None:
        decision = validate_handoff(
            from_agent="triage",
            to_agent="support",
            handoff_count=3,
            max_handoffs=3,
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.action, "escalate_after_max_handoffs")

    def test_loop_detected(self) -> None:
        decision = validate_handoff(
            from_agent="a",
            to_agent="b",
            handoff_count=1,
            max_handoffs=5,
            recent_path=("a", "b", "a"),
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.action, "block_handoff_loop")

    def test_valid_handoff(self) -> None:
        decision = validate_handoff(
            from_agent="triage",
            to_agent="play_ops",
            handoff_count=0,
            max_handoffs=3,
        )
        self.assertTrue(decision.ok)


class GroupChatGuardTests(unittest.TestCase):
    def test_max_turns_escalates(self) -> None:
        decision = validate_group_chat(
            discussion_turns=6,
            max_turns=6,
            converged=False,
        )
        self.assertFalse(decision.ok)
        self.assertEqual(decision.action, "escalate_after_max_discussion_turns")


class ConcurrentReconcileTests(unittest.TestCase):
    def test_confidence_winner(self) -> None:
        result = reconcile_concurrent(
            outputs=[
                {"agent": "s", "conclusion": "hold", "confidence": 0.55},
                {"agent": "f", "conclusion": "buy", "confidence": 0.82},
            ],
            method="confidence",
        )
        self.assertTrue(result.ok)
        assert result.winner is not None
        self.assertEqual(result.winner["agent"], "f")

    def test_unresolvable_conflict_escalates(self) -> None:
        result = reconcile_concurrent(
            outputs=[
                {"agent": "a", "conclusion": "yes", "confidence": 0.7},
                {"agent": "b", "conclusion": "no", "confidence": 0.7},
            ],
            method="majority",
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.action, "escalate_unresolvable_conflict")


class PlanWorkflowTests(unittest.TestCase):
    def test_ops_verify_plan_is_sequential_with_gates(self) -> None:
        plan = plan_workflow(
            intent="play_ops_verify",
            agents=("diagnostics", "link_step", "confirm_step", "banner_readback"),
        )
        self.assertEqual(plan.pattern, "sequential")
        self.assertTrue(plan.inter_step_validation)
        self.assertGreaterEqual(plan.max_handoffs, 1)
        self.assertEqual(plan.steps[-1].agent, "banner_readback")
        self.assertTrue(all(step.requires_gate for step in plan.steps[:-1]))

    def test_concurrent_plan_skips_inter_step_gates(self) -> None:
        plan = plan_workflow(
            intent="parallel_reads",
            agents=("north_star", "paywall", "store"),
            needs_parallel=True,
        )
        self.assertEqual(plan.pattern, "concurrent")
        self.assertFalse(plan.inter_step_validation)
        self.assertEqual(plan.conflict_method, "confidence")


if __name__ == "__main__":
    unittest.main()
