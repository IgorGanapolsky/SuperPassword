"""TDD: ROSE-lite autowire runs without human shell handoff."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / ".claude" / "scripts" / "memory"))

from agent_rose_lite import autowire  # noqa: E402
from memory_manager import MemoryManager  # noqa: E402


class AutowireCoreTests(unittest.TestCase):
    def _seed_memory(self, memory_dir: Path) -> None:
        mgr = MemoryManager(memory_dir=memory_dir)
        mgr.save_cells(
            [
                {
                    "id": "c_sdk",
                    "scene": "automation",
                    "cell_type": "risk",
                    "salience": 0.5,
                    "content": "Play targetSdk 36 needs Robolectric 4.16 and JDK 21",
                    "evidence_count": 2,
                    "first_seen": "2026-09-01T00:00:00Z",
                    "last_seen": "2026-09-07T00:00:00Z",
                    "source_ids": ["lesson_sdk"],
                },
                {
                    "id": "c_ui",
                    "scene": "animation-parity",
                    "cell_type": "fact",
                    "salience": 0.9,
                    "content": "iOS cosine period equals full cycle time",
                    "evidence_count": 1,
                    "first_seen": "2026-09-01T00:00:00Z",
                    "last_seen": "2026-09-07T00:00:00Z",
                    "source_ids": ["lesson_ui"],
                },
            ]
        )

    def test_session_start_ingests_maintains_and_recalls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory_dir = root / "memory"
            memory_dir.mkdir()
            self._seed_memory(memory_dir)
            artifact = root / "out" / "rose_lite_session.json"

            result = autowire.run_autowire(
                mode="session-start",
                query="Robolectric JDK targetSdk",
                memory_dir=memory_dir,
                artifact_path=artifact,
                do_ingest=True,
                do_maintain=True,
                runtime="claude",
                hook_event="SessionStart",
                sync_claude_hooks=False,
            )

            self.assertTrue(artifact.exists())
            payload = json.loads(artifact.read_text())
            self.assertEqual(payload["mode"], "session-start")
            self.assertGreaterEqual(payload["recalled"], 1)
            self.assertIn("Robolectric", payload["cells"][0]["content"])
            self.assertIn("hookSpecificOutput", result["hook_stdout"])
            self.assertEqual(
                result["hook_stdout"]["hookSpecificOutput"]["hookEventName"],
                "SessionStart",
            )
            self.assertIn(
                "ROSE-lite",
                result["hook_stdout"]["hookSpecificOutput"]["additionalContext"],
            )

    def test_prompt_mode_uses_stdin_prompt_for_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory_dir = root / "memory"
            memory_dir.mkdir()
            self._seed_memory(memory_dir)

            stdin_payload = json.dumps(
                {"prompt": "Fix Play targetSdk 36 Robolectric failures"}
            )
            result = autowire.run_autowire(
                mode="prompt-context",
                query=None,
                memory_dir=memory_dir,
                artifact_path=root / "rose.json",
                do_ingest=False,
                do_maintain=False,
                runtime="claude",
                hook_event="UserPromptSubmit",
                stdin_text=stdin_payload,
                sync_claude_hooks=False,
            )
            self.assertEqual(result["query"], "Fix Play targetSdk 36 Robolectric failures")
            self.assertEqual(
                result["hook_stdout"]["hookSpecificOutput"]["hookEventName"],
                "UserPromptSubmit",
            )

    def test_cursor_runtime_emits_additional_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory_dir = root / "memory"
            memory_dir.mkdir()
            self._seed_memory(memory_dir)
            result = autowire.run_autowire(
                mode="session-start",
                query="animation parity",
                memory_dir=memory_dir,
                artifact_path=root / "rose.json",
                do_ingest=False,
                do_maintain=False,
                runtime="cursor",
                hook_event="sessionStart",
                sync_claude_hooks=False,
            )
            self.assertIn("additional_context", result["hook_stdout"])
            self.assertNotIn("hookSpecificOutput", result["hook_stdout"])

    def test_ci_mode_writes_marketing_artifact_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            memory_dir = root / "memory"
            memory_dir.mkdir()
            self._seed_memory(memory_dir)
            artifact = root / "marketing" / "data" / "rose_lite_autowire.json"
            result = autowire.run_autowire(
                mode="ci",
                query="automation memory maintain",
                memory_dir=memory_dir,
                artifact_path=artifact,
                do_ingest=True,
                do_maintain=True,
                runtime="ci",
                hook_event=None,
                sync_claude_hooks=False,
            )
            self.assertTrue(artifact.exists())
            body = json.loads(artifact.read_text())
            self.assertEqual(body["runtime"], "ci")
            self.assertIn("stats", body)
            self.assertEqual(result["hook_stdout"], {})

    def test_resolve_query_falls_back_to_git_branch(self) -> None:
        with mock.patch.object(
            autowire,
            "_git_branch_hint",
            return_value="feat/play-api36-robolectric",
        ):
            q = autowire.resolve_query(explicit=None, stdin_text="", env={})
        self.assertIn("play-api36", q)


class HookContractTests(unittest.TestCase):
    def test_claude_hooks_manifest_wires_session_and_prompt(self) -> None:
        # Canonical tracked manifest (settings.json is ThumbGate-protected locally).
        manifest = ROOT / "scripts" / "agent_rose_lite" / "claude_hooks.json"
        self.assertTrue(manifest.exists(), "claude_hooks.json must exist")
        data = json.loads(manifest.read_text())
        hooks = data.get("hooks") or {}
        self.assertIn("SessionStart", hooks)
        self.assertIn("UserPromptSubmit", hooks)
        session_cmd = json.dumps(hooks["SessionStart"])
        prompt_cmd = json.dumps(hooks["UserPromptSubmit"])
        self.assertIn("autowire.py", session_cmd)
        self.assertIn("session-start", session_cmd)
        self.assertIn("autowire.py", prompt_cmd)
        self.assertIn("prompt-context", prompt_cmd)

        apply_script = ROOT / "scripts" / "agent_rose_lite" / "apply_claude_hooks.py"
        self.assertTrue(apply_script.exists())

    def test_cursor_hooks_json_wires_session_and_prompt(self) -> None:
        hooks_path = ROOT / ".cursor" / "hooks.json"
        self.assertTrue(hooks_path.exists(), "tracked .cursor/hooks.json required")
        data = json.loads(hooks_path.read_text())
        self.assertEqual(data.get("version"), 1)
        self.assertIn("sessionStart", data["hooks"])
        self.assertIn("beforeSubmitPrompt", data["hooks"])
        blob = json.dumps(data)
        self.assertIn("autowire.py", blob)

    def test_workflow_exists_for_daily_maintain(self) -> None:
        wf = ROOT / ".github" / "workflows" / "rose-lite-autowire.yml"
        self.assertTrue(wf.exists())
        text = wf.read_text()
        self.assertIn("schedule:", text)
        self.assertIn("autowire.py", text)
        self.assertIn("marketing/data/rose_lite_autowire.json", text)


if __name__ == "__main__":
    unittest.main()
