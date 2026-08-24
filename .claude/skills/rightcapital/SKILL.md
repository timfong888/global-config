---
name: rightcapital
description: Navigate and automate the RightCapital client portal (Downshift Financial white-label) via Browserless. Covers auth profile, URL structure, section map, and data extraction patterns. Activate when any task involves reading or automating app.rightcapital.com.
---

# RightCapital Portal Navigation

RightCapital is a financial planning platform. The Satchel account uses it as **Downshift Financial** (white-label). All automation goes through the Browserless MCP tool.

## Authentication

**Do not attempt to log in manually.** Use the saved Browserless auth profile:

```
profile: browserless-mt6s5jj6
```

Pass `profile: "browserless-mt6s5jj6"` on EVERY `browserless_agent` call in a session — omitting it after the first call drops auth state.

Authenticated account: `timfong888@gmail.com`

## Base URL Pattern

```
https://app.rightcapital.com/client/{clientId}/{planId}/{section}
```

Known client session IDs (from observed session):
- clientId: `kQU8FLMIfYZ2h81lrrbDCw`
- planId: `0g8lcULyLWiiZUTMQ12ehg`

If the session redirects after auth, extract the IDs from the resulting URL — they may rotate.

## Section Map

| Nav label | Path segment | Sub-sections |
|---|---|---|
| Dashboard | `dashboard/snapshot` | Snapshot (default landing) |
| Profile | `profile/net-worth` | net-worth · goals · income · savings · expenses · family |
| Vault | `vault` | Document storage |
| Settings | (modal, no path) | Account settings |

## Quick Navigation

To jump to a section, use `goto` with the full path:

```json
{"method": "goto", "params": {"url": "https://app.rightcapital.com/client/kQU8FLMIfYZ2h81lrrbDCw/0g8lcULyLWiiZUTMQ12ehg/dashboard/snapshot"}}
```

Replace the last segment with any sub-section path from the table above.

## Key Data Points (observed 2026-08-24)

| Metric | Value |
|---|---|
| Net worth | $8,088,551 |
| Probability of success (Optimized) | 82% |
| Effective federal tax rate | 16.1% |
| Portfolio allocation | 73% equity / 27% fixed income |
| Taxable assets | $5,177,393 |
| Tax-deferred assets | $876,362 |
| Tax-free assets | $520,373 |

Balance sheet breakdown: Bank $300K · Card ($18.5K) · Investment $6.27mm · Stock Plan $139K · Loan ($1.01mm) · Property $2.4mm

## Session Timeout Warning

Browserless MCP requests time out after **60 seconds**. Batch all commands for a single page into one `browserless_agent` call. Navigating to RightCapital takes ~3-5 seconds; factor this into the batch.

## Accessing the Dashboard — Minimal Recipe

```json
[
  {"method": "goto", "params": {"url": "https://app.rightcapital.com/client/kQU8FLMIfYZ2h81lrrbDCw/0g8lcULyLWiiZUTMQ12ehg/dashboard/snapshot", "waitUntil": "domcontentloaded"}},
  {"method": "waitForTimeout", "params": {"time": 4000}},
  {"method": "screenshot", "params": {}}
]
```

## Profile → Net Worth Extraction

The net worth page lists accounts by category (Bank, Card, Investment, Stock Plan, Loan, Property, Insurance, Business, Other). Use `snapshot` to read current values, or `text` to extract the full account list.

## Conceptual Platform Notes

- **Monte Carlo simulation** drives the probability-of-success metric
- **Tax bucket modeling**: RightCapital tracks taxable / tax-deferred / tax-free separately — useful for Roth conversion and RMD analysis
- **White-label**: Downshift Financial branding is cosmetic; all RightCapital features are present
- **Client vs advisor portal**: This profile accesses the client view. The advisor view (full planning workspace with what-if scenarios) requires a separate advisor login.
- **Account aggregation**: "Link Account" uses Plaid. "Add Account" is manual entry.
