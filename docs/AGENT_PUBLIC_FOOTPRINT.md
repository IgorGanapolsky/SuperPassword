# Public footprint (Metabigor-inspired, $0)

Adapted from [GitHubProjects on Threads](https://www.threads.com/@githubprojects/post/DcxNr9RG2tQ) and [j3ssie/metabigor](https://github.com/j3ssie/metabigor). Steal the **method**, not the recon binary.

Free public sources, no API keys. Compose **our** Play listing, iTunes lookup, and GitHub repo. Do not map third-party hosts, ports, certs, or CVEs.

| Metabigor | Random-Timer control plane |
| --- | --- |
| Keyless public reads | `compose_footprint` |
| Target in, surfaces out | `evaluate_target` allowlist |
| Cite a found URI | `evaluate_claim` |
| Pipeable stdout | fail-closed CLI |

## What we deliberately did *not* copy

- `metabigor cert|ip|related|cdn|url` against arbitrary sites.
- Shodan InternetDB, crt.sh pivots, grep.app secret search, VirusTotal, IntelX.

Existing Play/iTunes verifiers stay the store-version gates. This module only answers “is this an owned public surface, and did a free read-back hit it?”

## Fail-closed CLI

```bash
python3 scripts/public_footprint.py \
  --engine public_owned \
  --target com.iganapolsky.randomtimer \
  --sources scripts/tests/fixtures/public_footprint_owned.json \
  --cite play:com.iganapolsky.randomtimer
```

Allow only when every JSON `ok` is true (process exit 0). Incomplete inputs exit 2.

## Live evidence (project 299775, trailing 7d, 2026-09-08)

WQTU `3`. `timer_started` 349/48. `timer_completed` 76/18. `paywall_viewed` 19/9. `paywall_view` 12/6. `paywall_dismissed` 9/5. Zero IAP attempts. Ranker puts the attempt path ahead of more recon hops.

`paywall_purchase_success` is telemetry, not ledger revenue.

## Source

- https://www.threads.com/@githubprojects/post/DcxNr9RG2tQ
- https://github.com/j3ssie/metabigor
