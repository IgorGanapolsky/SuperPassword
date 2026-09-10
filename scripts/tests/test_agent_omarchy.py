"""Omarchy steal: pin+hash, idle release, lazy open, loopback. Fail closed. No QEMU desktop."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_omarchy import (
    evaluate_claim,
    evaluate_dirty_loop,
    evaluate_forward,
    evaluate_idle,
    evaluate_lazy_open,
    evaluate_pin,
    evaluate_platform,
    evaluate_reset,
    evaluate_share,
    pick_control,
    rank_work,
    require_omarchy_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_omarchy.json"


class PlatformTests(unittest.TestCase):
    def test_local_harness_passes(self) -> None:
        d = evaluate_platform(platform="local_omarchy_harness")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_local_omarchy_harness")

    def test_qemu_desktop_fails(self) -> None:
        d = evaluate_platform(platform="try_omarchy_qemu")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_omarchy_desktop")

    def test_basecamp_omarchy_install_fails(self) -> None:
        d = evaluate_platform(platform="omarchy_linux_desktop")
        self.assertFalse(d.ok)


class PinTests(unittest.TestCase):
    def test_pinned_with_sha256_passes(self) -> None:
        d = evaluate_pin(
            revision="c3d48b7d",
            sha256="a" * 64,
            floating=False,
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_pinned_provenance")

    def test_floating_pin_fails(self) -> None:
        d = evaluate_pin(revision="main", sha256="a" * 64, floating=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_floating_pin")

    def test_missing_hash_fails(self) -> None:
        d = evaluate_pin(revision="c3d48b7d", sha256="", floating=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_missing_hash")


class IdleTests(unittest.TestCase):
    def test_release_on_idle_passes(self) -> None:
        d = evaluate_idle(held_open=False, idle=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_idle_released")

    def test_hold_open_while_idle_fails(self) -> None:
        d = evaluate_idle(held_open=True, idle=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_idle_hold")


class LazyOpenTests(unittest.TestCase):
    def test_open_on_demand_passes(self) -> None:
        d = evaluate_lazy_open(opened_at_startup=False, demanded=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_lazy_open")

    def test_open_at_startup_without_demand_fails(self) -> None:
        d = evaluate_lazy_open(opened_at_startup=True, demanded=False)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_eager_open")


class DirtyLoopTests(unittest.TestCase):
    def test_refresh_when_dirty_passes(self) -> None:
        d = evaluate_dirty_loop(dirty=True, refreshed=True)
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_dirty_refresh")

    def test_unconditional_refresh_fails(self) -> None:
        d = evaluate_dirty_loop(dirty=False, refreshed=True)
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unconditional_refresh")


class ForwardTests(unittest.TestCase):
    def test_loopback_tcp_passes(self) -> None:
        d = evaluate_forward(bind="127.0.0.1", protocol="tcp")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_loopback_forward")

    def test_public_bind_fails(self) -> None:
        d = evaluate_forward(bind="0.0.0.0", protocol="tcp")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_public_forward")


class ShareTests(unittest.TestCase):
    def test_single_shared_path_passes(self) -> None:
        d = evaluate_share(paths=["~/Work"])
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_single_share")

    def test_multiple_shares_fail(self) -> None:
        d = evaluate_share(paths=["~/Work", "~/Secrets"])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_multi_share")


class ResetTests(unittest.TestCase):
    def test_typed_confirm_passes(self) -> None:
        d = evaluate_reset(confirm_text="Try Omarchy", expected="Try Omarchy")
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_confirmed_reset")

    def test_wrong_confirm_fails(self) -> None:
        d = evaluate_reset(confirm_text="yes", expected="Try Omarchy")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_unconfirmed_reset")


class PickClaimTests(unittest.TestCase):
    def test_picks_local_control(self) -> None:
        d = pick_control(
            controls=[
                {"id": "qemu-desktop", "platform": "try_omarchy_qemu"},
                {"id": "pin-hash-idle", "platform": "local_omarchy_harness"},
            ]
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.addresses, ("omarchy:pin-hash-idle",))

    def test_cite_must_match(self) -> None:
        picked = pick_control(
            controls=[{"id": "pin-hash-idle", "platform": "local_omarchy_harness"}]
        )
        self.assertTrue(evaluate_claim(cite="omarchy:pin-hash-idle", addresses=picked.addresses).ok)
        self.assertFalse(evaluate_claim(cite="omarchy:missing", addresses=picked.addresses).ok)


class RankTests(unittest.TestCase):
    def test_iap_beats_idle_cpu_proxy(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "cut-idle-cpu",
                    "metric": "idle_cpu",
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
        d = require_omarchy_controls(
            has_platform=True,
            has_controls=False,
            has_cite=True,
        )
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_incomplete_controls")


class CliTests(unittest.TestCase):
    def test_cli_allows_local_harness(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/agent_omarchy.py"),
                "--platform",
                "local_omarchy_harness",
                "--controls",
                str(FIXTURE),
                "--cite",
                "omarchy:pin-hash-idle",
                "--revision",
                "c3d48b7d",
                "--sha256",
                "a" * 64,
                "--bind",
                "127.0.0.1",
                "--idle",
                "1",
                "--held-open",
                "0",
                "--dirty",
                "1",
                "--refreshed",
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

    def test_cli_blocks_qemu_desktop(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts/agent_omarchy.py"),
                "--platform",
                "try_omarchy_qemu",
                "--controls",
                str(FIXTURE),
                "--cite",
                "omarchy:pin-hash-idle",
            ],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
