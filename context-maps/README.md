# Software Tools — Context Maps Index

**Epic:** [SAT-857 — Enable Software Tools programmatically](https://linear.app/sophia-xyz/issue/SAT-857/enable-software-tools-programmatically)

This index tells agents **which context map to read** and **which Linear sub-issue to check** before working with any software tool in this workspace.

---

## How to Use This Index

1. **Identify the software tool** you need to work with.
2. **Read its context map** (linked below) — it contains access method, auth details, selectors, and known failure modes.
3. **Check the Linear sub-issue** for the latest agent notes and blockers.
4. **Pick the access method** from the decision tree in the context map (typically: MCP first, Browserless fallback).

---

## Tool Registry

| Software | Context Map | Linear Sub-issue | Primary Access | Status |
|---|---|---|---|---|
| **Boldin** (retirement planner) | [`context-maps/boldin.md`](./boldin.md) | [SAT-946](https://linear.app/sophia-xyz/issue/SAT-946/demonstrate-access-and-understanding-of-boldin) | Boldin MCP (`https://www.boldin.com/mcp`) | ✅ Mapped |

---

## Adding a New Tool

When a new software tool is onboarded under SAT-857:

1. Create `context-maps/<tool-name>.md` following the format in `boldin.md`:
   - YAML header (machine-readable access params)
   - Agent decision tree (which access method, when)
   - Auth details and selectors
   - Known failure modes
   - Key URLs

2. Add a row to the **Tool Registry** table above.

3. Link the context map from the corresponding Linear sub-issue description.

4. Invoke the `software-tool-context` skill to verify the map is complete.

---

## Global Access Patterns

These patterns apply across all tools in this Epic. Individual context maps reference them.

### Browserless (fallback browser automation)

- **MCP server:** `https://mcp.browserless.io/mcp` (HTTP, `Authorization: Bearer <BROWSERLESS_TOKEN>`)
- **Profiles:** authenticated browser state, reusable across sessions — `browserless_profiles` to list
- **1Password integration:** `op_int_d58a78c2bc15ff369ddf9e05` — inject credentials without exposing them in logs
- **BQL endpoint:** `https://production-sfo.browserless.io/chromium/bql?token=TOKEN&integrationId=OP_INT_ID`
- **Gotcha:** Hotwire/Turbo apps don't trigger `waitForNavigation` — listen for DOM changes instead

### 1Password (credential management)

- **Vault:** `browserless-access-vault` — credentials for Browserless-accessible services
- **Access pattern:** `op://browserless-access-vault/<ItemName>/<field>`
- **Service account integration ID:** `op_int_d58a78c2bc15ff369ddf9e05`

---

*Last updated: 2026-08-24 — SAT-857*
