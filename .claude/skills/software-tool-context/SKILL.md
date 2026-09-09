---
name: software-tool-context
description: 'Load the context map for a specific software tool in the SAT-857 "Enable Software Tools programmatically" Epic. Resolves access method, auth details, and known failure modes before working with the tool. Invoke at the start of any task that involves programmatically accessing a third-party software tool (Boldin, etc.) tracked under that Epic, BEFORE attempting any API call, browser automation, or MCP interaction with it.'
---

# /software-tool-context — Load a software tool's context map

## Purpose

This skill bootstraps an agent session with everything it needs to work with a specific software tool:
- Which access method to use (MCP vs. Browserless)
- Auth details, selectors, and endpoints
- Known failure modes to avoid
- Latest status from the Linear sub-issue

## Step 1 — Identify the tool

Determine which software tool the task involves. Common tools:

| Tool | Keyword signals |
|---|---|
| Boldin | "retirement planner", "Boldin", "NewRetirement", "planner", SAT-946 |

## Step 2 — Read the context map

Read the tool's context map from `global-config/context-maps/`:

| Tool | Context Map | Linear Sub-issue |
|---|---|---|
| Boldin | `context-maps/boldin.md` | SAT-946 |

**If no context map exists for the tool yet:**
1. Check `context-maps/README.md` for the Tool Registry
2. If absent, create a new map following `boldin.md` as a template
3. Add the tool to the registry and open a Linear sub-issue under SAT-857

## Step 3 — Check the Linear sub-issue

Fetch the sub-issue (e.g., SAT-946) and its comments to surface:
- Latest agent notes on blockers or workarounds
- Whether auth is stale and needs refresh
- Any changes to access method since the context map was written

```graphql
query IssueContext($id: String!) {
  issue(id: $id) {
    id identifier title description
    comments(last: 5) { nodes { body createdAt } }
  }
}
```

## Step 4 — Apply the decision tree

Every context map includes an **Agent Access Decision Tree**. Follow it to pick the access method for the current task:

```
Is the tool's MCP server available and authorized?
  YES → use MCP (preferred, no browser needed)
  NO  → use Browserless with the tool's named profile
        Is the profile authenticated (not expired)?
          YES → attach profile to Browserless tool call
          NO  → run the profile refresh runbook from the context map
```

## Step 5 — Proceed with the task

With context loaded and access method selected, proceed. Note any new failure modes or workarounds discovered during the session and update the context map via PR if significant.

---

## Index of all tools

The full registry is at:

```
global-config/context-maps/README.md
```

Epic: [SAT-857 — Enable Software Tools programmatically](https://linear.app/sophia-xyz/issue/SAT-857/enable-software-tools-programmatically)
