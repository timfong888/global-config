# Boldin Context Map

<!-- AGENT HEADER — machine-readable quick-reference -->
```yaml
context_map:
  subject: Boldin (NewRetirement, Inc.)
  version: "2026-08-23"
  ticket: SAT-946
  access_methods:
    primary: boldin_mcp_server       # preferred for agents
    fallback: browserless_profile    # use when MCP is insufficient
  mcp:
    endpoint: https://www.boldin.com/mcp
    transport: http
    auth: oauth_browser_flow
  browserless:
    profile: boldin
    token_env: BROWSERLESS_TOKEN
    base_url: https://production-sfo.browserless.io
    bql_url: https://production-sfo.browserless.io/chromium/bql
  auth:
    email: mary@fong888.com
    otp_delivery: email             # 10-min validity; gmail via POP has 30-60 min lag
    otp_email_account: timfong888@gmail.com
  onepassword:
    vault: browserless-access-vault
    item: Boldin
    integration_id: op_int_d58a78c2bc15ff369ddf9e05
  key_urls:
    login: https://www.boldin.com/auth/sign-in
    planner: https://www.boldin.com/retirement/planner
    assets: https://www.boldin.com/planner/myplan/assets
    developer_docs: https://developers.boldin.com/
    mcp_server: https://www.boldin.com/mcp
    help: https://help.boldin.com/en/
```

---

## 1. What is Boldin?

**Boldin** (legal name: NewRetirement, Inc. d/b/a Boldin) is a retirement-planning SaaS platform. It models the full financial life — income, spending, Social Security, taxes, real estate, healthcare, and investment accounts — through scenario planning.

- **Stack:** Ruby on Rails + Turbo/Stimulus (Hotwire)
- **Scale:** 250,000+ users, 5/5 stars (5,295 reviews)
- **Press:** Forbes, NYT, MarketWatch, WSJ, AARP

---

## 2. Agent Access Decision Tree

```
Need to read or update Boldin data?
│
├─► Is the Boldin MCP server available?
│       YES → use MCP (see §3)
│       NO  → use Browserless with `boldin` profile (see §4)
│
└─► Does the task require OTP login in this session?
        YES → warn: OTP via timfong888@gmail.com has 30-60 min POP lag
              prefer existing `boldin` profile which is already authenticated
        NO  → proceed normally
```

---

## 3. Primary Access: Boldin MCP Server

**Preferred method for all agent tasks.**

### Setup (one-time, Claude Code local)
```bash
claude mcp add --transport http boldin https://www.boldin.com/mcp
```
Then run `claude`, type `/mcp`, and complete the OAuth sign-in with the Boldin account.

### Usage (Blocks sessions — MCP already registered globally)
The MCP is available in all Blocks sessions. No setup needed.

### Tool invocation pattern
```
tool: boldin_* (enumerate via /mcp in Claude Code)
auth: OAuth flow — complete once in browser, token persists
```

---

## 4. Fallback Access: Browserless + `boldin` Profile

Use when the Boldin MCP is unavailable or when raw browser interaction is needed.

### Profile status check
```
tool: browserless_profiles
params: {}
expect: profile named "boldin" with recent updated_at
```

### Attaching the profile to any Browserless tool
```
tool: browserless_agent | browserless_smartscraper | browserless_function |
      browserless_export | browserless_crawl | browserless_performance
params:
  profile: "boldin"       # restores cookies, localStorage, IndexedDB
  # + task-specific params
```

### Raw CDP / Puppeteer connect URL
```
wss://production-sfo.browserless.io?token=<BROWSERLESS_TOKEN>&profile=boldin
```

### 1Password BQL endpoint (with credential injection)
```
https://production-sfo.browserless.io/chromium/bql
  ?token=<BROWSERLESS_TOKEN>
  &integrationId=op_int_d58a78c2bc15ff369ddf9e05
```

---

## 5. Authentication Details (Web / BQL)

| Field | Value |
|---|---|
| Sign-in URL | `https://www.boldin.com/auth/sign-in` |
| Email selector | `input#email` |
| Password selector | `input#password` |
| Submit | `button[name=button]` |
| OTP form action | `/auth/authenticate_otp?tenant_key=default` |
| OTP field | `input#otp_code` |
| Remember device | `input#remember_device` (checkbox — check it) |
| OTP submit | `input[name=commit]` |
| OTP delivery | Email → `mary@fong888.com` (10-min window) |
| OTP retrieval account | `timfong888@gmail.com` (POP: 30-60 min lag — unreliable) |

### Known failure modes

| Symptom | Cause | Fix |
|---|---|---|
| New OTP triggered mid-session | Re-submitting credentials in a new BQL session | Use existing `boldin` profile; don't re-login |
| `waitForNavigation` timeout after OTP | Hotwire/Turbo uses fetch, not full page loads | Listen for specific DOM change instead |
| Gmail OTP never arrives in time | POP polling delay (30-60 min) | Prefer `boldin` profile; avoid OTP-required flows |

---

## 6. Profile Refresh Runbook

When the `boldin` profile goes stale (calls land on the login page):

### Inspect first (dry run — no upload)
```bash
browserless profile inspect \
  --browser brave --profile Boldin \
  --only-domain boldin.com
```

### Refresh (captures + uploads in place)
```bash
browserless profile refresh \
  --browser brave --profile Boldin \
  --only-domain boldin.com \
  --name boldin --accept-terms
```

**Prerequisites:**
- Log into Boldin in local Brave **Boldin** profile (dir `Profile 1`) first
- Brave does not need to be closed
- `--only-domain boldin.com` is required every time — without it the full cookie jar uploads

### Initial upload (reference only)
```bash
browserless profile upload \
  --browser brave --profile Boldin \
  --only-domain boldin.com \
  --name boldin --accept-terms
```

**CLI location:** `/opt/homebrew/bin/browserless` v0.2.0  
**Token:** macOS keychain, server `https://production-sfo.browserless.io`

---

## 7. Key Planner URLs

| Resource | URL |
|---|---|
| Homepage | https://www.boldin.com/ |
| Login | https://www.boldin.com/auth/sign-in |
| Planner | https://www.boldin.com/retirement/planner |
| Assets | https://www.boldin.com/planner/myplan/assets |
| Pricing | https://www.boldin.com/retirement/pricing/ |
| Developer Docs | https://developers.boldin.com/ |
| MCP Server | https://www.boldin.com/mcp |
| Help Center | https://help.boldin.com/en/ |
| Enterprise | https://www.boldin.com/retirement/enterprise/home/ |
| Release Notes | https://www.boldin.com/retirement/release-notes/ |

---

## 8. Product Tiers

| Tier | Price | Key capabilities |
|---|---|---|
| **Basic** | Free | Core planner, limited AI, up to 5 coach alerts, 2 explorers, 10+ charts |
| **PlannerPlus** | $144/yr | Unlimited AI, Monte Carlo, Roth explorer, tax projections, 36+ charts, multiple scenarios, account linking |
| **Boldin Advisors** | $3,200 flat | CFP® guidance, written plan, portfolio analysis, withdrawal strategies |

---

## 9. Key Features (PlannerPlus)

- **Boldin AI** — unlimited plan conversations
- **Monte Carlo** — probability stress-testing
- **Roth Conversion Explorer** — year-by-year modeling
- **Social Security Explorer** — optimize claiming age
- **Tax projections** — state + federal, side-by-side
- **Scenario comparison** — maintain and compare multiple plan versions
- **Account linking** — top 3 aggregators (Plaid-class)
- **Digital Coach** — alerts, opportunities, warnings

---

## 10. Developer / API Integration

| Integration | Description |
|---|---|
| **MCP Server** | Connect agents directly (`https://www.boldin.com/mcp`) — preferred |
| **Tenant Data API** | Securely store, retrieve, manage user data |
| **Widgets** | Embeddable web components (incl. Roth Conversion widget) |
| **White-label Planner** | Hosted, fully branded (enterprise only) |

---

*Generated: 2026-08-23 — SAT-946 (child of SAT-857)*
