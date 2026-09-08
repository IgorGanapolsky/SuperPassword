---
name: skyvern-free-tier-roi
description: >
  Routes Skyvern Discover vs BrowserOS vs Play listing scripts for Random Timer.
  Use when Skyvern, Discover, or store-visibility automation is proposed.
---

# Skyvern free-tier ROI (Random Timer)

Skyvern Discover does **not** move WQTU. Play listing proof is already local:

```bash
python3 scripts/verify_play_public_listing.py --package com.iganapolsky.randomtimer --country US
python3 scripts/skyvern_free_guard.py --goal "Play listing" --url "https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer" --plan free
```

Hobby (29 USD/month) exceeds the 20 USD/month cap. Never start a paid Skyvern plan from an agent.

Allow a Skyvern cloud run only when `scripts/skyvern_free_guard.py` returns `allow_cloud_run: true` (free plan, key present, allowlisted host, max_steps <= 8).
