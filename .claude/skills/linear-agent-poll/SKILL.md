---
name: linear-agent-poll
description: One tick of the Linear agent poller — select issues queued in a team's "Agent Queue" workflow state (plus any handed-back issue with a fresh human reply), dispatch one worker per issue across coding/writing/admin tracks, and hand each back via workflow state, never reassignment. Use when asked to run a poll tick, work a Linear agent queue, or dispatch per-ticket Linear workers.
---

# linear-agent-poll

Ported from `github.com/timfong888/linear-agent-poller` (`.claude/commands/linear-agent-poll.md` + `profiles/*.md`). Workspace-agnostic: resolve config from the invoking repo, not from this file.

## Workspace config

Look for an `## Agent Poll Configuration` block in the invoking repo's `CLAUDE.md`. The Satchel values below are a documented default, **not a silent fallback** — before using them, confirm you're actually meant to be polling Satchel (the invoking repo/session says so, or Tim has said so), then introspect `team(id: "88661a7f-d07e-4590-9724-b8f69e30556e") { id name states { nodes { id name type } } }` and confirm the name/states still match before trusting any id below. If the invoking repo's `CLAUDE.md` has no config block **and** there's no clear signal you should default to Satchel, stop and report a configuration error rather than guessing — don't query or mutate Linear against an unconfirmed team, since a wrong state/team id silently mis-routes or silently no-ops every call downstream.

| Variable | Meaning | Satchel default |
|---|---|---|
| `TEAM_ID` / `TEAM_KEY` / `WORKSPACE_SLUG` | team id, identifier prefix, `linear.app/<slug>/issue/<KEY>-#` | `88661a7f-d07e-4590-9724-b8f69e30556e` / `SAT` / `sophia-xyz` |
| `STATE_AGENT_QUEUE` | **the turn signal** — a dedicated `unstarted` state before Todo; an issue in this *exact* state is queued. Each workspace needs its own | `73be9b83-4bd2-4ef1-97a7-0ff6e6ff5339` |
| `STATE_IN_PROGRESS` | set when a queued issue is picked up | `8439671f-0e5d-4a08-ba98-d3bf5b758d16` |
| `STATE_IN_REVIEW` / `STATE_NEEDS_INPUT` | every successful handback and every needs-input handback (often the same literal state — see B6) | `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` |
| `STATE_BLOCKED` | Blocked handback; `none` falls back to Needs-input behavior | `f68b9fad-0d13-4397-b1e0-97f6e7216e52` |
| `STATE_TODO` | landing state for a human-action spin-out (B6); `none` skips spin-outs | `4dfa455d-9248-4b2b-b3de-4d0d343efe21` |
| `STATE_DONE` | **never set by the agent** — Tim promotes manually | `299e627d-3989-40c4-8aea-b9d56209fa39` |
| `HUMAN_USER_ID` | Tim's user id — informational; assignee never moves off it | `aa3fb002-ba6c-440f-8837-cc5c92a3c748` |
| `ROUTING_LABELS` | coding/writing/admin label ids; `none` → infer track from the description | — (no default; infer) |
| `MODEL_LABELS` / `EFFORT_LABELS` | optional per-ticket `models`/`agent-effort` label group → overrides the dispatch model/effort for that issue | — (no default; use session default) |
| `CODING_PROJECT_LABEL` / `CODING_REPO_ROOT` | which Linear *Project* is coding-track, and its repo (per-Project, not one shared repo) | — (resolve per-Project; see B3) |

**Linear access.** Prefer a registered Linear MCP tool if this session has one. Otherwise Composio's `LINEAR_*` actions pinned to the configured account, with direct GraphQL via `$LINEAR_API_KEY` as a documented fallback (see the `linear-ticket` skill for exact tool names). Comments post under Tim's account — **sign every comment `(by Claude)`**, and tag it `[model: <model>, effort: <effort>]` right before the signature (the orchestrator fills these in at dispatch; a worker can't reliably self-report its own effort setting). Render any cross-issue reference as a Markdown link (`[SAT-123](https://linear.app/<slug>/issue/SAT-123)`), never a bare identifier — plain identifiers don't auto-link via the API.

## Part A — Orchestrator (one tick)

**A1. Find candidates.** Primary: issues where `state.id` **exactly equals** `STATE_AGENT_QUEUE`, oldest-first, capped at the first 50 (same deliberate bound as the secondary query below) — a single-state equality match, not a `state.type` range. This distinction is load-bearing: In Review is also a `started`-type state (every handback lands there), so a type-range filter would re-queue every handback forever. Secondary (auto-resume, only if a floor state is configured): issues currently sitting in `STATE_IN_REVIEW` / `STATE_NEEDS_INPUT` / `STATE_BLOCKED` (dedupe ids that collide) with a human reply newer than your last `(by Claude)` comment **in that same thread**, where that thread **already contains a prior `(by Claude)` handback of yours** — you're resuming your own handback, not adopting a thread you never touched. Fetch the floor-state set by `updatedAt` (first 50 is enough — any reply bumps `updatedAt`). Empty on both → "Queue empty", end the tick.

**A2. Select the batch (oldest-first, capped).** For each candidate, fetch full issue + comments and apply the B2 pending check — **never use `comments(last: N)`**; that ordering has been unreliable on this connection repeatedly. Page `comments(first: 20, after: cursor)` until `hasNextPage` is false, then read the true newest comment. Determine track (routing label, else inferred) and any model/effort label override (translate via `MODEL_LABELS`/`EFFORT_LABELS`; absent → today's default). Fill two slots: **non-coding** (writing+admin) up to 3, **coding** up to 1 — the coding cap avoids a worktree collision between parallel workers.

**A3. Dispatch in parallel.** One subagent per selected issue, all in a single batch, each loading the **`linear-worker`** skill for exactly its own issue. Hand it: issue id/identifier, track, resolved model/effort, and the workspace config. Wait for all, collect each worker's one-line result (`done:`, `needs-input:`, `blocked:`, or `skipped:`).

**A4. Self-pace** (only when run on a loop with no fixed interval): worked ≥1 issue → ~2 min · empty 1st time → ~4 min · empty 2–3× → ~10 min · empty 4+× → ~30 min.

## Part B — Per-issue worker

Each dispatched subagent loads the **`linear-worker`** skill and runs it for exactly its one issue. The worker handles all per-issue logic: layered context loading (B1), per-thread pending check (B2), track profile execution (B3–B5.5), and handback via the **`linear-handback`** skill (B6). Pass it: issue `id`/`identifier`, `track`, resolved `model`/`effort`, and the workspace config above.
