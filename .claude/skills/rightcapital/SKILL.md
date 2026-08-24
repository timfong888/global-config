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

**Auth profile expiry**: The Browserless profile session `browserless-mt6s5jj6` will expire server-side after ~1 hour of use. When expired, navigating to any `/client/...` URL shows "You have been logged out." To recover: the user must manually log in at `https://app.rightcapital.com` and refresh the Browserless profile via the Browserless dashboard. The `loadSecret` / 1Password approach remains blocked until the service account `op_int_9f083604e6b2c807164bf7d7` is granted access to `browserless-access-vault`.

## Page State Persistence Between Calls

Within a session, page state IS maintained between separate `browserless_agent` calls — you do NOT need to re-navigate for every action. However:
- `snapshot` and bare `evaluate` calls (without preceding `goto`) may report `about:blank` — this is a snapshot artifact, not the actual page state. Trust screenshots over snapshots for current page state.
- Always start with `goto` when beginning a new task or after a session interruption.
- Do NOT include `goto` if you are continuing an in-progress form interaction from a previous batch.

## Expenses Page — Shadow DOM Behavior

The expenses page cards (Living Expenses, Tax and Fees, Other Expense, Medical Expense) render in **shadow DOM** and are NOT accessible via `text=` or regular CSS selectors. Key selectors:

| Element | Selector | Notes |
|---|---|---|
| "Add Expense" button | `button[data-testid='button-with-dropdown-sign']` | In accessibility tree; use native `click` |
| Dropdown items (Medical, Other…) | Not accessible via selector | Use evaluate + `MouseEvent` dispatch |
| Expense form name input | `input[name='name']` | In accessibility tree when form is open |
| Expense form amount input | `input[name='monthlyAmount']` | In accessibility tree when form is open |
| Expense form Save button | `button[type='button']:nth-of-type(2)` | When form is open; Cancel=1st, Save=2nd, Delete=3rd |
| Expense form Cancel button | `button[type='button']` | 1st occurrence |
| Expense form Delete button | `button[type='button']:nth-of-type(3)` | 3rd occurrence |
| Owner select | `select[name='personId']` | Options: Mary, Tim, Joint |
| Expense starts year | `input[type='number']` (1st) | Spinbutton for calendar year |
| Expense ends year | `input[type='number']` (2nd) | Spinbutton for calendar year |

## Adding a New Expense — Proven Flow

Complete single-batch recipe for adding a new "Other Expense" entry:

```json
[
  {"method": "goto", "params": {"url": "https://app.rightcapital.com/client/kQU8FLMIfYZ2h81lrrbDCw/0g8lcULyLWiiZUTMQ12ehg/profile/expenses", "waitUntil": "load"}},
  {"method": "waitForTimeout", "params": {"time": 5000}},
  {"method": "click", "params": {"selector": "button[data-testid='button-with-dropdown-sign']"}},
  {"method": "evaluate", "params": {"content": "(async () => { await new Promise(r => setTimeout(r, 1500)); const all = [...document.querySelectorAll('*')]; const matches = all.filter(el => el.children.length === 0 && (el.textContent||'').trim() === 'Other'); if (!matches.length) return 'NO OTHER total=' + all.length; const target = matches[matches.length-1]; target.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, composed: true})); return 'CLICKED Other'; })()"}},
  {"method": "waitForTimeout", "params": {"time": 3000}},
  {"method": "evaluate", "params": {"content": "(async () => { await new Promise(r => setTimeout(r, 1000)); const setVal = (el, v) => { const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; s.call(el, v); el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); }; const allInputs = [...document.querySelectorAll('input')]; const textInput = allInputs.find(el => !el.type || el.type === 'text'); if (textInput) setVal(textInput, 'EXPENSE NAME HERE'); const yearInputs = allInputs.filter(el => /^2\\\\d{3}$/.test(el.value)); if (yearInputs[0]) setVal(yearInputs[0], 'START_YEAR'); if (yearInputs[1]) setVal(yearInputs[1], 'END_YEAR'); const numInput = allInputs.find(el => el.type === 'number' || /^\\\\d+$/.test(el.value || '')); if (numInput && numInput !== textInput) setVal(numInput, 'MONTHLY_AMOUNT'); return 'FILLED'; })()"}},
  {"method": "waitForSelector", "params": {"selector": "button[type='button']:nth-of-type(2)", "timeout": 5000}},
  {"method": "click", "params": {"selector": "button[type='button']:nth-of-type(2)"}},
  {"method": "waitForTimeout", "params": {"time": 4000}},
  {"method": "screenshot", "params": {"fullPage": true, "type": "jpeg", "quality": 65}}
]
```

**Critical**: Clicking "Other" in the dropdown auto-creates a blank "Mary's Other Expense $0" entry on the server immediately. If you fill and Save, it updates that entry. If the batch fails before Save, the blank entry persists and must be manually deleted. Always confirm Save succeeded before adding another entry.

**Do NOT** use `evaluate` to `.click()` or dispatch `MouseEvent` on the Save/Delete/Cancel buttons — this crashes the React SPA. Use Browserless native `click` with the CSS selector instead.

## Editing an Existing Expense via URL

If you know the expense ID (from the URL after clicking a card), navigate directly:

```
https://app.rightcapital.com/client/kQU8FLMIfYZ2h81lrrbDCw/0g8lcULyLWiiZUTMQ12ehg/profile/expenses?f=profile.expenses.expense%3A{expense-id}&a=true
```

Then use the same Save/Delete button selectors above.

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
