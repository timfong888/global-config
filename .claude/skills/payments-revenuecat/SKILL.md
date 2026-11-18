---
name: payments-revenuecat
description: Add in-app purchases to an Expo / React Native app with RevenueCat, sandbox-test them, and hand off go-live to Tim. Use for "add payments", "accept payments via RevenueCat", "paywall", "in-app purchase", "unlock" or "restore purchases" in any mobile app. Worked example is timfong888/would-you-rather (PR #83, docs/payments.md).
---

# Payments with RevenueCat (Expo / React Native)

Tim reuses one RevenueCat account for every app. Agents configure RevenueCat through its API, never the dashboard. Money, prices and go-live stay with Tim.

## Approvals (stop and get Tim's words, dated)

| Gate | Needs Tim | Agent may do before it |
|---|---|---|
| Product model + prices | yes, quote his reply on the issue | draft options with a recommendation |
| Screenshots + listing text | yes (see `app-store-release`) | generate them as PR files |
| Go-live: real-money products, production keys, App Review | yes, separate go | everything on Test Store and sandbox |

PRs touching payments never auto-merge: when CI is green and review passes, report `READY <PR> <sha>` and wait.

## Access

- RevenueCat v2 API: host `api.revenuecat.com`, path `/v2`. In the cloud agent environment the proxy injects the secret key; send any dummy `Authorization: Bearer x`. Project and Test Store app ids: `GET /v2/projects`, `GET /v2/projects/{p}/apps`. Verified for Would You Rather: `proj686a561d`, Test Store `app4a3e1a9c34`.
- Node `fetch` ignores the proxy: run scripts with `NODE_USE_ENV_PROXY=1`.
- Never create live products at real prices. Test Store is simulated, no money.
- Public SDK keys (`test_`, `appl_`, `goog_`) are safe in `EXPO_PUBLIC_*`. Secret keys (`sk_`) never are.

## Steps

1. **Model.** Write the product table in the issue: product id, entitlement, price. Pattern that worked: one all-categories (or all-features) pack plus one unlock per unit; access rule = pack entitlement OR unit entitlement, so content added later is included. Ids identical in RevenueCat, Apple and Google: `<app>_premium_all`, `<app>_unlock_<unit_with_underscores>`; entitlements `premium_all`, `cat_<unit>`.
2. **Catalog as code.** Put ids, prices and the access rule in one pure module (`lib/catalog.ts`) derived from the content source, so the catalog cannot drift. A sync script reads it and creates everything idempotently (`npm run rc:sync`).
3. **Install.** `react-native-purchases`: pick the newest version whose peer `react-native` range fits the app (9.15.3 for RN 0.74; latest 11.x needs RN >= 0.80). Test Store needs v9+. No Expo Go: purchases need a dev build (`expo-dev-client`, EAS).
4. **Wrapper by platform file.** `lib/purchases.native.ts` (real SDK) and `lib/purchases.ts` (web stub: `isAvailable() = false`). Metro picks per platform, so the web bundle never contains the SDK (verify: `expo export --platform web`, grep the output). Interface: `isAvailable, configure, getEntitlements, onEntitlementsChange, getPrices, purchase(productId), restore`. `purchase` returns `{status:'cancelled'}` on user cancel and throws on other errors. The app is inert without `EXPO_PUBLIC_RC_IOS_KEY`.
5. **Gating.** Context derives `isUnlocked(id)` from active entitlements; bootstrap with `getCustomerInfo`, then `addCustomerInfoUpdateListener` so refund or expiry revokes access live. Show the store `priceString`, never a hard-coded price (keep a fallback string).
6. **Paywall.** Buy button calls the SDK directly (Apple's sheet). Offer the pack as a second button. Restore Purchases on the paywall. User cancel shows nothing. Remove any custom card/Apple Pay mock on native, and ship no owner-code or promo-code field in the App Store build (Guideline 3.1.1, re-check current text); grant yourself access with a RevenueCat promotional entitlement.
7. **Keys per stage** as EAS environment variables: development = Test Store `test_`, preview = `appl_` sandbox, production = `appl_`. Add `scripts/check-rc-keys.mjs` as the `eas-build-pre-install` hook: fail production/preview builds carrying `test_`.
8. **Tests.** Unit-test the catalog and access rule (`tsx --test`). `tsc --noEmit`, `expo export` for web and the native platform.

## RevenueCat API quirks (v2, project-scoped)

- Product: `POST /products {store_identifier, app_id, type:"non_consumable", display_name, title}`. Test Store requires `title`; allowed types are subscription, consumable, non_consumable (not `one_time`).
- Price: `POST /products/{id}/test_store_prices {prices:[{currency:"USD", amount_micros:1990000}]}`. No `country`. Repeat gives 409 "already exists": treat as success.
- Entitlement: `POST /entitlements {lookup_key, display_name}`, then `POST /entitlements/{id}/actions/attach_products {product_ids:[...]}`.
- One offering, one package per product: `POST /offerings {lookup_key:"default", display_name}`, `POST /offerings/{id}` with `is_current:true`, `POST /offerings/{id}/packages {lookup_key, display_name}`, `POST /packages/{id}/actions/attach_products {products:[{product_id, eligibility_criteria:"all"}]}`.
- Lists paginate with `next_page`; pass `?limit=100`.
- Verify as the app sees it: `GET /v1/subscribers/{id}/offerings` with the public key and `X-Platform: ios`.
- Promo grant: `POST /v2/projects/{p}/customers/{id}/actions/grant_entitlement {entitlement_id, expires_at}`. The customer must exist first (any `GET /v1/subscribers/{id}` with the public key creates it).
- Store apps (App Store, Play): create the store products by hand in the consoles (signed-token APIs, and it is Tim's price gate), then create RevenueCat product entries that reference the same ids. Apple needs the Paid Apps agreement signed or products silently fail to load.

## Sandbox test plan

AUTO (agent, Test Store): sync twice (second run creates 0); offerings via public key list every package; promo grant shows in `/v1/subscribers`; unit tests; web and native bundles build.
DEVICE (dev build or TestFlight, sandbox Apple ID): buy one unit; buy the pack; relaunch keeps access; cancel is quiet; restore after reinstall; offline or missing offering shows a sane message; refund/expiry revokes live; promo grant unlocks. Check each in the RevenueCat customer view. Report AUTO and DEVICE separately; never claim a DEVICE check passed that was not run on a device.

## Report

Per unit: status, PR, what Tim must do with one URL, blocked host or key. Credentials: say exactly where each is stored (EAS env, Vercel env, cloud-environment network secret) and never ask Tim to paste a secret in chat.
