"""TDD for local agent sandbox + durable drive (Blaxel-inspired, zero-cost)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_blaxel_primitives import (  # noqa: E402
    AgentDrive,
    SandboxSession,
    evaluate_connectivity,
    evaluate_platform,
    rank_agent_efficiency,
    suspend_resume_roundtrip_ms,
)


class PlatformGateTests(unittest.TestCase):
    def test_local_sandbox_allowed_under_budget(self) -> None:
        d = evaluate_platform(platform="local_agent_sandbox")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_sandbox")

    def test_paid_baseten_blaxel_cloud_denied(self) -> None:
        for name in (
            "baseten_sandboxes",
            "blaxel_cloud",
            "baseten_inference_paid",
            "blaxel_agent_drive_saas",
        ):
            d = evaluate_platform(platform=name)
            self.assertFalse(d.ok, msg=name)
            self.assertEqual(d.action, "block_paid_agentic_cloud")


class AgentDriveTests(unittest.TestCase):
    def test_put_get_outlives_sandbox_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = AgentDrive(root=root / "agent_drive")
            sandbox = root / "sandbox_a"
            sandbox.mkdir()
            src = sandbox / "evidence.json"
            src.write_text(json.dumps({"oct9": False}), encoding="utf-8")
            put = drive.put(
                session_id="s1",
                relative_path="evidence.json",
                source=src,
                content_type="application/json",
            )
            self.assertTrue(put.ok)
            self.assertEqual(put.version, 1)
            for child in sandbox.iterdir():
                child.unlink()
            sandbox.rmdir()
            got = drive.get(session_id="s1", relative_path="evidence.json")
            self.assertTrue(got.ok)
            self.assertEqual(json.loads(got.path.read_text(encoding="utf-8")), {"oct9": False})
            self.assertEqual(got.version, 1)

    def test_second_put_versions_without_clobber(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            drive = AgentDrive(root=Path(tmp) / "drive")
            a = Path(tmp) / "a.txt"
            b = Path(tmp) / "b.txt"
            a.write_text("v1", encoding="utf-8")
            b.write_text("v2", encoding="utf-8")
            drive.put(session_id="s", relative_path="note.txt", source=a)
            put2 = drive.put(session_id="s", relative_path="note.txt", source=b)
            self.assertEqual(put2.version, 2)
            latest = drive.get(session_id="s", relative_path="note.txt")
            self.assertEqual(latest.path.read_text(encoding="utf-8"), "v2")
            v1 = drive.get(session_id="s", relative_path="note.txt", version=1)
            self.assertEqual(v1.path.read_text(encoding="utf-8"), "v1")


class SandboxLifecycleTests(unittest.TestCase):
    def test_suspend_sets_idle_cost_zero_and_persists_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = AgentDrive(root=root / "drive")
            session = SandboxSession.create(
                session_id="play-oct9",
                work_dir=root / "wt",
                drive=drive,
                goal="verify merchant payment method",
            )
            (session.work_dir / "scratch.txt").write_text("pending deposit", encoding="utf-8")
            suspended = session.suspend(artifact_globs=("scratch.txt",))
            self.assertTrue(suspended.ok)
            self.assertEqual(suspended.status, "suspended")
            self.assertEqual(suspended.idle_cost_usd_per_hour, 0.0)
            ckpt = drive.get(session_id="play-oct9", relative_path="_sandbox/checkpoint.json")
            self.assertTrue(ckpt.ok)
            payload = json.loads(ckpt.path.read_text(encoding="utf-8"))
            self.assertEqual(payload["goal"], "verify merchant payment method")
            self.assertEqual(payload["status"], "suspended")

    def test_resume_restores_artifacts_before_model_next_sentence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = AgentDrive(root=root / "drive")
            session = SandboxSession.create(
                session_id="s-resume",
                work_dir=root / "wt",
                drive=drive,
                goal="resume test",
            )
            (session.work_dir / "artifact.md").write_text("# keep", encoding="utf-8")
            session.suspend(artifact_globs=("artifact.md",))
            resume_dir = root / "wt2"
            resumed = SandboxSession.resume(
                session_id="s-resume",
                work_dir=resume_dir,
                drive=drive,
            )
            self.assertTrue(resumed.ok)
            self.assertEqual(resumed.status, "running")
            self.assertEqual((resume_dir / "artifact.md").read_text(encoding="utf-8"), "# keep")

    def test_suspend_resume_roundtrip_under_budget_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            drive = AgentDrive(root=root / "drive")
            ms = suspend_resume_roundtrip_ms(
                session_id="perf",
                work_dir=root / "wt",
                resume_dir=root / "wt2",
                drive=drive,
            )
            self.assertLess(ms, 250.0)


class ConnectivityIsolationTests(unittest.TestCase):
    def test_allowlisted_mcp_ok(self) -> None:
        d = evaluate_connectivity(target="mcp://user-thumbgate/satisfy_gate")
        self.assertTrue(d.ok)

    def test_unknown_egress_denied(self) -> None:
        d = evaluate_connectivity(target="https://evil.example/exfil")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_untrusted_egress")


class EfficiencyRankingTests(unittest.TestCase):
    def test_ranks_higher_outcome_per_effort_first(self) -> None:
        ranked = rank_agent_efficiency(
            [
                {"id": "spam", "outcome_weight": 1.0, "effort_units": 20.0, "improvement_rate": 0.1},
                {"id": "oct9", "outcome_weight": 8.0, "effort_units": 3.0, "improvement_rate": 0.4},
                {"id": "noise", "outcome_weight": 5.0, "effort_units": 5.0, "improvement_rate": 0.05},
            ]
        )
        self.assertEqual([r["id"] for r in ranked], ["oct9", "noise", "spam"])
        self.assertGreater(ranked[0]["efficiency_score"], ranked[1]["efficiency_score"])


if __name__ == "__main__":
    unittest.main()
