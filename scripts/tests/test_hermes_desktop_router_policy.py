"""OpenRouter Ori steal: pin Desktop tool turns; grade tools, not chat."""

from __future__ import annotations

import unittest

from scripts.hermes_desktop_router_policy import (
    PINNED_TOOL_MODELS,
    grade_tool_turn,
    decide_desktop_route,
    summarize_traffic_rows,
)


class DesktopRouterPinTests(unittest.TestCase):
    def test_hermes_main_is_pinned_for_tool_intent(self) -> None:
        d = decide_desktop_route(
            provider="custom:litellm-gateway",
            model="hermes-main",
            intent="tool",
        )
        self.assertEqual(d.action, "pin")
        self.assertTrue(d.allow)
        self.assertEqual(d.resolved_model, "hermes-main")

    def test_copilot_acp_is_blocked_for_tool_intent(self) -> None:
        d = decide_desktop_route(
            provider="copilot-acp",
            model="claude-fable-5.1",
            intent="tool",
        )
        self.assertEqual(d.action, "block_acp")
        self.assertFalse(d.allow)

    def test_local_3b_is_blocked_for_tool_intent(self) -> None:
        d = decide_desktop_route(
            provider="custom:litellm-gateway",
            model="qwen2.5:3b-hermes-64k",
            intent="tool",
        )
        self.assertEqual(d.action, "block_weak_model")
        self.assertFalse(d.allow)

    def test_openrouter_is_not_desktop_primary(self) -> None:
        d = decide_desktop_route(
            provider="openrouter",
            model="openai/gpt-4o",
            intent="tool",
        )
        self.assertEqual(d.action, "block_metered_primary")
        self.assertFalse(d.allow)

    def test_router_may_only_pick_pinned_tool_models(self) -> None:
        d = decide_desktop_route(
            provider="custom:litellm-gateway",
            model="nous-deepseek",
            intent="tool",
        )
        self.assertEqual(d.action, "route_pinned")
        self.assertTrue(d.allow)
        self.assertIn("nous-deepseek", PINNED_TOOL_MODELS)

    def test_glm_is_fallback_not_primary_pin(self) -> None:
        d = decide_desktop_route(
            provider="custom:litellm-gateway",
            model="glm-5.3",
            intent="tool",
        )
        self.assertEqual(d.action, "route_pinned")
        self.assertTrue(d.allow)


class OriStyleToolEvalTests(unittest.TestCase):
    def test_terminal_call_passes(self) -> None:
        g = grade_tool_turn(
            tool_names=["terminal"],
            assistant_text="wrote the proof file",
        )
        self.assertTrue(g.pass_eval)
        self.assertIn("terminal", g.tools_called)

    def test_meta_tool_call_without_name_fails(self) -> None:
        g = grade_tool_turn(
            tool_names=["tool_call"],
            assistant_text='{"error": "tool_call requires a \'name\' argument"}',
        )
        self.assertFalse(g.pass_eval)
        self.assertEqual(g.fail_reason, "meta_tool_call")

    def test_babysit_pip_manual_fails(self) -> None:
        g = grade_tool_turn(
            tool_names=[],
            assistant_text="Step 1: pip install notebookLM then open the browser.",
        )
        self.assertFalse(g.pass_eval)
        self.assertEqual(g.fail_reason, "babysit_prose")

    def test_empty_tools_on_tool_intent_fails(self) -> None:
        g = grade_tool_turn(
            tool_names=[],
            assistant_text="I will use the web_browser tool next.",
        )
        self.assertFalse(g.pass_eval)
        self.assertEqual(g.fail_reason, "no_tool_called")


class LocalTrafficAnalyticsTests(unittest.TestCase):
    def test_summarize_counts_models_without_external_api(self) -> None:
        rows = [
            {"model": "hermes-main", "status": "success"},
            {"model": "qwen2.5:3b-hermes-64k", "status": "success"},
            {"model": "hermes-main", "status": "failure"},
        ]
        s = summarize_traffic_rows(rows)
        self.assertEqual(s["total"], 3)
        self.assertEqual(s["by_model"]["hermes-main"]["success"], 1)
        self.assertEqual(s["by_model"]["hermes-main"]["failure"], 1)
        self.assertEqual(s["weak_model_successes"], 1)


if __name__ == "__main__":
    unittest.main()
