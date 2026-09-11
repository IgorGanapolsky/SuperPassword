"""NVIDIA CUDA Rust steal: ownership + launch contracts for ops. Fail closed."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from scripts.agent_cuda_rust import (
    evaluate_aliasing,
    evaluate_claim,
    evaluate_disjoint_ownership,
    evaluate_doctor,
    evaluate_interop,
    evaluate_launch_contract,
    evaluate_lazy_sync,
    evaluate_platform,
    evaluate_readiness,
    evaluate_track_preference,
    pick_kernel,
    rank_work,
    require_cuda_rust_controls,
)


REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "scripts/tests/fixtures/agent_cuda_rust.json"


class PlatformTests(unittest.TestCase):
    def test_local_passes(self) -> None:
        d = evaluate_platform(platform="ops_ownership_gate")
        self.assertTrue(d.ok)

    def test_gpu_rental_fails(self) -> None:
        d = evaluate_platform(platform="cuda_cloud_gpu_rental")
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_gpu_spend")


class TrackTests(unittest.TestCase):
    def test_tile_first_passes(self) -> None:
        d = evaluate_track_preference(
            prefer_tile=True, simt_selected=False, explicit_control_needed=False
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_tile_first")

    def test_simt_without_need_fails(self) -> None:
        d = evaluate_track_preference(
            prefer_tile=False, simt_selected=True, explicit_control_needed=False
        )
        self.assertFalse(d.ok)

    def test_simt_with_need_passes(self) -> None:
        d = evaluate_track_preference(
            prefer_tile=False, simt_selected=True, explicit_control_needed=True
        )
        self.assertTrue(d.ok)


class AliasingTests(unittest.TestCase):
    def test_disjoint_buffers_pass(self) -> None:
        d = evaluate_aliasing(input_ids=["a", "b"], output_ids=["c"])
        self.assertTrue(d.ok)

    def test_overlap_fails(self) -> None:
        d = evaluate_aliasing(input_ids=["a", "c"], output_ids=["c"])
        self.assertFalse(d.ok)
        self.assertEqual(d.action, "block_aliasing")


class DisjointTests(unittest.TestCase):
    def test_exclusive_slots_pass(self) -> None:
        d = evaluate_disjoint_ownership(
            exclusive_write_slots=True, shared_mutable=False
        )
        self.assertTrue(d.ok)

    def test_shared_mutable_fails(self) -> None:
        d = evaluate_disjoint_ownership(
            exclusive_write_slots=False, shared_mutable=True
        )
        self.assertFalse(d.ok)


class LaunchContractTests(unittest.TestCase):
    def test_validated_passes(self) -> None:
        d = evaluate_launch_contract(contract_declared=True, config_validated=True)
        self.assertTrue(d.ok)

    def test_unvalidated_fails(self) -> None:
        d = evaluate_launch_contract(contract_declared=True, config_validated=False)
        self.assertFalse(d.ok)


class DoctorTests(unittest.TestCase):
    def test_doctor_pass(self) -> None:
        self.assertTrue(evaluate_doctor(doctor_pass=True).ok)

    def test_doctor_fail(self) -> None:
        self.assertFalse(evaluate_doctor(doctor_pass=False).ok)


class LazySyncTests(unittest.TestCase):
    def test_lazy_plan_passes(self) -> None:
        d = evaluate_lazy_sync(
            chain_recorded=True, synced=False, ownership_returned=False
        )
        self.assertTrue(d.ok)
        self.assertEqual(d.action, "allow_lazy_plan")

    def test_synced_with_return_passes(self) -> None:
        d = evaluate_lazy_sync(
            chain_recorded=True, synced=True, ownership_returned=True
        )
        self.assertTrue(d.ok)

    def test_sync_without_return_fails(self) -> None:
        d = evaluate_lazy_sync(
            chain_recorded=True, synced=True, ownership_returned=False
        )
        self.assertFalse(d.ok)


class ReadinessTests(unittest.TestCase):
    def test_alpha_local_ok(self) -> None:
        d = evaluate_readiness(maturity="alpha", claim_production=False)
        self.assertTrue(d.ok)

    def test_alpha_as_production_fails(self) -> None:
        d = evaluate_readiness(maturity="alpha", claim_production=True)
        self.assertFalse(d.ok)


class InteropTests(unittest.TestCase):
    def test_interop_passes(self) -> None:
        d = evaluate_interop(lock_in=False, shared_contract=True)
        self.assertTrue(d.ok)

    def test_lockin_fails(self) -> None:
        d = evaluate_interop(lock_in=True, shared_contract=False)
        self.assertFalse(d.ok)


class RankTests(unittest.TestCase):
    def test_iap_beats_tflops_vanity(self) -> None:
        ranked = rank_work(
            candidates=[
                {
                    "id": "tflops-press",
                    "metric": "gpu_tflops",
                    "expected_iap_attempts": 0,
                    "effort": 1,
                },
                {
                    "id": "iap-alias-gate",
                    "metric": "iap_attempt",
                    "expected_iap_attempts": 2,
                    "effort": 1,
                },
            ]
        )
        self.assertEqual(ranked[0]["id"], "iap-alias-gate")
        self.assertEqual(ranked[1]["score"], 0.0)


class PickClaimTests(unittest.TestCase):
    def test_picks_local_kernel(self) -> None:
        payload = json.loads(FIXTURE.read_text())
        d = pick_kernel(kernels=payload["kernels"])
        self.assertTrue(d.ok)
        self.assertIn("crs:iap-alias-gate", d.addresses)

    def test_cite_must_match(self) -> None:
        d = evaluate_claim(
            cite="crs:iap-alias-gate",
            addresses=("crs:iap-alias-gate",),
        )
        self.assertTrue(d.ok)


class CompletenessTests(unittest.TestCase):
    def test_incomplete_fails(self) -> None:
        d = require_cuda_rust_controls(
            has_platform=True, has_kernels=False, has_cite=True
        )
        self.assertFalse(d.ok)


class CliTests(unittest.TestCase):
    def test_cli_allows_local_kernel(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_cuda_rust.py"),
            "--platform",
            "ops_ownership_gate",
            "--kernels",
            str(FIXTURE),
            "--cite",
            "crs:iap-alias-gate",
            "--prefer-tile",
            "1",
            "--input-ids",
            "catalog,entitlement",
            "--output-ids",
            "iap_attempt",
            "--exclusive-write-slots",
            "1",
            "--contract-declared",
            "1",
            "--config-validated",
            "1",
            "--doctor-pass",
            "1",
            "--chain-recorded",
            "1",
            "--synced",
            "1",
            "--ownership-returned",
            "1",
            "--maturity",
            "alpha",
            "--claim-production",
            "0",
            "--lock-in",
            "0",
            "--shared-contract",
            "1",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)

    def test_cli_blocks_gpu_rental(self) -> None:
        cmd = [
            sys.executable,
            str(REPO / "scripts/agent_cuda_rust.py"),
            "--platform",
            "cuda_cloud_gpu_rental",
            "--kernels",
            str(FIXTURE),
            "--cite",
            "crs:iap-alias-gate",
        ]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["platform"]["ok"])


if __name__ == "__main__":
    unittest.main()
