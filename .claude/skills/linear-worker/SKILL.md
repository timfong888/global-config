---
name: linear-worker
description: Per-issue worker for the Linear agent poller — loads layered context (B1), confirms pending state per-thread (B2), routes to the matching track profile (B3), posts the pickup comment (B4), does the work (B5), self-reviews (B5.5), then calls linear-handback. Callable standalone as /linear-worker SAT-NNN to work one issue without a full poll tick. Load to work a single Linear issue in any track. Dispatched by linear-agent-poll for each issue in the batch, or invoked standalone with /linear-worker SAT-NNN.
---

# /linear-worker — one issue, one turn

You own **exactly the issue handed to you** — do not touch any other issue. Use Composio
Linear tools pinned to `LINEAR_ACCOUNT`. Sign every comment `(by Claude)`.

**Standalone invocation (`/linear-worker SAT-NNN`):** resolve workspace config yourself —
look for `## Agent Poll Configuration` in the active CLAUDE.md, else use Satchel defaults
from the config table in `linear-agent-poll`. Use inherited session model/effort as defaults
for the `[model: …, effort: …]` tag.

**Dispatched by orchestrator:** workspace config, model, effort, id, identifier, and track
are handed in by A3 in `linear-agent-poll` — use them directly.

---

## B1. Load it (layered context — ticket > epic > project > vault > global)

**One round-trip, not three.** `LINEAR_GET_LINEAR_ISSUE` already returns `project` and
`parent` on the issue. Read `assignee`, `description`, `labels`, `comments.nodes`
(chronological), `project { id name description labels }`, and `parent { id identifier title description }`.

```graphql
query IssueWithContext($id: String!) {
  issue(id: $id) {
    id identifier title description
    labels { nodes { name } }
    comments { nodes { id body createdAt user { name } parent { id } } }  # parent id = thread structure — load-bearing for B2 and B5
    project { id name description labels { nodes { name } } }  # description may carry agent-context block; labels/name drive coding-repo resolution (B3)
    parent  { id identifier title description }   # the "epic"
  }
}
```

**`LINEAR_GET_LINEAR_ISSUE` lacks `parent` id on comments** — use `LINEAR_RUN_QUERY_OR_MUTATION`
with the query above whenever you need per-thread reasoning (B2) or to post a nested reply (B5).

**Resolve linked CLAUDE.md pointers.** For each of `project.description` and `parent.description`,
look for a canonical `agent-context` fenced block (schema below); fall back to scanning for an
`obsidian://open?...file=<path>` URI. URL-decode the `file=` param, join to vault root
`~/Documents/remoteObsidian1025`, **canonicalize (resolve `..` and symlinks) and verify it
still falls under that vault root** — if it resolves outside, treat as missing and continue.
Never block the tick on a missing or invalid link.

**Context stack — all layers stack, none are discarded:**

| Layer | Source |
|---|---|
| L0 Global | `~/.claude/CLAUDE.md` — already in the harness |
| L1 Repo / vault | repo or vault `CLAUDE.md` for the cwd — already in the harness |
| L2 Project | `project.description` + linked vault `CLAUDE.md` |
| L3 Epic | `parent.description` + linked `CLAUDE.md` |
| L4 Issue | `issue.description` + `comments` |

When the combined stack is over budget: compact verbose prose only — **never** remove a hard
rule or `rules:` entry from an `agent-context` block. Conflict between layers: more-specific
wins (`ticket > epic > project > vault > global`) — this is a rare tie-breaker, not the
default merge behavior.

**`agent-context` block schema** (appears at top of project/epic descriptions):
````markdown
```agent-context
claude_md: obsidian://open?vault=remoteObsidian1025&file=10-Projects%2FAurora%2FCLAUDE.md
rules:
  - Never push to main; always open a PR.
scope: Aurora GTM — token-optimization positioning
```
````
`claude_md:` = single pointer; `rules:` = hard rules that survive compaction verbatim.

---

## B2. Confirm it's pending & set the mode — per thread, not flat (SAT-480)

A comment's **thread** = its `parent.id` if set, else its own `id`. Threads are single-level.
Evaluate "pending" per thread — **never compare comment timestamps issue-wide**.

**Pending** when any thread has input you haven't addressed:
- You've **never** commented on the issue at all — fresh ask. Pull in newest human comment(s)
  from every existing thread too (don't work from description alone if threads narrow the ask).
- Some thread has a human comment **newer than your most recent `(by Claude)` comment in that
  same thread** — including a thread you've never replied in.

**Already answered** (every thread's newest comment is already yours) → return
`skipped: already answered`. Stop.

**State floor** (secondary auto-resume path only): a newer human reply re-enters the queue
**only** when the issue is in `STATE_IN_REVIEW`, `STATE_NEEDS_INPUT`, or `STATE_BLOCKED`.
Done / Canceled / Backlog / Todo / In Progress are hard-excluded regardless of comment recency.

**Prior-handback requirement** (secondary path only): auto-resume a floor-state thread only
if it already contains a prior `(by Claude)` handback — you're resuming your work, not adopting
a thread the agent never touched.

**Loop breaker — per thread.** Count consecutive `> question:` (Needs-input) handbacks since
your last `✅ Ready for review` / `✅ Done` handback in the thread. If ≥ 3, post:
```text
🔴 Needs input — I've gone {n} rounds without converging; please restate the goal, or move
this to Agent Queue to force another pass. [model: {model}, effort: {effort}] (by Claude)
```
Treat that thread as **parked** — don't auto-resume on a reply that re-litigates the same point.
Only genuinely new direction or an explicit Agent Queue move resumes it.

**No actionable content?** If the newest human reply is pure acknowledgment ("thanks", "looks
good"), post a one-line `(by Claude)` acknowledgment nudging Tim to promote to Done, then hand
back. Don't skip, or the same reply re-fires next tick.

**Reply targets:** record each pending thread — answer each as a nested reply in B5.

**Mode:** Fresh if no prior `> question:` on the issue. Resume if you have one.

---

## B3. Run the profile for your track

Use the track handed to you by the orchestrator. Only if genuinely ambiguous: post a
`> question:`, set `assigneeId` = `HUMAN_USER_ID`, end.

| Track | Profile |
|---|---|
| coding | **Resolve the repo from the issue's Project first (SAT-365):** look up `project.name` in the `CODING_REPO_ROOT` mapping (workspace config). If the Project isn't listed, ask Tim (`> question:`) rather than guessing. State the ticket's **completion condition** as a happy path — primary user-facing flow in plain language — plus the **verifiable test** whose pass/fail proves it holds. Include this in the B4 pickup comment so it's on the record. Then: branch → change → run tests/lint → run `coderabbit review` (clean CodeRabbit is a **hard merge-gate**) → commit → push → open PR with `gh`. **Never push to main.** Output: the PR's **full clickable GitHub URL** — use the template in `linear-handback` (coding-PR success variant). |
| writing | Load the **`agent-writing`** skill (Skill tool) — classify research vs draft, route to the matching skill, post inline (short) or to a linked vault note (long). Output: the draft or vault-note link. |
| admin | Load the **`agent-admin`** skill (Skill tool) — route by sub-type (email/vault/logseq); email is draft-only, never send; vault uses `inbox-triage` + `move-to-obsidian` (PARA) with CHANGELOG logging; LogSeq todos are proposed as a batch and only become Linear Todo issues on explicit approval. Output: Done / Pending Approval / Skipped report. |

**Image capability (any track).** When a ticket needs a generated or edited image, load the
**`capability-image`** skill (Skill tool) and follow its pipeline (generate → download → host →
attach → report cost) — it's a capability, not a fourth track ([SAT-491](https://linear.app/sophia-xyz/issue/SAT-491)).

---

## B4. Start work (both modes)

Post a comment:
- Fresh → `🤖 On it — {track}. [model: {model}, effort: {effort}] (by Claude)`
- Resume → `🤖 Resuming — got your reply. [model: {model}, effort: {effort}] (by Claude)`

`{model}` / `{effort}` are the values handed in by the orchestrator — fill from those, not
from self-introspection.

**Coding track only:** append the happy-path + verifiable-test statement from B3 to this
comment — e.g. "Happy path: {plain-language flow}. Proof: {test name/path}."

`LINEAR_UPDATE_ISSUE`: set `stateId` = `STATE_IN_PROGRESS` only — **do not set `assigneeId`**.
Drop any stale `agent-ready` / `agent-needs-human` labels from `labelIds`.

never block the tick on it.

---

## B5. Do the work

Run the matching profile using the full layered context from B1 (project/epic descriptions,
resolved `CLAUDE.md` rules, advisory snippets). Compact only verbose prose; never compact a
hard rule.


**Threaded replies (SAT-480).** When answering a specific pending thread from B2, post as a
nested reply — not a new top-level comment:
- `LINEAR_CREATE_LINEAR_COMMENT` has **no** `parentId` parameter. For threaded replies use
  `LINEAR_RUN_QUERY_OR_MUTATION` running `commentCreate(input: { issueId, body, parentId })`,
  passing `body` via GraphQL variables.
- `parentId` = the thread's **root** comment id (the human comment's `parent.id`, or its own
  `id` if it started the thread). Threads are single-level — `parentId` is always the root.
- Answer each pending thread in its own nested reply. Issue-level status comments stay top-level.

---

## B5.5. Self-review gate

Before calling `linear-handback`, do one lightweight check: re-read the ticket's acceptance
criteria / completion condition (coding: the happy-path + verifiable-test from B3) and the
track's profile rules, then confirm your B5 output satisfies them. No new tooling, one pass.

- **Pass** → call `linear-handback` with the Success path.
- **Fail** → either close the gap yourself (iterate on B5), or call `linear-handback` with
  the Needs-input or Blocked path instead.

---

## Handback

Load the **`linear-handback`** skill (Skill tool) and execute it with the issue's full
resolved context: `id`, `identifier`, `track`, `model`, `effort`, `HUMAN_USER_ID`, `TEAM_ID`,
and all state IDs (`STATE_IN_REVIEW`, `STATE_NEEDS_INPUT`, `STATE_BLOCKED`, `STATE_TODO`)
from workspace config.

> **State-transition ownership:** `linear-handback` owns all Linear state transitions and
> `assigneeId` writes. Track skills (`agent-writing`, `agent-admin`) describe *output
> classification* (short/long/image, Done/Pending/Skipped) — their internal "State → In Review"
> notes are outcome labels, not direct Linear calls. The actual `LINEAR_UPDATE_ISSUE` with
> `stateId` always comes from `linear-handback` after the track skill returns.
