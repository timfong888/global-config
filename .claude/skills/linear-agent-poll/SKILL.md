---
name: linear-agent-poll
description: "One tick of the Linear agent poller — select a batch of pending issues queued in the Agent Queue workflow state, dispatch one linear-worker subagent per issue in parallel (non-coding fan-out + at most one coding), and hand each back via workflow state. Workspace-agnostic — resolves IDs from the invoking project's CLAUDE.md or global-config CLAUDE.md."
whenToUse: Run when the user wants to poll and process pending Linear issues from the Agent Queue state. Use /linear-agent-poll or when asked to run a tick of the poller.
---

# /linear-agent-poll — one poll tick

You are the **orchestrator** in a `/loop`. Run **one tick**: select a batch of
pending issues, dispatch one `linear-worker` subagent per issue in parallel, then stop.

## Workspace configuration (resolve FIRST, before any Linear call)

This command is workspace-agnostic. Resolve these variables before doing anything:

1. Look for an `## Agent Poll Configuration` block in the **CLAUDE.md of the project
   you were invoked from** (the active working directory). If present, use its values.
2. If no such block exists, look for the same block in the **global-config CLAUDE.md**
   (loaded as global context in every Blocks session). Use those values if present.
3. If neither has a config block, **report a configuration error** — do not guess IDs
   or query Linear against an unconfirmed team.

| Variable | Meaning |
|---|---|
| `LINEAR_ACCOUNT` | Composio Linear connection to pin (`--account` / `account:`) |
| `TEAM_ID` | Linear team id |
| `TEAM_KEY` | Team prefix for identifiers |
| `WORKSPACE_SLUG` | Slug for cross-issue links `linear.app/<slug>/issue/<KEY>-###` |
| `STATE_AGENT_QUEUE` | **The turn signal.** Exact `unstarted`-type state — an issue here is queued for the agent. Every workspace must create its own "Agent Queue" state; there is no shared cross-workspace id. |
| `STATE_IN_PROGRESS` | "started" state id — set when the agent picks an issue up |
| `STATE_IN_REVIEW` | State for every successful handback. Also an open-loop / auto-resume state: Tim replies to a handback comment and the next tick auto-resumes it. |
| `STATE_DONE` | "completed" state id — **never set by the agent**; Tim promotes manually |
| `STATE_NEEDS_INPUT` | State on a needs-input handback; if `none`, leave state unchanged |
| `STATE_BLOCKED` | State for a Blocked handback — work stopped by an external dependency. Also a floor state for auto-resume. Must be a real team workflow state — introspect `team { states { nodes { id name type } } }` to find it, never invent an id. |
| `STATE_TODO` | Plain `unstarted` Todo state — landing state for human-action Todo spin-outs. If `none`, skip spin-outs. |
| `HUMAN_USER_ID` | Tim's user — informational only; assignee stays on the human permanently |
| `ROUTING_LABELS` | routing-label ids (coding/writing/admin); if `none`, infer track from description |
| `MODEL_LABELS` | Optional per-ticket model override. Maps label name → actual `model:` value (e.g. `sonnet 5` → `sonnet`, `opus 4.8` → `opus`, `fable 5` → `fable`, `haiku` → `haiku`). If `none`/absent, fall back to default. |
| `EFFORT_LABELS` | Optional per-ticket effort override. Identity mapping (`high` → `high`). If `none`/absent, fall back to default. |
| `CODING_PROJECT_LABEL` | Project-level label marking a Linear Project as coding-track. Until created, treat every Project in `CODING_REPO_ROOT` as coding-track. |
| `CODING_REPO_ROOT` | Per-Project repo mapping (e.g. `Project Name` → `/path/to/repo`). **No portable default — must be set per workspace.** |

All Linear calls use the Composio Linear tools pinned to `LINEAR_ACCOUNT`. Comments post
under Tim's account — **sign every agent comment `(by Claude)`**. Cross-issue links:
`[SAT-123](https://linear.app/<WORKSPACE_SLUG>/issue/SAT-123)` — never a bare identifier.

Every posted comment carries `[model: <model>, effort: <effort>]` right before `(by Claude)`.
The **orchestrator** fills these — hand them to `linear-worker` in A3 alongside `id`,
`identifier`, and `track` — the worker does not self-introspect model/effort.

Turn signal = workflow state `STATE_AGENT_QUEUE`, not assignee. Assignee stays on the human
permanently. Labels `agent-ready` / `agent-needs-human` are deprecated — clear if seen.

---

## Part A — Orchestrator (the tick)

### A1. Find candidates

**Primary path** — issues in the exact `STATE_AGENT_QUEUE` state:
```graphql
query { issues(filter: { team: { id: { eq: "<TEAM_ID>" } },
                         state: { id: { eq: "<STATE_AGENT_QUEUE>" } } }, first: 50) {
  nodes { id identifier createdAt } } }
```
Single-state equality match, **not** a `state.type` range — In Review is also a `started`-type
state; a type-range filter would re-queue every handback forever. This exact match prevents that.

**Secondary path — auto-resume from a reply.** Also catch floor-state issues
(`STATE_IN_REVIEW`, `STATE_NEEDS_INPUT`, `STATE_BLOCKED`) with a human reply newer than your
last `(by Claude)` comment in some thread:
```graphql
query { issues(filter: { team: { id: { eq: "<TEAM_ID>" } },
                         state: { id: { in: [<FLOOR_STATE_IDS>] } } },
               first: 50, orderBy: updatedAt) {
  nodes { id identifier updatedAt } } }
```
Build `<FLOOR_STATE_IDS>` from the configured floor-state ids, dropping any that resolve to
`none` and de-duplicating. Skip the secondary query if no floor state is configured.
These are candidates only — A2 and `linear-worker` B2 apply the prior-handback gate and
loop-breaker. Candidates = union of both queries. Both empty → "Queue empty", **end the tick**.

### A2. Select the batch (oldest-first, capped)

Walk candidates **oldest-first** (by `createdAt`, or oldest unaddressed human reply for the
secondary path). For each, `LINEAR_GET_LINEAR_ISSUE` and determine:

- **Pending?** — apply the B2 rule from `linear-worker`. Skip already-answered issues.
  **Never use `comments(last: N)` for this check** — page `first: 20` + `after:
  pageInfo.endCursor` until `hasNextPage` is `false`. This pre-filter saves dispatching workers
  on obviously-closed issues; `linear-worker` re-runs the full B2 check authoritatively.
- **Track** — routing label if `ROUTING_LABELS` is configured and present, else infer from description (coding · writing · admin).
- **Model override** — if `MODEL_LABELS` is configured, check for a `models`-group label and translate it. If absent, leave unset; A3 uses the default.
- **Effort override** — if `EFFORT_LABELS` is configured, check for an `agent-effort`-group label (identity mapping). If absent, leave unset; A3 uses the default.

Fill two slots, stopping when both are full or candidates run out:
- **Non-coding** (writing + admin): up to **3**
- **Coding**: up to **1** (no worktree collision)

Nothing pending → "Queue empty", end the tick.

### A3. Dispatch the batch in parallel

Spawn **one subagent per selected issue, concurrently** (a single message with multiple Agent
dispatches). Each subagent loads the **`linear-worker`** skill (Skill tool) and runs it for
exactly its one issue. Hand the worker: `id`, `identifier`, `track`, `model`, `effort`, and
all resolved workspace config variables.

**Model selection:** if A2 found a `models`-group label, use that translated model directly.
Otherwise, fall back to the inherited session default (Sonnet) unless explicitly overriding by
judgment. Wait for all workers to finish, then collect each worker's one-line result.

*Known limit:* two admin workers that both append to `CLAUDE-CHANGELOG.md` can race. Rare
with this batch size; acceptable for now.

### A4. Self-pacing (when run via `/loop` with no interval)

**Worked ≥1 issue** → ~2 min · **Empty, 1st** → ~4 min · **Empty 2–3×** → ~10 min · **Empty 4+×** → ~30 min.
