"""Spotify shunt hooks: rewrite large reads locally. Fail-open on bad stdin."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.token_shunt import (
    decide_hook,
    is_targeted_bash,
    slice_text,
)


REPO = Path(__file__).resolve().parents[2]


def _fat_file(path: Path, lines: int = 400) -> Path:
    body = ["# heading one", "alpha target line"]
    body.extend(f"pad {i}" for i in range(lines))
    path.write_text("\n".join(body) + "\n")
    return path


class TargetedBashTests(unittest.TestCase):
    def test_piped_grep_is_targeted(self) -> None:
        self.assertTrue(is_targeted_bash("cat docs/AGENT_TOKEN_SHUNT.md | grep WQTU"))

    def test_bare_cat_is_not_targeted(self) -> None:
        self.assertFalse(is_targeted_bash("cat docs/AGENT_TOKEN_SHUNT.md"))


class LocalSliceTests(unittest.TestCase):
    def test_query_slice_is_smaller_than_source(self) -> None:
        text = "\n".join(["# Title", "keep this paywall line", *["x"] * 400])
        sliced = slice_text(text=text, query="paywall", max_lines=80)
        self.assertLess(len(sliced.splitlines()), 400)
        self.assertIn("paywall", sliced)


class HookDecisionTests(unittest.TestCase):
    def test_bad_stdin_fails_open(self) -> None:
        decision = decide_hook(raw="not-json")
        self.assertEqual(decision["permission"], "allow")
        self.assertEqual(decision["action"], "fail_open")

    def test_large_untargeted_read_rewrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _fat_file(Path(tmp) / "fat.md")
            decision = decide_hook(
                raw=json.dumps(
                    {
                        "tool_name": "Read",
                        "tool_input": {"path": str(path)},
                    }
                )
            )
        self.assertEqual(decision["permission"], "allow")
        self.assertEqual(decision["action"], "rewrite_read")
        self.assertEqual(decision["updated_input"]["limit"], 80)
        self.assertIn("path", decision["updated_input"])

    def test_targeted_read_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _fat_file(Path(tmp) / "fat.md")
            decision = decide_hook(
                raw=json.dumps(
                    {
                        "tool_name": "Read",
                        "tool_input": {"path": str(path), "offset": 10, "limit": 20},
                    }
                )
            )
        self.assertEqual(decision["permission"], "allow")
        self.assertEqual(decision["action"], "allow_read")

    def test_bare_cat_of_large_file_denied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _fat_file(Path(tmp) / "fat.md")
            decision = decide_hook(
                raw=json.dumps({"tool_name": "Shell", "command": f"cat {path}"})
            )
        self.assertEqual(decision["permission"], "deny")
        self.assertEqual(decision["action"], "block_bash_read")

    def test_piped_cat_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _fat_file(Path(tmp) / "fat.md")
            decision = decide_hook(
                raw=json.dumps(
                    {
                        "tool_name": "Shell",
                        "command": f"cat {path} | grep paywall",
                    }
                )
            )
        self.assertEqual(decision["permission"], "allow")
        self.assertEqual(decision["action"], "allow_bash")


class HookCliTests(unittest.TestCase):
    def test_hook_cli_rewrites_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _fat_file(Path(tmp) / "fat.md")
            proc = subprocess.run(
                [sys.executable, str(REPO / "scripts" / "token_shunt.py"), "--hook"],
                cwd=REPO,
                input=json.dumps(
                    {"tool_name": "Read", "tool_input": {"path": str(path)}}
                ),
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["permission"], "allow")
        self.assertEqual(payload["updated_input"]["limit"], 80)

    def test_hook_cli_bad_stdin_exits_zero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "token_shunt.py"), "--hook"],
            cwd=REPO,
            input="{",
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["permission"], "allow")


if __name__ == "__main__":
    unittest.main()
