---
name: linear-handback
description: Post a standardized handback comment and set the correct workflow state on a Linear issue. Covers all three primary outcomes — Success, Needs input, Blocked — plus the optional Human-action Todo spin-out. Callable from any track (coding, writing, admin) so every handback uses the same comment templates and state-transition logic.
whenToUse: Use at the end of working a Linear issue to post the handback comment and set workflow state. Called by linear-worker B6; also callable directly from any track profile that handles its own ticket work.
---

# linear-handback

Posts the closing comment and transitions the Linear workflow state after working an issue. The **state change is the handback**, not reassignment — `assigneeId` stays on `HUMAN_USER_ID` throughout; the re-set in the templates below is a defensive no-op for the common case.

## Inputs (provided by the caller)

| Name | What it is |
|---|---|
| `issue_id` | Linear issue id (UUID) |
| `issue_identifier` | Human-readable id (e.g. `SAT-123`) |
| `model` / `effort` | Values the orchestrator dispatched this worker at — use as-is, never self-report |
| `outcome` | `success` · `needs-input` · `blocked` |
| `thread_root_id` | Root comment id if answering a specific thread; omit for issue-level handbacks |
| Outcome fields | `summary`, `links` (success) · `question` (needs-input) · `blocked_what`, `blocked_unblock` (blocked) |

**Linear access.** Use the same tool path as `linear-agent-poll` (registered MCP tool → Composio `LINEAR_*` → direct GraphQL via `$LINEAR_API_KEY`).

**Thread placement.** When `thread_root_id` is provided, post via `commentCreate(input: { issueId, body, parentId })` with `body` in variables (not inlined); otherwise top-level via `LINEAR_CREATE_LINEAR_COMMENT` or equivalent.

## Legibility — every comment

Answer first (line 1 = outcome) · one idea per bullet, ≤20 words · **bold 2–4 load-bearing words** per bullet, not whole sentences · no inline walls of code or paths — own line or behind a link · depth lives behind a link (PR, note), not inline · target 5–8 short lines.

## Pick exactly one primary outcome

### Needs input — question answerable with a typed reply

```text
🔴 Needs input — {one-line what you're waiting on}
> question: {the specific question} [model: {m}, effort: {e}] (by Claude)
```

`assigneeId = HUMAN_USER_ID`, `priority = Urgent`, `state = STATE_NEEDS_INPUT` (skip state change if `STATE_NEEDS_INPUT` is `none`). Return `needs-input: {identifier}`.

### Blocked — work stopped; only Tim can unblock it

An external dependency failed (outage, exhausted quota, missing access) or a real-world action only Tim can take stands between here and the finish line — not answerable with a typed reply.

```text
⛔ Blocked — {one-line: what stopped the work}
- What happened: {what was attempted, in order, and where it stopped}
- To unblock: {the specific action/decision Tim must take}
[model: {m}, effort: {e}] (by Claude)
```

`priority = Urgent`, `state = STATE_BLOCKED` (a real introspected workflow state — `none` falls back to Needs-input behavior; if both resolve to `none`, skip state change, issue stays in `STATE_IN_PROGRESS`, marker + Urgent priority are still visible). Return `blocked: {identifier}`.

### Success (default outcome)

`assigneeId = HUMAN_USER_ID`, `state = STATE_IN_REVIEW` (**never** `STATE_DONE` — terminal-state rule below), `priority = normal`. Every success carries two bullets after the headline:

```text
✅ Done — {summary + links}.
- What changed: {short summary}
- Decision needed to move to Done: {none — safe to promote, or the specific check}
[model: {m}, effort: {e}] (by Claude)
```

**Coding PR:** `{links}` must be the PR's full clickable `https://github.com/<owner>/<repo>/pull/<N>` (resolve via `gh repo view --json owner,name` or take the URL `gh pr create` prints) — never a bare `PR #<N>`. Add a `Review on: GitHub PR page` line so Tim knows where the diff lives.

Judgment-bearing work (writing/admin needing Tim's eyes) → `✅ Ready for review —` instead of `✅ Done —`, same bullets, same state.

Return `done: {identifier}`.

## Human-action Todo spin-out (composes with Success; optional)

When the conclusion is "Tim must personally do X in the real world," spin it out as its own `STATE_TODO` issue rather than burying it in the handback comment.

1. **Idempotency check first.** Search for an existing spin-out already linked (`relatedTo`) to the original, or a `STATE_TODO` issue whose description already contains `{identifier}`. Reuse and link if found — never create a duplicate.
2. If none exists: `issueCreate` with `teamId = TEAM_ID`, `stateId = STATE_TODO`, `assigneeId = HUMAN_USER_ID`, `projectId` = original's project (omit if none), `title = "Action (Tim): {imperative action}"`. Description = reasoning, decision/recommendation, why, concrete steps, Markdown link back to the original.
3. `issueRelationCreate` type `related` between spin-out and original. If this fails after the create, retry before proceeding — don't hand back with a dangling unlinked spin-out.
4. **Omit any routing/model/effort label** — `STATE_TODO` keeps it outside both A1 paths (not `STATE_AGENT_QUEUE`, not a floor state), so it's never auto-dispatched; the missing labels are belt-and-suspenders documentation of that.
5. Hand the **original** back through **Success** above, linking the spin-out identifier in the `What changed` bullet. Return `done: {identifier} (spun out {spin-out-identifier})`.

Skip entirely if `STATE_TODO` is `none` — fold the action into the handback comment instead.

## Terminal-state rule

The agent **never** sets `STATE_DONE`, however final the work looks — coding tickets don't merge their own PR either. Only comment wording (`Done —` vs `Ready for review —`) signals confidence; state is always `STATE_IN_REVIEW` for a successful handback. Only Needs-input and Blocked use Urgent priority.
