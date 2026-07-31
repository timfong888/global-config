---
name: linear-agent-poll
description: One tick of the Linear agent poller — select issues queued in a team's "Agent Queue" workflow state (plus any handed-back issue with a fresh human reply), dispatch one worker per issue across coding/writing/admin tracks, and hand each back via workflow state, never reassignment. Use when asked to run a poll tick, work a Linear agent queue, or dispatch per-ticket Linear workers.
---

# linear-agent-poll

Ported from `github.com/timfong888/linear-agent-poller` (`.claude/commands/linear-agent-poll.md` + `profiles/*.md`). Workspace-agnostic: resolve config from the invoking repo, not from this file.

## Workspace config

Look for an `## Agent Poll Configuration` block in the invoking repo's `CLAUDE.md`. If absent, use Satchel's values below as the documented default — never invent an id, always introspect (`team { states { nodes { id name type } } }`) to confirm one still resolves before using it.

| Variable | Meaning | Satchel default |
|---|---|---|
| `TEAM_ID` / `TEAM_KEY` / `WORKSPACE_SLUG` | team id, identifier prefix, `linear.app/<slug>/issue/<KEY>-#` | `88661a7f-…30556e` / `SAT` / `sophia-xyz` |
| `STATE_AGENT_QUEUE` | **the turn signal** — a dedicated `unstarted` state before Todo; an issue in this *exact* state is queued. Each workspace needs its own | `73be9b83-…6ff5339` |
| `STATE_IN_PROGRESS` | set when a queued issue is picked up | `8439671f-…758d16` |
| `STATE_IN_REVIEW` / `STATE_NEEDS_INPUT` | every successful handback and every needs-input handback (often the same literal state — see B6) | `21d53c23-…4b7002e` |
| `STATE_BLOCKED` | Blocked handback; `none` falls back to Needs-input behavior | `f68b9fad-…7216e52` |
| `STATE_TODO` | landing state for a human-action spin-out (B6); `none` skips spin-outs | `4dfa455d-…343e21` |
| `STATE_DONE` | **never set by the agent** — Tim promotes manually | — |
| `HUMAN_USER_ID` | Tim's user id — informational; assignee never moves off it | `aa3fb002-…c92a3c748` |
| `ROUTING_LABELS` | coding/writing/admin label ids; `none` → infer track from the description | — |
| `MODEL_LABELS` / `EFFORT_LABELS` | optional per-ticket `models`/`agent-effort` label group → overrides the dispatch model/effort for that issue | — |
| `CODING_PROJECT_LABEL` / `CODING_REPO_ROOT` | which Linear *Project* is coding-track, and its repo (per-Project, not one shared repo) | — |

**Linear access.** Prefer a registered Linear MCP tool if this session has one. Otherwise Composio's `LINEAR_*` actions pinned to the configured account, with direct GraphQL via `$LINEAR_API_KEY` as a documented fallback (see the `linear-ticket` skill for exact tool names). Comments post under Tim's account — **sign every comment `(by Claude)`**, and tag it `[model: <model>, effort: <effort>]` right before the signature (the orchestrator fills these in at dispatch; a worker can't reliably self-report its own effort setting). Render any cross-issue reference as a Markdown link (`[SAT-123](https://linear.app/<slug>/issue/SAT-123)`), never a bare identifier — plain identifiers don't auto-link via the API.

## Part A — Orchestrator (one tick)

**A1. Find candidates.** Primary: issues where `state.id` **exactly equals** `STATE_AGENT_QUEUE` — a single-state equality match, not a `state.type` range. This distinction is load-bearing: In Review is also a `started`-type state (every handback lands there), so a type-range filter would re-queue every handback forever. Secondary (auto-resume, only if a floor state is configured): issues currently sitting in `STATE_IN_REVIEW` / `STATE_NEEDS_INPUT` / `STATE_BLOCKED` (dedupe ids that collide) with a human reply newer than your last `(by Claude)` comment **in that same thread**, where that thread **already contains a prior `(by Claude)` handback of yours** — you're resuming your own handback, not adopting a thread you never touched. Fetch the floor-state set by `updatedAt` (first 50 is enough — any reply bumps `updatedAt`). Empty on both → "Queue empty", end the tick.

**A2. Select the batch (oldest-first, capped).** For each candidate, fetch full issue + comments and apply the B2 pending check — **never use `comments(last: N)`**; that ordering has been unreliable on this connection repeatedly. Page `comments(first: 20, after: cursor)` until `hasNextPage` is false, then read the true newest comment. Determine track (routing label, else inferred) and any model/effort label override (translate via `MODEL_LABELS`/`EFFORT_LABELS`; absent → today's default). Fill two slots: **non-coding** (writing+admin) up to 3, **coding** up to 1 — the coding cap avoids a worktree collision between parallel workers.

**A3. Dispatch in parallel.** One subagent per selected issue, all in a single batch, running Part B below for exactly its own issue. Hand it: issue id/identifier, track, resolved model/effort, and the workspace config. Wait for all, collect each worker's one-line result.

**A4. Self-pace** (only when run on a loop with no fixed interval): worked ≥1 issue → ~2 min · empty 1st time → ~4 min · empty 2–3× → ~10 min · empty 4+× → ~30 min.

## Part B — Per-issue worker

Own exactly the one issue you were handed. Sign every comment `(by Claude)`; never post as Tim; never touch `assigneeId` except to leave it on the human.

**B1. Load layered context.** A ticket is a delta against project/epic baselines — fetch `issue { description comments { nodes { body createdAt user parent { id } } } project { description labels } parent { description } }` in one call (comment `parent.id` is thread structure, needed for B2/B5). For `project.description` / `parent.description`, look for a fenced ` ```agent-context ` block:
```
claude_md: <pointer to a linked CLAUDE.md, if any>
rules:
  - hard rule text, one per line
scope: one-line description
```
Stack layers least- to most-specific (global → repo → project → epic → issue) — additive, not overriding. Compact only verbose prose if over budget; **hard rules (`never`/`always`/`must` lines, and any `rules:` entry) survive compaction verbatim.** Only for a genuine same-point contradiction does the more-specific layer win (`ticket > epic > project`).

**B2. Confirm pending, per thread (not flat).** Linear comments are single-level threaded (`parent` id, or own id if root). For each thread, compare its newest comment against your most recent `(by Claude)` comment **in that same thread** — never against your newest comment issue-wide (a flat comparison hides a reply in an older thread behind an unrelated newer one). Pending when: you've never commented at all (fresh ask — use the description plus the newest comment in every existing thread), or some thread's newest comment is human and newer than your last reply there. All threads already answered by you → stop, return `skipped: already answered`.
- **Floor + prior-handback gate** (secondary/auto-resume path only): a reply only resumes a thread that's currently in a floor state (`STATE_IN_REVIEW`/`STATE_NEEDS_INPUT`/`STATE_BLOCKED`) **and** already contains a prior `(by Claude)` handback in it.
- **Loop breaker:** count consecutive `> question:` (needs-input) handbacks in a thread since its last Ready-for-review/Done handback. At **≥3**, stop auto-resuming it: post `🔴 Needs input — I've gone {n} rounds without converging; please restate the goal, or move this to Agent Queue to force another pass. [model: {m}, effort: {e}] (by Claude)` and treat the thread as parked.
- Pure acknowledgment with no request ("thanks", "looks good") → one short `(by Claude)` reply nudging toward Done, don't invent work, don't skip silently.

**B3. Run the track's profile.**

| Track | What to do |
|---|---|
| **coding** | Resolve the repo from the issue's **Project** via `CODING_REPO_ROOT` (each coding Project owns its own repo) — a Project not in the mapping is a config gap, ask rather than guess. State the ticket's happy path + verifiable test in plain language before branching (restate the ticket's own framing if it already has one). Branch → change → tests/lint → `coderabbit review`, apply fixes, re-run until clean (**hard merge gate, not optional**) → commit → push → open a PR with `gh`. **Never push to main.** Output: the PR's full clickable URL (see B6 template) — never a bare `PR #<N>`. |
| **writing** | Classify the ask by its end deliverable — **research** (cited findings), **plan** (structure/options/recommendation, not prose), **write** (finished prose), or **image** (edited photo, see `linear-image-pipeline`) — and self-label it if the issue has no `mode` label already (obey an existing one even if your own read differs; note the discrepancy in one line). Writing work is reversible by default: act on the most-likely reading with a stated one-line assumption rather than blocking; block only when the step is expensive/irreversible (a large research run, publish-without-review). Size the output: short (≲400 words) → post inline; long → write to a linked note if this repo has a notes/vault location configured, otherwise keep it inline or attach it as a file — don't assume an Obsidian-style vault path exists in a Blocks sandbox. |
| **admin** | Classify into exactly one sub-type by intent (email / filing / task-list) — ambiguous → one `> question:` naming the choices, Urgent, stay in review. **Trust boundary is the point, not friction:** draft-only for any outbound message (never send), propose-first for any batch of new items (never create them until an explicit approval reply), never delete anything without listing it as a proposal first. **Local-vault- or local-mailbox-dependent sub-types (file filing into a personal notes vault, a personal task-journal sweep) need that store mounted in the session** — if it isn't, say so and hand back rather than silently no-op'ing; the email/draft sub-type has no such dependency (it's API-based) and should still run normally. |

**Image capability (any track):** when a ticket needs a generated or edited image, follow `linear-image-pipeline` rather than reinventing generate→download→host→attach→cost-report.

**B4. Start work (both fresh and resume).** Post `🤖 On it — {track}. [model: {m}, effort: {e}] (by Claude)` (fresh) or `🤖 Resuming — got your reply. [model: {m}, effort: {e}] (by Claude)` (resume). Coding track: append the happy-path + test statement to this same comment. Update the issue: `state = STATE_IN_PROGRESS` only — **do not touch `assigneeId`**; this call's only job is to leave `STATE_AGENT_QUEUE` so A1 stops re-selecting it. If this repo carries the poller's own `tests/lib/progress_file.py` helper, write an initial progress record (`--phases-total <honest count>`); it's a best-effort local heartbeat aid, never a gate — skip it without blocking if the helper or its directory isn't present.

**B5. Do the work**, applying the stacked context from B1. **Threaded replies (per SAT-480):** an answer to a specific pending thread from B2 posts as a **nested reply** in that thread (`parentId` = the thread's root comment id — its own `parent.id`, or its own id if it started the thread; threads are single-level, so `parentId` is always the root, never a mid-thread id). A generic fixed "create comment" action typically has no `parentId` parameter — for a threaded reply, run the raw mutation `commentCreate(input: { issueId, body, parentId })` (pass `body` via variables, not inlined, to avoid tripping GraphQL validation on large markdown) or use a Linear MCP tool's native reply/`parentId` support if this session has one. Issue-level status comments (the B4 pickup marker, a fresh-ask B6 handback) stay top-level.

**B5.5. Self-review gate.** Before B6, re-read the ticket's own completion condition (coding: the happy-path/test statement) and the track's rules, and confirm your B5 output actually satisfies them — one pass, not a new QA harness. Pass → proceed to B6. Fail → don't post a false success: either close the gap yourself, or hand back through the Needs-input or Blocked path below instead (set `priority` = Urgent either way).

**B6. Report & hand back** — the state change *is* the handback, not reassignment.

*Legibility, every comment:* answer first (line 1 = the outcome) · one idea per bullet, ≤20 words · bold 2–4 load-bearing words per bullet, not whole sentences · no inline walls of code/URLs — own line or a link · depth lives behind a link (PR, note), not inline · target 5–8 short lines.

Pick exactly one primary outcome:
- **Needs input** — a question answerable with a typed reply:
  ```
  🔴 Needs input — {one-line what you're waiting on}
  > question: {the specific question} [model: {m}, effort: {e}] (by Claude)
  ```
  `assigneeId = HUMAN_USER_ID`, `priority = Urgent`, `state = STATE_NEEDS_INPUT` (skip the state change if it's `none`). Return `needs-input: {issue}`.
- **Blocked** — work stopped on an external dependency or a real-world action only Tim can take (not answerable inline):
  ```
  ⛔ Blocked — {one-line: what stopped the work}
  - What happened: {what was attempted, in order, and where it stopped}
  - To unblock: {the specific action/decision Tim must take}
  [model: {m}, effort: {e}] (by Claude)
  ```
  `priority = Urgent`, `state = STATE_BLOCKED` (a real, introspected workflow state — `none` falls back to Needs-input behavior, or stays `STATE_IN_PROGRESS` if both resolve to `none`). Return `blocked: {issue}`.
- **Success** (deterministic or judgment-bearing — the default outcome): `assigneeId = HUMAN_USER_ID`, `state = STATE_IN_REVIEW` (**never** `STATE_DONE` — the agent never self-certifies; Tim promotes it), `priority` = normal. Every success comment carries two bullets after the headline — `What changed:` and `Decision needed to move to Done:` (or `none — safe to promote`).
  ```
  ✅ Done — {summary + links}.
  - What changed: {short summary}
  - Decision needed to move to Done: {none — safe to promote, or the check}
  [model: {m}, effort: {e}] (by Claude)
  ```
  For a **coding PR**, `{links}` must be the PR's full clickable `https://github.com/<owner>/<repo>/pull/<N>` (resolve `<owner>/<repo>` via `gh repo view --json owner,name`, or take the URL `gh pr create` prints) — never a bare `PR #<N>` — plus a `Review on:` line naming where the diff review actually happens (GitHub, not Linear). Judgment-bearing work (writing/admin needing Tim's eyes) uses `✅ Ready for review —` instead of `✅ Done —`, same bullets, same state.
- **Human-action Todo spin-out** — composes with Success, isn't a fourth outcome. When part of the conclusion is "Tim must personally do X in the real world," create a separate `STATE_TODO` issue (`assigneeId = HUMAN_USER_ID`, no routing/model/effort label — so no A1 path ever auto-dispatches it) carrying the reasoning, `relatedTo` the original, and link it from the original's `What changed` bullet. Check for an existing spin-out first (`relatedTo` on the original, or a `STATE_TODO` issue whose description already references it) before creating a duplicate. Skip entirely if `STATE_TODO` is `none` — fold the action into the handback comment instead.

**Terminal-state rule:** the agent never sets `STATE_DONE`, however final the work looks — coding tickets don't merge their own PR either. Only the comment wording (`Done —` vs `Ready for review —`) signals confidence; the state is always `STATE_IN_REVIEW` for a successful handback. Only Needs-input and Blocked use Urgent priority.
