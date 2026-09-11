# Agent CUDA Rust (NVIDIA-inspired, $0)

Adapted from NVIDIA’s CUDA Rust announcement ([MarkTechPost summary](https://www.marktechpost.com/2026/09/08/nvidia-announces-cuda-rust-with-cuda-oxide-simt-and-cutile-rs-tile-for-compile-time-safe-gpu-kernels/)): `cuda-oxide` (SIMT) and `cutile-rs` (Tile) with compile-time ownership. Steal the **safety / launch method**, not GPU cloud rental.

| Source construct | Random-Timer control plane |
| --- | --- |
| Prefer Tile before SIMT | `evaluate_track_preference` |
| Borrow checker rejects aliasing | `evaluate_aliasing` |
| DisjointSlice exclusive writes | `evaluate_disjoint_ownership` |
| `#[launch_contract]` + validate | `evaluate_launch_contract` |
| `cargo oxide doctor` | `evaluate_doctor` |
| Lazy chain until `.sync_on` | `evaluate_lazy_sync` |
| Alpha ≠ production | `evaluate_readiness` |
| Interop, no lock-in | `evaluate_interop` |

## Mapped to our product (not GPU kernels)

Example ownership gate for IAP diagnosis:

1. Doctor: env keys + Play Console session present
2. Tile-first: high-level catalog/entitlement reads before low-level `adb`/unsafe paths
3. Declare inputs (`catalog`, `entitlement`) and output (`iap_attempt`) with **no alias**
4. Launch contract: Maestro flow shape validated before run
5. Lazy plan → sync → return ownership of evidence artifacts to the host session

## What we deliberately did *not* copy

- CUDA cloud / A100 rental / HF paid GPU under the **$20/month** cap.
- Claiming TFLOPS or crates.io downloads as product progress.
- Treating alpha `cuda-oxide` / `cutile-rs` as production-ready.

## Fail-closed CLI

```bash
python3 scripts/agent_cuda_rust.py \
  --platform ops_ownership_gate \
  --kernels scripts/tests/fixtures/agent_cuda_rust.json \
  --cite crs:iap-alias-gate \
  --prefer-tile 1 \
  --input-ids catalog,entitlement --output-ids iap_attempt \
  --exclusive-write-slots 1 \
  --contract-declared 1 --config-validated 1 \
  --doctor-pass 1 \
  --chain-recorded 1 --synced 1 --ownership-returned 1 \
  --maturity alpha --claim-production 0 \
  --lock-in 0 --shared-contract 1
```

## Live evidence (project 299775, trailing 7d, 2026-09-11)

WQTU `5`. Ranker puts IAP / alias-reject gates ahead of GPU TFLOPS vanity.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://www.marktechpost.com/2026/09/08/nvidia-announces-cuda-rust-with-cuda-oxide-simt-and-cutile-rs-tile-for-compile-time-safe-gpu-kernels/
