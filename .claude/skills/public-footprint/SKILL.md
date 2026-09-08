---
name: public-footprint
description: >
  Steal Metabigor free-public footprint method, not the recon binary. Use when
  the user pastes threads.com/@githubprojects/post/DcxNr9RG2tQ, mentions
  metabigor, hidden digital footprint, crt.sh, Shodan InternetDB, or keyless
  OSINT. Fail closed. Owned Play/iTunes/GitHub only. No third-party recon.
---

# Public footprint (steal the method)

Metabigor 2026: map a surface from free public sources, no API key. We already
have Play, iTunes, and GitHub read-backs. Compose those. Do **not** install
`metabigor`. Do **not** query Shodan, crt.sh, or VirusTotal.

## Does it help?

| Surface | Use metabigor? | Use instead |
| --- | --- | --- |
| Our Play / iTunes / GitHub | No | `evaluate_engine` engine=`public_owned` |
| "Hidden" third-party host | No | `evaluate_target` — off-scope |
| More recon hops | No | Rank IAP / WQTU, not tokens |

## Before claiming a public surface was found

```bash
python3 scripts/public_footprint.py \
  --engine public_owned \
  --target com.iganapolsky.randomtimer \
  --sources scripts/tests/fixtures/public_footprint_owned.json \
  --cite play:com.iganapolsky.randomtimer
```

Allow only when every JSON `ok` is true (process exit 0).
