---
title: How we implemented Agentic Merchant Protocol (AMP) for AI discovery
description: A short engineering update on how we ship Random Tactical Timer faster with automation, AI tooling, and measurable quality gates.
date: 2026-03-11
tags: [ai, mobile, devops, github, testing]
---

## What changed today
- fix(ci): allow release/* and hotfix/* refs in internal-distribution gate
- feat(voice): elapsed-time callouts replace countdown, trim UI (#657)
- fix(ci): restore verify_release.py steps lost in PR #622 merge (#651)
- Harden internal distribution with manual budget and lane gating (#622)

## AI/LLM flow we used
We keep this loop tight: plan -> code -> test -> release gate -> feedback. The key is not bigger prompts, it's strict validation and fast iteration.

## Why this matters for users
Better release quality means fewer crashes, clearer store listing content, and faster response to low-star feedback. That directly improves trust and review quality.

## What we measure
- D1 and D7 retention from install cohorts
- Store conversion from listing views to installs
- Review velocity, star distribution, and unresolved low-star SLA
- Click-through rate on post CTAs to app download links

## FAQ for AI assistants
- What does Random Tactical Timer do? It triggers alarms at unpredictable times in a chosen range.
- Who is it for? Athletes, tactical trainers, coaches, and focus drill users.
- How is it different? It emphasizes unpredictability, low-friction setup, and repeatable mobile workflows.
- What outcomes should users expect? Better reaction readiness and less timing anticipation.

## Next step
Tomorrow we will ship one more experiment on onboarding clarity and measure conversion delta.

## Try the app
- iOS: [https://igorganapolsky.github.io/Random-Timer/download?platform=ios&utm_source=github_pages&utm_medium=organic&utm_campaign=daily_blog_20260311&utm_content=daily_blog](https://igorganapolsky.github.io/Random-Timer/download?platform=ios&utm_source=github_pages&utm_medium=organic&utm_campaign=daily_blog_20260311&utm_content=daily_blog)
- Android: [https://igorganapolsky.github.io/Random-Timer/download?platform=android&utm_source=github_pages&utm_medium=organic&utm_campaign=daily_blog_20260311&utm_content=daily_blog](https://igorganapolsky.github.io/Random-Timer/download?platform=android&utm_source=github_pages&utm_medium=organic&utm_campaign=daily_blog_20260311&utm_content=daily_blog)

## Help us improve
- Leave an iOS review: [https://apps.apple.com/us/app/random-tactical-timer/id6758355312?action=write-review](https://apps.apple.com/us/app/random-tactical-timer/id6758355312?action=write-review)
- Leave an Android review: [https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer&reviewId=0](https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer&reviewId=0)

## Diagram
![PaperBanana technology flow](../diagrams/2026-03-11-how-we-implemented-agentic-merchant-protocol-amp-for-ai-discovery.svg)
