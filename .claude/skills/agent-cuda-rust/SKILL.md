---
name: agent-cuda-rust
description: Fail-closed Tile-first ownership and launch-contract controls adapted from NVIDIA CUDA Rust (cuda-oxide / cutile-rs). Deny GPU cloud spend.
---

# Agent CUDA Rust

Use when parallel agents share artifacts, before launching multi-step store/IAP automation, or when choosing high-level vs low-level control paths.

## Instructions

1. Prefer **Tile** (safe high-level defaults) before **SIMT** (explicit/low-level control).
2. Reject plan-time **aliasing** (same buffer as input and mutable output).
3. Give parallel workers **exclusive write slots**; deny shared mutable ownership.
4. Declare a **launch contract** and validate config before launch.
5. Run **doctor** before scaffold/launch.
6. Record a lazy chain; execute only on **sync**, then return ownership.
7. Do not claim alpha tooling as production.
8. Keep interop; do not lock into one path.
9. Deny CUDA cloud / paid GPU rental under the monthly cap.

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

## Examples

- Allow: Tile-first IAP catalog read with disjoint evidence slots and validated Maestro contract.
- Deny: “rent A100”; “SIMT without need”; “output buffer reused as input”; “alpha is production”.

## Performance Notes

- Zero external spend path.
- Ranker zeros GPU TFLOPS / crates vanity metrics.

## Troubleshooting

- Exit `2`: inspect `aliasing`, `track`, `launch_contract`, `doctor`, `readiness` keys.
- See `docs/AGENT_CUDA_RUST.md`.
