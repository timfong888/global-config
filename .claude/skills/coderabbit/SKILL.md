---
name: coderabbit
description: Run CodeRabbit CLI in an agentic review-fix loop to surface bugs, security issues, and logic errors before a PR. Use after implementing a feature or fix, before committing, or when the user asks to review or quality-check code changes. TRIGGER on: "review my changes", "run coderabbit", "code review loop", "cr review", "quality check before PR".
---

# CodeRabbit Agentic Review Loop

Use this skill to run CodeRabbit CLI reviews in an iterative implement → review → fix cycle, stopping after at most **2 fix loops**.

## Prerequisites

### Installation

```bash
# Check if installed
which cr || which coderabbit

# Install if missing
curl -fsSL https://cli.coderabbit.ai/install.sh | sh
# or: brew install coderabbit
```

### Authentication

```bash
# Interactive (browser)
cr auth login

# Headless / CI (API key from coderabbit.ai → Account Settings → API Keys)
cr auth login --api-key "cr-xxxxxxxxxxxx"

# Verify
cr doctor
```

If `cr doctor` fails or the user is not authenticated, stop and ask the user to authenticate before continuing.

---

## The Agentic Loop

Run at most **2 review-fix iterations**. Do not loop more than twice — residual style warnings do not block shipping.

### Step 1 — Initial Review

```bash
# Review uncommitted/staged changes; output optimised for agent consumption
cr --prompt-only --type uncommitted
```

- `--prompt-only`: minimal, agent-oriented output (no interactive UI)
- `--type uncommitted`: target staged + unstaged local edits
- If you need structured JSON (for downstream parsing): use `cr --agent` instead

### Step 2 — Triage Findings

Prioritise findings in this order — fix only what matters:

| Severity | Action |
|---|---|
| Critical (security, data loss, crashes) | Fix immediately |
| High (logic bugs, race conditions, memory leaks) | Fix immediately |
| Medium (error handling, edge cases) | Fix if quick (<5 min) |
| Low / Style | Skip — do not loop for these |

Read cached results without re-running the full analysis:

```bash
cr review findings        # re-read last review output
cr review --show-prompts  # inspect the AI prompts used
```

### Step 3 — Apply Fixes

Apply fixes to the affected files. Keep changes minimal and targeted.

### Step 4 — Verification Pass

After fixes, run one final review to catch regressions:

```bash
cr --prompt-only --type uncommitted
```

If only low/style findings remain → **stop the loop and proceed**.  
If new critical/high findings appear → apply one more targeted fix, then stop.

---

## Command Reference

```bash
# Modes
cr                               # plain text, interactive UI (default)
cr --plain                       # detailed plain text, no UI
cr --prompt-only                 # minimal output optimised for AI agents
cr --agent                       # structured JSON for agent/skill integrations

# Scope
cr --type uncommitted            # staged + unstaged local edits (default for loops)
cr --type committed              # committed but not yet pushed
cr --base <branch>               # diff against alternate base branch

# Utilities
cr review findings               # re-read cached results from last review
cr review --show-prompts         # inspect saved AI prompts
cr stats                         # review statistics
cr doctor                        # diagnostics / health check
cr auth org                      # switch organisations
```

---

## Loop Limits & Stopping Conditions

Stop the review loop when **any** of the following is true:

- All critical and high findings are resolved
- 2 fix iterations have completed
- Only low-severity or style findings remain
- `cr doctor` reports auth/config issues (stop and escalate to user)

**Never loop more than twice.** Endless review cycles hurt velocity without proportional quality gains.

---

## Plan & CLI Limits

CLI reviews draw from your plan's included allowance first:

- **Pro plan**: covers normal agentic loop usage (1–2 review cycles per task). Sufficient for most workflows.
- **Free tier**: 3 reviews per hour limit.
- **Usage-Based Add-On** ($0.25/file): only needed for very high-volume automated pipelines (e.g., CI triggering `cr review` on every commit). Configure at: **coderabbit.ai → Account Settings → Subscription & Billing → Usage-based add-on**.

If you hit rate limits mid-loop, the add-on removes that cap — but on Pro you're unlikely to need it for typical agentic loop usage.

---

## Example Session

```text
# After implementing a feature:
1. cr --prompt-only --type uncommitted     ← loop 1: initial review
   → found 2 critical, 1 medium finding
2. [fix the 3 issues]
3. cr --prompt-only --type uncommitted     ← loop 2: verification
   → only style warnings remain → STOP
4. git add / commit / push / open PR
```
