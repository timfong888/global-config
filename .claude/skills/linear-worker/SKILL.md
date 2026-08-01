---
name: linear-worker
description: Per-issue worker for the Linear agent poller — loads layered context, confirms the issue is pending (per thread, not flat), runs the matching track profile (coding/writing/admin), and hands back via the linear-handback skill. Dispatched by linear-agent-poll for exactly one issue; also callable directly to work a single Linear issue without the full poll tick.
whenToUse: Use to work a single Linear issue through the full poller flow (context load → pending check → track execution → handback). Called by linear-agent-poll per dispatched issue; also callable standalone as "/linear-worker SAT-123".
---

# linear-worker

Works exactly one Linear issue. Own only the issue handed to you — do not touch any other. Sign every comment `(by Claude)`; never post as Tim.

## Inputs

| Name | What it is |
|---|---|
| `issue_id` | Linear issue id (UUID) |
| `issue_identifier` | Human-readable id (e.g. `SAT-123`) |
| `track` | `coding` · `writing` · `admin` (from orchestrator label/inference; genuinely ambiguous → B3 below) |
| `model` / `effort` | Dispatch values from the orchestrator — use as-is for comment tags and when calling `linear-handback` |
| Workspace config | All `STATE_*` ids, `TEAM_ID`, `CODING_REPO_ROOT`, `HUMAN_USER_ID`, etc., resolved by `linear-agent-poll` |

**Linear access.** Prefer a registered Linear MCP tool. Otherwise Composio `LINEAR_*` actions, with direct GraphQL via `$LINEAR_API_KEY` as fallback.

## B1. Load layered context

Fetch in one call: `issue { description labels { nodes { name } } comments { nodes { id body createdAt user { id } parent { id } } pageInfo { hasNextPage endCursor } } project { id name description labels } parent { description } }`. If `pageInfo.hasNextPage` is true, keep paging with `after: endCursor` until false.

For `project.description` / `parent.description`, look for a fenced `agent-context` block:

```yaml
claude_md: <path or obsidian URI to a linked CLAUDE.md>
rules:
  - hard rule text, one per line
scope: one-line description
```

If `claude_md:` is present, resolve and read that file: join a relative path against the repo root, canonicalize, verify the result still resolves under the repo root — reject anything that escapes it. On any failure, fall back to the raw description text for that layer rather than blocking.

Stack layers least- to most-specific (global → repo → project → epic → issue) — additive, not overriding. Compact only verbose prose if over budget; **hard rules (`never`/`always`/`must` lines, and any `rules:` entry) survive compaction verbatim**. Only for a genuine same-point contradiction does the more-specific layer win (`ticket > epic > project`).

## B2. Confirm pending, per thread (not flat)

Linear comments are single-level threaded (`parent` id = thread root, or own id if a root comment). For each **distinct thread**, compare its newest comment against your most recent `(by Claude)` comment **in that same thread** — never issue-wide (a flat comparison hides replies in older or untouched threads; that was the SAT-480 bug).

**Pending** when: you've never commented on the issue at all (fresh ask — use the description plus the newest comment in every existing thread), or some thread has a human comment newer than your last `(by Claude)` reply in it. All threads already answered by you → stop, return `skipped: already answered`.

- **Floor + prior-handback gate** (secondary/auto-resume path only): a reply only resumes a thread currently in `STATE_IN_REVIEW`/`STATE_NEEDS_INPUT`/`STATE_BLOCKED` that already has a prior `(by Claude)` handback in it — you're resuming your own handback, not adopting a thread you never touched.
- **Loop breaker**: count consecutive `> question:` (needs-input) handbacks in a thread since its last Ready-for-review/Done handback. At ≥3, stop: post `🔴 Needs input — I've gone {n} rounds without converging; please restate the goal, or move this to Agent Queue to force another pass. [model: {m}, effort: {e}] (by Claude)` and stop. This is a B2 bail-out — do not proceed to B4/B6; issue state stays wherever it already was.
- **Pure acknowledgment** (floor-state threads, auto-resume path only): if the newest human reply is pure ack with no request ("thanks", "looks good") → one short `(by Claude)` acknowledgment nudging toward Done, then stop. B2 bail-out — state stays.

## B3. Run the track's profile

Use the track handed by the orchestrator. Only if genuinely ambiguous after reading the description, call `linear-handback` with `outcome=needs-input` naming the choices you couldn't pick between, and end rather than guessing.

| Track | What to do |
|---|---|
| **coding** | Resolve the repo via `CODING_REPO_ROOT` from the issue's Project name — a Project not in the mapping is a config gap, ask rather than guess. State the happy path + verifiable test in plain language before branching. Branch → change → tests/lint → `coderabbit review`, apply fixes, re-run until clean (**hard merge gate, not optional**) → commit → push → `gh pr create`. **Never push to main.** Output: full clickable PR URL for `linear-handback` success template. |
| **writing** | Classify by end deliverable: **research** (cited findings), **plan** (structure/options/recommendation), **write** (finished prose), or **image** (call `linear-image-pipeline`). Act on the most-likely reading with a stated one-line assumption rather than blocking; block only on expensive/irreversible steps. Short (≲400 words) → inline; long → linked note or attached file — don't assume an Obsidian vault path exists in a Blocks session. |
| **admin** | Classify into exactly one sub-type: email / filing / task-list. Draft-only for any outbound message (never send). Propose-first for any batch of new items (never create until an explicit approval reply). Local-vault- or mailbox-dependent sub-types require that store mounted — if it isn't, say so and hand back rather than silently no-op'ing. |

**Image capability (any track):** when a ticket needs a generated or edited image, call `linear-image-pipeline` (generate → download → host → attach → cost-report) rather than reinventing the steps.

## B4. Start work

Post `🤖 On it — {track}. [model: {m}, effort: {e}] (by Claude)` (fresh) or `🤖 Resuming — got your reply. [model: {m}, effort: {e}] (by Claude)` (resume). Coding track: append the happy-path + verifiable-test statement to this same comment. Set `state = STATE_IN_PROGRESS` — **do not touch `assigneeId`**; this call's only job is to leave `STATE_AGENT_QUEUE` so the orchestrator stops re-selecting it.

If this repo carries `tests/lib/progress_file.py`, write an initial progress record: `python3 tests/lib/progress_file.py write --dir state --issue {identifier} --phases-total <honest count> --now "..."` — best-effort local heartbeat, never a gate.

## B5. Do the work

Apply the stacked context from B1. **Threaded replies:** an answer to a specific pending thread posts as a **nested reply** (`commentCreate` with `parentId` = the thread root's id — threads are single-level so `parentId` is always the root, never a mid-thread reply). A generic "create comment" action has no `parentId` parameter — run the raw mutation `commentCreate(input: { issueId, body, parentId })` with `body` in variables (not inlined, to avoid GraphQL validation errors on large markdown), or use a Linear MCP tool's native `parentId` support if available. Issue-level status comments (B4 pickup marker, fresh-ask B6 handback) stay top-level.

Update the progress file at each natural phase boundary: `python3 tests/lib/progress_file.py write --dir state --issue {identifier} --phases-done {n} --now "..."` — best-effort, never a gate.

## B5.5. Self-review gate

Before calling `linear-handback`, re-read the ticket's completion condition (coding: the happy-path/test statement) and the track's rules, and confirm your B5 output satisfies them — one pass, not a new QA harness. Pass → proceed. Fail → either close the gap yourself (iterate on B5), or call `linear-handback` with `outcome=needs-input` or `outcome=blocked` instead (set `priority = Urgent` either way).

## B6. Hand back

Call the `linear-handback` skill, passing: `issue_id`, `issue_identifier`, `model`, `effort`, `outcome` (success/needs-input/blocked), any outcome-specific fields (summary, links, question, blocked_what, blocked_unblock), and `thread_root_id` if replying inside a specific thread.

Write the progress file terminal marker before or alongside: `python3 tests/lib/progress_file.py write --dir state --issue {identifier} --state done` — best-effort, never a gate.

Return `linear-handback`'s result (`done: {identifier}`, `needs-input: {identifier}`, or `blocked: {identifier}`) as this worker's one-line result to the orchestrator.
