---
name: app-store-release
description: Take an Expo / React Native app from code to TestFlight and App Store submission - EAS build, App Store screenshots, listing text, privacy answers, in-app product metadata, App Store Connect upload. Use for "ship to the App Store", "TestFlight build", "App Store screenshots", "app listing", "submit for review". Worked example is timfong888/would-you-rather (store/ios, docs/ios-build.md).
---

# App Store release (Expo / EAS)

Order: access, build config, builds, listing kit PR, Tim approves, upload, TestFlight, submit. Payments are in `payments-revenuecat`.

## Approvals

| Gate | Needs Tim's dated go |
|---|---|
| Screenshots and listing text | yes: ship them as files in a PR; upload only after he approves |
| Prices and product ids | yes (`payments-revenuecat`) |
| `production` build submitted, App Review submission | yes, separate go, never implied by a TestFlight build |

Never submit for review, switch to production keys, or create live products without a relayed go.

## Access (credentials: ask, never in chat)

Each is a **cloud-environment network secret** (agent proxy injects it), set by Tim; report the exact host, header and the shortest path.

| Need | Host | Where Tim gets it |
|---|---|---|
| Expo access token | `api.expo.dev`, `Authorization: Bearer` | https://expo.dev/settings/access-tokens, "Create token" |
| App Store Connect API key (role App Manager): .p8, Key ID, Issuer ID | `api.appstoreconnect.apple.com` | https://appstoreconnect.apple.com/access/integrations/api, "Generate API Key" |
| Paid Apps agreement signed, banking and tax | (Tim, in App Store Connect Business) | without it IAP products silently fail to load |
| Apple signing login | interactive, once, first `eas build -p ios` | Tim runs it; EAS then manages certificates |

Both hosts are blocked by default in the agent proxy (403): the environment must allow them. App Store Connect needs a short-lived ES256 JWT signed with the .p8, so a static proxy secret cannot call it: upload runs where the key can sign, never paste the .p8 into a repo or chat. If blocked, report host or key and stop; do not work around.

## Build config

- `expo-dev-client` (`npx expo install`), `eas.json` profiles: `development` (dev client, internal), `development-simulator`, `preview` and `production` (`distribution: store`, `autoIncrement`, `environment`). `appVersionSource: "remote"` goes in the top-level `cli` block, never in a build profile (EAS rejects it there): `"cli": {"version": ">= 13.2.0", "appVersionSource": "remote"}` (`environment` needs 13.2.0+).
- `ios.infoPlist.ITSAppUsesNonExemptEncryption: false` when only HTTPS is used, so TestFlight skips export compliance.
- Per-profile variables as **EAS environment variables**, not in the repo. A `eas-build-pre-install` script fails `production` builds carrying Test Store or sandbox keys.
- `eas init` (writes the project id into `app.json`), `eas build --profile preview --platform ios`, `eas submit --profile preview --platform ios` (TestFlight). Build and submit run via `npx eas-cli` with `EXPO_TOKEN` set to a dummy value so the proxy substitutes the real one.

## Listing kit (files in a PR for Tim, nothing uploaded)

`store/ios/`: `listing.md`, `privacy.md`, `iap.md`, `screenshots/<device>/NN-name.png`, `README.md` with open items.

**Screenshots** by running the app: web export or dev server in headless Chromium (Playwright), `deviceScaleFactor` so pixels are exact:

| Slot | Pixels | Viewport x scale |
|---|---|---|
| iPhone 6.9" | 1320 x 2868 | 440 x 956 @3 |
| iPhone 6.5" | 1284 x 2778 | 428 x 926 @3 |
| iPad 13" | 2064 x 2752 | 1032 x 1376 @2 |

Check the PNG header sizes. Use only real app state: do not mock data (guideline 2.3 accuracy). Web renders differ from native chrome; say so. If `supportsTablet` is true iPad shots are required: recommend iPhone-only for v1 if the iPad layout is a stretched phone column. IAP review screenshots (one paywall capture per product) need a native build.

**Listing limits:** name 30, subtitle 30, promo text 170, keywords 100 (comma-separated, no spaces), description 4000. Count them in code. Name is often taken: list fallbacks.

**Age rating and category:** use Apple's current scale (4+, 9+, 13+, 16+, 18+; the old 12+/17+ labels are gone) and answer each questionnaire item separately. Audit the shipped content, not a guess: scan the question or content bank per category for alcohol, drugs, violence, sexual, crude, gambling and mature themes, then read the hits and record the evidence (ids) next to each answer. Apple computes the final rating, so state an expectation, not a promise. If adult themes exist do not pick the Kids category. Leaving a category out of the release changes the audit: re-run it.

**Privacy (a common blocker):** the privacy policy, the App Privacy label and the real data flows must agree. Cover SDKs (`posthog`, `react-native-purchases`, crash tools) **and the backend**: read every API route that stores or logs a field (geo headers, ids, timestamps) and add its data type, e.g. coarse location stored with a player id is a Coarse Location row. Compare with the in-app policy page. In Would You Rather the page claimed "no analytics or third-party SDKs" while PostHog and RevenueCat ran. Draft replacement text in the PR; do not edit live legal text without Tim.

**IAP metadata:** table of product id, reference name, display name (30), description (45), price tier. The Apple product id must equal the RevenueCat product's `store_identifier` (not its internal `id`, e.g. `prod1a2b...`): cross-check `GET /v2/projects/{p}/products` filtered to the intended `app_id`, comparing `items[].store_identifier`.

## Upload (only after Tim approves the PR)

App Store Connect API (JWT ES256, `iss` = Issuer ID, `kid` = Key ID, audience `appstoreconnect-v1`, lifetime <= 20 minutes). Verify endpoints against current Apple docs before use. Order: version localization (text, keywords, URLs), screenshot sets per display type then screenshots, in-app purchase localizations and prices, age rating, review details. Builds arrive via `eas submit`. Re-read what was set in App Store Connect before reporting done.

## TestFlight, then submit

1. `preview` build to TestFlight; Tim or a sandbox tester installs. Run the DEVICE checks of `payments-revenuecat`.
2. Submit IAPs with the first app version (Apple reviews together).
3. Only on Tim's go: `production` build, then submit for review.

Report per step: status, PR, what Tim must do with one URL, blocked host or key.
