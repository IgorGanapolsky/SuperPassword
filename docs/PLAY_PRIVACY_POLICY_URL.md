# Play Console — Privacy Policy URL

**Canonical URL (paste into Play Console):**

```
https://igorganapolsky.github.io/Random-Timer/privacy-policy/
```

## Console path

1. [Google Play Console](https://play.google.com/console) → **Random Tactical Timer** (`4976249162120849673`)
2. **Policy** → **App content**
3. **Privacy policy** → enter the URL above → **Save**

## Verify before submit

```bash
curl -sI -A "Googlebot" "https://igorganapolsky.github.io/Random-Timer/privacy-policy/" | head -1
# Expected: HTTP/2 200
```

## Do not use

| URL | Why |
|-----|-----|
| `https://igorganapolsky.com/Random-Timer/privacy-policy/` | Custom domain path not mapped on apex site (404) |
| `https://github.com/.../blob/main/PRIVACY_POLICY.md` | GitHub UI page, not a standalone policy page |
| Any URL that 301s to `igorganapolsky.com` | Broken redirect chain caused Play 404 (fixed 2026-09-09) |

## Source of truth

- Markdown: `PRIVACY_POLICY.md` (repo root)
- Deployed HTML: `privacy-policy/index.html` → copied into `marketing/site/` by `.github/workflows/pages-deploy.yml`
- Redundant host: `IgorGanapolsky.github.io` repo path `Random-Timer/privacy-policy/` (user site mirror)

## Redeploy

```bash
gh workflow run pages-deploy.yml --ref develop
```
