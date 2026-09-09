# Developers — Random Tactical Timer

**Single destination** for humans and AI agents building, shipping, or extending this app.

Playbook inspiration: [Pi developer capabilities & documentation](https://minepi.com/blog/dev-capabilities-documentation/) — unify scattered docs, organize around the developer journey, publish a clear capability catalog, and keep docs aligned with current platform behavior.

Machine-readable catalog: [`developer_capabilities.json`](developer_capabilities.json)  
GitHub Pages mirror: https://igorganapolsky.github.io/Random-Timer/marketing/site/developers.md

---

## 1. Get started

1. Read [`CLAUDE.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/CLAUDE.md) (CTO operating rules) and [`AGENTS.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/AGENTS.md) (agent contract).
2. Confirm GitHub auth (`gh auth status`) — never paste PATs into chat or tracked files.
3. Fetch + PR hygiene: `git fetch --prune`, `gh pr list --state open`.
4. North Star: **WQTU** (users with ≥3 `timer_completed` in 7d) — query live PostHog before product guesses.

Package: `com.iganapolsky.randomtimer`  
Stores: [App Store](https://apps.apple.com/us/app/random-tactical-timer/id6758355312) · [Google Play](https://play.google.com/store/apps/details?id=com.iganapolsky.randomtimer)

---

## 2. Local build

Entry point: **[`Makefile`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/Makefile)** (`make verify`).

| Platform | Path | Typical command |
| --- | --- | --- |
| Android | [`native-android/`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-android/) | `./gradlew assembleDebug` / `testDebugUnitTest` |
| iOS | [`native-ios/`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/native-ios/) | `xcodebuild -scheme RandomTimer` |

Deeper platform notes:

- Android agent workflow: [`ANDROID_AGENT_WORKFLOW.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/ANDROID_AGENT_WORKFLOW.md)
- Android testing: [`ANDROID_TESTING_INSTRUCTIONS.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/ANDROID_TESTING_INSTRUCTIONS.md)
- iOS summary: [`IOS_IMPLEMENTATION_SUMMARY.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/IOS_IMPLEMENTATION_SUMMARY.md)
- Device e2e: [`DEVICE_E2E_TESTS.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/DEVICE_E2E_TESTS.md)

CI uploads debug APK artifact `app-debug` on PRs — link it after CI completes; do not ask humans to dig for it.

---

## 3. Integrate capabilities

Authoritative list (status + evidence paths): [`developer_capabilities.json`](developer_capabilities.json).

### Local storage

Preferences and session state stay **on-device** (Android DataStore / SharedPreferences; iOS UserDefaults). This is intentional: no required backend for timer prefs, lower infra cost, privacy-by-default. Data does **not** automatically follow a user across devices.

### Native share

iOS has a `ShareSheet` (`UIActivityViewController`) wrapper. It is **partial** today (component exists; product UI wiring incomplete). Android lacks an `ACTION_SEND` helper. Preferred pattern (Pi-style): use the OS share sheet for store links / session summaries instead of a custom share backend.

### Pro / payments (AI-assisted path)

1. Read entitlement code paths under Android `billing/` and iOS StoreKit modules.
2. Treat `paywall_purchase_success` as **telemetry**, not ledger revenue ([`OPERATIONAL_RELIABILITY.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/OPERATIONAL_RELIABILITY.md)).
3. Prove catalog + purchase state with store API / device evidence before claiming fixed.

### Analytics

PostHog events power WQTU and paywall funnels. Baseline notes: [`north-star-baseline.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/north-star-baseline.md). Always re-query live data when decisions matter.

### Background reliability

- iOS Live Activities: [`LIVE_ACTIVITY_IMPLEMENTATION.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/LIVE_ACTIVITY_IMPLEMENTATION.md)
- Android notifications / FGS: [`ANDROID_NOTIFICATION_ENHANCEMENTS.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/ANDROID_NOTIFICATION_ENHANCEMENTS.md)

---

## 4. Store launch

1. Metadata must be complete before publish (Android Fastlane en-US + iOS Fastlane en-US) — see [`CLAUDE.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/CLAUDE.md) Store Publishing Rule.
2. Release flow: [`RELEASE.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/RELEASE.md), version automation: [`APP_STORE_VERSION_AUTOMATION.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/APP_STORE_VERSION_AUTOMATION.md).
3. Changelog policy: [`STORE_CHANGELOG_POLICY.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/docs/STORE_CHANGELOG_POLICY.md).
4. Never claim “ready / uploaded / live” without read-back evidence (counts, field values, HTTP/API responses).

Privacy: [`../PRIVACY_POLICY.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/PRIVACY_POLICY.md)

---

## Overlap map (what this hub replaces as the entry point)

| Older / adjacent doc | Still useful for | Prefer starting at |
| --- | --- | --- |
| Root [`README.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/README.md) | Product + screenshot overview | This hub for build/ship |
| [`AGENTS.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/AGENTS.md) | Agent policy | This hub for capability path |
| [`scripts/README.md`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/scripts/README.md) | Python tooling index | This hub → then scripts |
| Marketing [`llms.txt`](https://github.com/IgorGanapolsky/Random-Timer/blob/develop/marketing/site/llms.txt) | Public AI crawl | This hub + capabilities JSON |

Audit: `python3 scripts/developers_docs_audit.py --repo-root .`
