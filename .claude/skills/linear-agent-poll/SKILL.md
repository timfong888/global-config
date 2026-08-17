---
name: linear-agent-poll
description: One tick of the Linear agent poller — select a batch of pending issues queued in the "Agent Queue" workflow state, dispatch one subagent per issue to work them in parallel (non-coding fan-out + at most one coding), and hand each back via workflow state (never by reassigning). Workspace-agnostic — resolves IDs from the invoking project's CLAUDE.md, defaulting to Satchel.
whenToUse: Run when the user wants to poll and process pending Linear issues from the Agent Queue state. Use /linear-agent-poll or when asked to run a tick of the poller.
---

# /linear-agent-poll — one poll tick

You are the **orchestrator** in a `/loop`. Run **one tick**: select a batch of
pending issues, dispatch one subagent per issue to work them **in parallel**, then
stop.

## Workspace configuration (resolve FIRST, before any Linear call)

This command is workspace-agnostic. Resolve these variables before doing anything:

1. Look for an `## Agent Poll Configuration` block in the **CLAUDE.md of the project
   you were invoked from** (the active working directory). If present, use its values.
2. If no such block exists, use the **Satchel defaults** in the table below.

| Variable | Meaning | Satchel default |
|---|---|---|
| `LINEAR_ACCOUNT` | Composio Linear connection to pin (`--account` / `account:`) | `satchel-linear` |
| `TEAM_ID` | Linear team id | `88661a7f-d07e-4590-9724-b8f69e30556e` |
| `TEAM_KEY` | Team prefix for identifiers | `SAT` |
| `WORKSPACE_SLUG` | Slug for cross-issue links `linear.app/<slug>/issue/<KEY>-###` | `sophia-xyz` |
| `STATE_AGENT_QUEUE` | **The turn signal.** A dedicated `unstarted`-type team workflow state, positioned before Todo — an issue in this *exact* state is queued for the agent; nothing else means that. **Every workspace using this command must create its own "Agent Queue" team state** (Settings → Teams → \<team\> → Workflow) and set its own id here; there is no shared cross-workspace id. | `73be9b83-4bd2-4ef1-97a7-0ff6e6ff5339` (Satchel's "Agent Queue") |
| `AGENT_USER_ID` | **Deprecated — no longer read.** The underlying Linear seat can be retired once no workspace `CLAUDE.md` still references it. | `41903248-8c2b-41e4-a7fb-f00f4feb9ba4` (@agentfong) |
| `HUMAN_USER_ID` | Tim's user — **informational only now.** The poller no longer writes this to `assigneeId` for turn-taking purposes; assignee stays on the human permanently (see B4/B6). | `aa3fb002-ba6c-440f-8837-cc5c92a3c748` (@timfong888) |
| `STATE_IN_PROGRESS` | "started" state id — set here when the agent picks a queued issue up out of `STATE_AGENT_QUEUE` | `8439671f-0e5d-4a08-ba98-d3bf5b758d16` |
| `STATE_IN_REVIEW` | state for **every successful handback** — deterministic or judgment-bearing alike (see B6 terminal-state rule: the agent never self-certifies Done). **Also an open-loop / auto-resume state (SAT-525):** from here, Tim just **replies to the agent's handback comment** and the next tick auto-resumes it (secondary path, A1+B2) — moving the state back to `STATE_AGENT_QUEUE` still works as a manual override but is no longer required. | `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` (In Review) |
| `STATE_DONE` | "completed" state id — **never set by the agent itself**; Tim promotes a ticket to this state manually once he's reviewed it | `299e627d-3989-40c4-8aea-b9d56209fa39` |
| `STATE_NEEDS_INPUT` | state to set on a needs-input handback; if `none`, leave the state unchanged | `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` (In Review) |
| `STATE_BLOCKED` | state for a **Blocked handback** (SAT-553, B6) — work stopped by an external dependency or a real-world action/decision only Tim can take, as opposed to a question he can answer inline (that's Needs-input). Visually distinct from In Review on the board, which is the whole point: Tim can tell "review my finished work" apart from "I'm stuck, unblock me" at a glance. **Also a floor state for auto-resume** (A1/B2): Tim replies with the unblocking action or decision and the next tick resumes it. Must be a **real team workflow state** — introspect `team { states { nodes { id name type } } }` to find it, never invent an id; if the team has no Blocked state, set `none` and the Blocked path falls back to the Needs-input state behavior (the `⛔ Blocked` comment marker still distinguishes it). | `f68b9fad-0d13-4397-b1e0-97f6e7216e52` (Satchel's "Blocked", `started`-type — introspected, not guessed) |
| `STATE_TODO` | the team's plain `unstarted` **Todo** state — the landing state for a **human-action Todo spin-out** (SAT-553, B6): a new issue for something Tim must execute personally. Deliberately outside *both* A1 paths (not `STATE_AGENT_QUEUE`, not a floor state), so a spin-out is never auto-dispatched to any agent. If `none`, skip spin-outs and fold the requested action into the handback comment instead. | `4dfa455d-9248-4b2b-b3de-4d0d343efe21` (Todo) |
| `ROUTING_LABELS` | routing-label ids (coding/writing/admin); if `none`, infer the track from the description | agent-coding `b4c6b47e-0ded-4468-a68c-4d3a5b58ec33` · agent-writing `79adef88-4350-48c2-a1da-31137a2dfbc8` · agent-admin `a1a9437b-8c75-4cd5-ba6b-5c1fb4443f00` |
| `MODEL_LABELS` | **Optional per-ticket model override (SAT-454).** Labels under the `models` parent group let Tim be explicit about which model tier to dispatch a ticket at, instead of leaving it to the orchestrator's judgment call. Label *names* carry a version-ish suffix that isn't the literal string the Agent tool's `model:` parameter expects, so this maps label name → actual model value; if `none`/not present on a candidate, fall back to today's default (Sonnet + judgment-based escalation per the global CLAUDE.md Model Tier Selection convention) | `sonnet 5` → `sonnet` · `opus 4.8` → `opus` · `fable 5` → `fable` · `haiku` → `haiku` |
| `EFFORT_LABELS` | **Optional per-ticket reasoning-effort override (SAT-469).** Labels under the `agent-effort` parent group (named `agent-effort`, not `effort` — Linear reserves the literal label name `effort`) let Tim be explicit about which reasoning effort to dispatch a ticket at, instead of leaving it to the orchestrator's judgment call — same mechanism as `MODEL_LABELS`, just for the Agent tool's `effort:` parameter. Label names are already the literal values the `effort:` parameter expects, so the mapping here is identity, not a translation; if `none`/not present on a candidate, fall back to today's default effort | `low` → `low` · `medium` → `medium` · `high` → `high` · `xhigh` → `xhigh` · `max` → `max` |
| `CODING_PROJECT_LABEL` | **Project-level** label marking a Linear Project as coding-track — it has its own dedicated repo and its issues run the coding profile. A Project without it isn't coding-track, whatever labels its individual issues carry. **Not yet created in the workspace** — until Tim adds it, treat every Project referenced in `CODING_REPO_ROOT` below as coding-track. | `coding-project` (label name; id TBD) |
| `CODING_REPO_ROOT` | **Per-Project, not one shared repo (SAT-365).** A coding ticket's repo is whichever one its *Linear Project* owns — resolved by looking up the issue's `project.name` in this mapping, same pattern as `ROUTING_LABELS` above. Add a row here each time a new coding Project is onboarded. | **No portable default — must be set per workspace** in the `## Agent Poll Configuration` block (e.g. `Claude and Local Agentic System` → `/path/to/repo`). |

All Linear calls below use the Composio Linear tools pinned to `LINEAR_ACCOUNT`.
Comments post under Tim's account, so **sign every agent comment `(by Claude)`**.
That signature is how you tell *your* comments from Tim's — rely on it below.

When a comment references another issue in the same workspace, write it as a clickable
Markdown link — `[<TEAM_KEY>-123](https://linear.app/<WORKSPACE_SLUG>/issue/<TEAM_KEY>-123)`
— never a bare `<TEAM_KEY>-123` (plain identifiers posted via the API don't auto-link).

**Every posted comment also carries a model/effort tag** — `[model: <model>, effort:
<effort>]` right before the `(by Claude)` signature (see B4 and B6 templates). The
**orchestrator** fills these in, not the worker: hand the model and effort it's
dispatching at down alongside the issue `id`, `identifier`, and `track` in A3, since
that's the only place these values are reliably known — a dispatched worker can't
always introspect its own effort setting, but the calling context always knows
exactly what it requested for that dispatch.

**Current state (SAT-408 audit):** today every dispatch runs at the inherited session
default — Sonnet, per the global CLAUDE.md Model Tier Selection convention — with no
explicit per-ticket override. That guidance (Opus for steered high-stakes work, Fable
for long-horizon autonomous work) is documented but not yet actively varying dispatch
choices in this poller. The tag above makes that visible on every Linear thread going
forward, so Tim (or a future audit) can read what was actually used straight off the
thread instead of inferring it. Actually varying model/effort by task complexity —
e.g. escalating a multi-file coding build to a higher tier — is optional future work;
this change only makes the existing (currently constant) choice visible and reportable.

**Primary trigger: the issue's workflow state is `STATE_AGENT_QUEUE`.** Workflow state is
the turn signal for a **fresh start**, not assignee — an issue sitting in that exact state
is queued for the agent. Tim starts a *new* ask by moving the issue's state to **Agent
Queue**. **Resuming an in-flight thread is automatic (SAT-525):** once you've handed a
ticket back to In Review / Needs-input, Tim just **replies to your comment** and the next
tick picks it up again — the act of responding to an agent handback *is* the resume signal,
so he no longer has to move the state back to Agent Queue for the back-and-forth (that
manual move still works as an override). You hand each ticket back by moving the state to
`STATE_IN_REVIEW` (or `STATE_BLOCKED`, for the SAT-553 Blocked path — see B6). Your queue is
every issue in `STATE_AGENT_QUEUE` (primary path) **plus** every
`STATE_IN_REVIEW` / `STATE_NEEDS_INPUT` / `STATE_BLOCKED` issue carrying a human reply newer
than your last `(by Claude)` comment **in a thread you've already handed back at least once**
(secondary auto-resume path — the prior-handback and loop-breaker gates live in A1 + B2; a
floor-state issue the agent never commented on is not queue-eligible this way). Assignee
stays on the human user throughout and
plays no role in this signal — the agent never needs its own paid Linear seat. Never ask
Tim to juggle labels.

**Secondary trigger — auto-resume from a reply (SAT-525).** You also pick up an issue that
**isn't** in `STATE_AGENT_QUEUE` when it sits in an **open-loop handback state**
(`STATE_IN_REVIEW`, `STATE_NEEDS_INPUT`, or `STATE_BLOCKED` — the **state floor**) and Tim
has left a reply newer than your last `(by Claude)` comment in a thread where you'd already
handed back once before (see the prior-handback requirement in B2 — this never adopts a
floor-state thread the agent never touched). Treat **In
Review as an open
loop**: a reply that arrives while the ticket is still parked there means "not done yet,
here's my input." This deliberately covers *both* cases Tim flagged — an explicit
`> question:` he answers, **and** a `✅ Ready for review` handback (e.g. a set of mock-ups) he
replies to with a new request ("give me another set") — both are "here's where the work
stands, here's my input," and both re-enter the queue with no manual state move. When he's
actually satisfied he moves the ticket to Done (or to Agent Queue for genuinely new scope),
which floors it out of auto-resume. Pick one up this way by moving its state directly to
`STATE_IN_PROGRESS` (you're picking it up immediately, no need to stage through Agent Queue).
The state floor + the per-thread loop breaker in B2 are what stop this from re-queuing
Done / Canceled / Backlog tickets or looping forever. Don't touch assignee either way. Never
assign to `@linear`: that hands the work to Linear's own hosted agent (it can start its own
coding session), not this local poller — this poller is triggered by workflow state, not by
any Linear user account, so there is no "agent user" for it to be assigned to anymore.

> Turn-taking labels `agent-ready` / `agent-needs-human` are **deprecated** — workflow
> state (`STATE_AGENT_QUEUE`) is the turn signal now, replacing both labels and (as of
> this change) assignment. Don't add the labels back; clear a stale one if you see it.
> The old **`@claude` comment nudge is also retired** (SAT-525): Tim removed it because it
> doesn't autocomplete unless registered as a real agent user, and the reply auto-resume
> path above now covers the same "quick mid-thread nudge" case — any reply resumes, no token
> required. Don't reintroduce an `@claude`-token candidate query.

---

## Part A — Orchestrator (the tick)

### A1. Find candidates
Your queue = issues in the *exact* `STATE_AGENT_QUEUE` state (account `LINEAR_ACCOUNT`):
```graphql
query { issues(filter: { team: { id: { eq: "<TEAM_ID>" } },
                         state: { id: { eq: "<STATE_AGENT_QUEUE>" } } }, first: 50) {
  nodes { id identifier createdAt } } }
```
**This is a single-state equality match, not a `state.type` range — that distinction is
load-bearing.** Agent Queue is its own state, not a member of a broader `unstarted`/`started`
bucket. That matters because **In Review is also a `started`-type state** (used for every
handback, see B6): if this filter instead matched on `state.type in ["unstarted",
"started"]`, every handed-back In-Review issue would match it too and re-enter the queue
forever. Matching `state.id` exactly against `STATE_AGENT_QUEUE` avoids that — Backlog, Todo,
In Progress, In Review, Done, and Canceled all fail this **primary** filter unconditionally,
regardless of type, until Tim explicitly moves an issue into Agent Queue. That exact-match
keeps the primary path clean — In-Review handbacks never re-enter the *primary* queue forever.
Auto-resume (below) reaches In-Review issues on purpose, but through a **separate** query with
its own guards (state floor + B2 loop breaker), so this invariant is preserved, not weakened:
the primary query stays a single-state equality match and never widens to a `state.type` range.

**Secondary path — auto-resume from a reply (SAT-525).** Also catch any issue *not* in
`STATE_AGENT_QUEUE` but sitting in the **state floor** (`STATE_IN_REVIEW` or
`STATE_NEEDS_INPUT`) that carries a human reply newer than your last `(by Claude)` comment in
some thread. There is **no** server-side filter for "newer than my last reply per thread" — the
`(by Claude)` marker is body text, not a field, because comments post under Tim's account — so
fetch the candidate set by state and reason per-thread client-side (the exact SAT-480 test,
reused in B2). Fetch recently-touched issues in the floor states, newest first:
```graphql
query { issues(filter: { team: { id: { eq: "<TEAM_ID>" } },
                         state: { id: { in: [<FLOOR_STATE_IDS>] } } },
               first: 50, orderBy: updatedAt) {
  nodes { id identifier updatedAt } } }
```
`<FLOOR_STATE_IDS>` = the **configured** floor-state ids only: build it from `STATE_IN_REVIEW`,
`STATE_NEEDS_INPUT`, and `STATE_BLOCKED` (SAT-553), **dropping any that resolve to `none`** and
**de-duplicating** when two share an id (as in Satchel, where the first two are both "In
Review" — the list collapses to that id plus Blocked's). Never interpolate a literal `none`
into the filter. If *no* floor state is configured,
skip the secondary query entirely — only the primary Agent-Queue path runs.
`first: 50, orderBy: updatedAt` is a deliberate bound, not a bug: any new reply bumps its
issue's `updatedAt` to the top, so the 50 most-recently-touched floor-state issues always
include every ticket with a fresh unaddressed reply — the same `first: 50` cap the primary
query uses, no pagination needed. These are *candidates* only: A2/B2 then keep just the ones
where some thread has a human comment newer than your last `(by Claude)` reply there —
**and that thread already contains a prior `(by Claude)` handback of yours** (you're resuming
a handback you made, not adopting a human-only thread the agent never touched; the B2 "fresh
ask — never commented at all" branch belongs to the *primary* Agent-Queue path, never to this
secondary reply path) — **and** the loop breaker hasn't tripped. Candidates = the union of the
two queries. If both empty → say "Queue empty", **end the tick**.

### A2. Select the batch (oldest-first, capped)
Walk candidates **oldest-first** (by issue `createdAt`, or oldest unaddressed human reply for
the secondary auto-resume path). For each, `LINEAR_GET_LINEAR_ISSUE` and determine:
- **Pending?** — apply the B2 rule. Skip anything not pending (already answered).
  **Never use `comments(last: N)` for this check, for any N — not even for a "quick peek."**
  On this Composio Linear connection `last:N` has repeatedly (8 confirmed recurrences) either
  returned a wrong/stale-ordered slice outright, or been correctly ordered but too narrow for
  a busy thread — both look identical from here ("newest visible comment is unanswered") and
  both cause a false-pending dispatch on an issue that's actually already resolved. Comments
  come back oldest-first, so a bounded `comments(first: 20)` only guarantees the true newest
  comment on threads with ≤20 total — for a busier thread, keep paging with `after:
  pageInfo.endCursor` until `hasNextPage` is `false`, then read the actual newest-`createdAt`
  node off that last page. This screening is a cheap pre-filter,
  not the authoritative gate: every dispatched worker independently re-runs the full B2 check
  against a fresh fetch before writing anything (that's what has caught every past false
  positive with zero duplicate-comment fallout) — but this screen still saves dispatching
  workers onto issues that are obviously already closed out.
- **Track** — routing label if `ROUTING_LABELS` is configured and present on the issue, else
  infer from the description/request (coding · writing · admin).
- **Model override (SAT-454)** — if `MODEL_LABELS` is configured, check the issue's labels for
  one under the `models` parent group (e.g. `sonnet 5`, `opus 4.8`, `fable 5`). If present,
  translate it via the `MODEL_LABELS` mapping to get the actual model value (e.g. `fable 5` →
  `fable`) and carry that forward as this issue's dispatch model — it **overrides** the default
  Sonnet/judgment call for A3. If no `models`-group label is present, leave the model unset
  here; A3 falls back to its usual default/judgment behavior, unchanged from today.
- **Effort override (SAT-469)** — if `EFFORT_LABELS` is configured, check the issue's labels for
  one under the `agent-effort` parent group (e.g. `low`, `medium`, `high`, `xhigh`, `max`). If
  present, translate it via the `EFFORT_LABELS` mapping to get the actual effort value (identity
  mapping — `high` → `high`) and carry that forward as this issue's dispatch effort — it
  **overrides** the default effort for A3. If no `agent-effort`-group label is present, leave the
  effort unset here; A3 falls back to its usual default behavior, unchanged from today.

Fill two slots, stopping when both are full or candidates run out:
- **Non-coding** (writing + admin): up to **3**.
- **Coding**: up to **1**.

The 1-coding cap means at most one subagent touches git, so there's no worktree collision.
Parallel coding (multiple coding issues, isolated worktrees) is out of scope here. If
nothing is pending → "Queue empty", end the tick.

### A3. Dispatch the batch in parallel
Spawn **one subagent per selected issue, concurrently** (a single message with multiple Agent
dispatches). Each subagent runs **Part B** for exactly its one issue; hand it the issue `id`,
`identifier`, `track`, the `model`/`effort` you're dispatching it at, and the resolved
workspace config. **Model selection:** if A2 found a `models`-group label for this issue, use
that translated model **directly** — it overrides the default/judgment call, no further
reasoning needed. Otherwise, fall back to today's behavior: the inherited session default —
Sonnet — unless you've explicitly overridden it by judgment for that call (global CLAUDE.md
Model Tier Selection convention). Wait for all to finish, then collect each worker's one-line
result.

*Known limit:* two **admin** workers that both append to `CLAUDE-CHANGELOG.md` can race on the
file. Rare with this batch size; acceptable for now — don't add locking.

**Detached-dispatch primitive (SAT-509).** `scripts/dispatch-worker.sh` can launch an
arbitrary worker command as a fully detached background OS process and durably record it —
`{issue_id, identifier, pid, started_at, workspace}` — to a JSONL registry (default path
`state/worker-registry.jsonl`) before returning, without waiting for the worker to finish.
See the script's header and `tests/test-dispatch-worker.sh` for the exact contract and
behavioral guarantees. The **reader** side is `scripts/inspect-in-progress.sh` (SAT-558): it
reports, per recorded worker, whether the pid is still ALIVE, how long it's been running
(LONG-RUNNING past a threshold), or is LIKELY-DEAD — the visibility that was missing when a
ticket sat In Progress for hours with no way to tell "slow" from "silently died". This tick
still dispatches via the in-session Agent tool and waits for every worker per A3 above —
rewiring the tick itself to shell out through this primitive instead (so a tick can return
before its workers finish, shrinking the watchdog window this file's A4/timeout notes
describe) is tracked as follow-on work, not yet done here.

### A4. Self-pacing (when run via `/loop` with no interval)
Schedule the next wake by outcome:
**Worked ≥1 issue** → ~2 min · **Empty, 1st** → ~4 min · **Empty 2–3×** → ~10 min · **Empty 4+×** → ~30 min.

---

## Part B — Per-issue worker (one subagent, one issue)

You own **exactly the issue handed to you** — do not touch any other issue. Use Composio Linear
tools pinned to `LINEAR_ACCOUNT`. Sign every comment `(by Claude)`; never post as Tim.

### B1. Load it (layered context — ticket > epic > project > vault > global)
The ticket is a *delta* against an assumed project baseline. To execute correctly, the
worker must load not just the issue but the **project** and **epic (parent issue)** context
and their rules. Assemble a 5-layer context stack, least- to most-specific, and prepend it
to your task input. (Design: vault note `02-AI-Tools/linear-agent-system/SAT-365-context-layering.md`.)

**1 — Fetch issue + project + epic in one call.** `LINEAR_GET_LINEAR_ISSUE` already returns
`project` and `parent` on the issue, so this is **one round-trip, not three**. Read:
`assignee`, `description`, `labels`, `comments.nodes` (chronological), **plus**
`project { id name description labels }` and `parent { id identifier title description }`
(the epic). Grab the Project's `labels` too — that's what tells you whether it's a
coding-track Project (`CODING_PROJECT_LABEL`) and, along with `project.name`, is what the
coding profile keys its repo lookup on (B3, SAT-365).
The GraphQL shape:
```graphql
query IssueWithContext($id: String!) {
  issue(id: $id) {
    id identifier title description
    labels { nodes { name } }
    comments { nodes { id body createdAt user { name } parent { id } } }  # comment `parent` id = thread structure — load-bearing for B2 per-thread pending and B5 nested replies
    project { id name description labels { nodes { name } } }  # description may carry the agent-context block / CLAUDE.md pointer; labels/name drive coding-repo resolution (B3)
    parent  { id identifier title description }   # the "epic", same convention
  }
}
```
**Comment threads need the raw query.** `LINEAR_GET_LINEAR_ISSUE`'s fixed shape returns
`comments.nodes` **without** each comment's `parent` id, so it can't tell you thread
structure. When you need per-thread reasoning (B2) or to post a nested reply (B5), fetch
the comments through `LINEAR_RUN_QUERY_OR_MUTATION` with the query above (which selects
`comments.nodes[].parent { id }`) rather than the fixed action.

**2 — Resolve any linked `CLAUDE.md`.** For each of `project.description` and
`parent.description`, look for a canonical **`agent-context` fenced block** (schema below);
fall back to scanning for an `obsidian://open?...file=<path>` URI or a vault-relative
`*CLAUDE.md` path. URL-decode the `file=` param, join it to the vault root
`~/Documents/remoteObsidian1025`, then **canonicalize the result (resolve `..` and
symlinks) and verify it still falls under that vault root** — if it resolves outside
(a path-escape attempt via `../`), treat it as a missing link rather than reading it.
Only then `Read` the file, **once**. If the pointer is missing, escapes the vault root,
or the file itself is missing, fall back to the raw description text for that layer and
continue — **never block the tick on a missing or invalid link**.

**3 — Assemble the stack (stacked, then compacted).** Layers, least- to most-specific:

| Layer | Source | How loaded |
|---|---|---|
| L0 Global | `~/.claude/CLAUDE.md` | already in the harness |
| L1 Repo / vault | repo or vault `CLAUDE.md` for the cwd | already in the harness |
| L2 Project | `project.description` **+** its linked vault `CLAUDE.md` | **fetched in B1.1, resolved in B1.2** |
| L3 Epic | `parent.description` **+** its linked `CLAUDE.md` | **fetched in B1.1, resolved in B1.2** |
| L4 Issue | `issue.description` + `comments` | fetched in B1.1 |

**All layers are additive and co-present — they stack, they don't clobber.** The Project
carries the big-picture context, the Epic adds mid-granularity (still wide) context, the
Issue is the most specific — and **none is discarded for being less specific.** Most content
across layers isn't contradictory; it's complementary, and it all sits in context together.

**When the combined stack is too large for the budget, compact it** — the way Claude Code's
own `/compact` works: condense verbose or redundant prose, merge overlapping points, drop
duplicated restatement. **Compaction must never remove a hard rule.** Hard rules (imperative
`never` / `always` / `must` lines and any `rules:` entry from an `agent-context` block)
survive compaction **verbatim**; only descriptive/narrative prose is eligible for compaction.

**Conflict is the exception, not the merge mechanism.** If two layers state genuinely
contradictory *hard rules* on the same point (a real contradiction, not just differing
emphasis or scope), the **more-specific layer's rule wins for that one conflict**
(`ticket > epic > project > vault > global`). This is a rare tie-breaker for actual
contradictions — the default is that everything stacks and is retained.

**4 — Advisory knowledge tier (RAG, optional).** For long-tail reference background (large
design notes, prior decisions) too big to load wholesale, you may query the local
`document-mcp` `search_documents` keyed on the ticket text (title + description) and inject
the top-k snippets as **supporting** context only. **Subordinate to rules:** never let a
retrieved snippet override a rule loaded deterministically from a project/epic `CLAUDE.md`.
Keep the index fresh (`reindex_document`) or the knowledge layer under-retrieves.

**5 — Token efficiency.** Fetch `project`+`parent` once per issue (the B1.1 call); `Read`
each linked `CLAUDE.md` once and hold it for the whole issue (don't re-read per sub-step);
prefer the track-relevant sections of a large `CLAUDE.md`; within a tick, cache by
`project.id` / `parent.id` so two issues under the same project don't both re-read it.

**Authoring convention (`agent-context` block).** So resolution is deterministic, not
prose-parsing. Project and epic descriptions carry a fenced block at the top:
````
```agent-context
claude_md: obsidian://open?vault=remoteObsidian1025&file=10-Projects%2FAurora%2FCLAUDE.md
rules:
  - Never push to main; always open a PR.
  - All external postings signed "(by Claude)".
scope: Aurora GTM — token-optimization positioning
```
````
`claude_md:` is the single pointer (obsidian URI **or** vault-relative path); `rules:` are
hard rules binding every issue in that project/epic — they stack additively with every other
layer's rules and **survive compaction verbatim**; free prose below the block is context for
the LLM and **is** eligible for compaction when the stack is over budget. The same block
works at project and epic level.

### B2. Confirm it's pending & set the mode — **per comment thread, not flat (SAT-480)**
Linear comments are **threaded**: each comment carries a `parent` id (fetched in B1.1). A
comment's **thread** is its `parent` id if it has one, else its own id — a top-level comment
is the root of its own thread, and Linear threads are single-level (a reply's `parent` is
always the thread root, never another reply). Evaluate "pending" **per thread**, comparing
timestamps thread-by-thread — **not** with one flat newest-comment-on-the-issue comparison.
That flat comparison is the SAT-480 bug: a human reply inside an *older* thread was wrongly
treated as already-answered whenever any *newer, unrelated* `(by Claude)` comment existed
elsewhere on the issue, so nested replies silently got no response.

For each thread, find your most recent `(by Claude)` comment **in that same thread** (match
`parent`; treat a `[by Claude]` bracket variant the same as `(by Claude)`).
- **Pending** when *any* thread has input you haven't addressed:
  - you've **never** commented on the issue at all — fresh ask; use the description for
    background, but also pull in the newest human comment(s) from every thread already on the
    issue (Tim may have elaborated before you ever picked it up) — don't work from the
    description alone if later comments narrow or redirect the ask; **or**
  - some thread has a human comment **newer than your most recent `(by Claude)` comment in
    that same thread** — including a human-started thread you've never replied in. Never
    compare a human reply against your newest comment issue-wide; only against your newest
    comment *in its own thread*.

  If every thread's newest comment is already yours (nothing newer in any thread) → **stop**,
  return `skipped: already answered`. (B4 moves the state out of `STATE_AGENT_QUEUE` as soon
  as you pick an issue up, so an already-answered issue normally isn't sitting in the queue
  at all — see the auto-resume gesture below for how it gets back in.)
- **State floor (SAT-525) — applies to the secondary auto-resume path only.** A newer human
  reply re-enters the queue **only** when the issue is currently in `STATE_IN_REVIEW`,
  `STATE_NEEDS_INPUT`, or `STATE_BLOCKED` (the open-loop handback states — Blocked joined the
  floor with SAT-553: Tim's reply carrying the unblocking action or decision is exactly the
  resume signal). If the issue is in **Done, Canceled, Backlog, Todo, or In Progress**, a
  stray reply does **not** auto-resume it — those are hard-excluded
  regardless of comment recency. (That Todo exclusion also covers the SAT-553 human-action **Todo spin-outs** from
  B6 by construction: they live in `STATE_TODO`, so commenting on one never dispatches an
  agent.) (The primary path is unaffected: an issue actually
  sitting in `STATE_AGENT_QUEUE` is always pending-eligible per the rule above.) This is why
  "any reply resumes it" is safe: the moment Tim is satisfied he moves the ticket to Done (or
  to Agent Queue for genuinely new scope), which drops it below the floor.
- **Prior-handback requirement (SAT-525) — secondary path only.** Auto-resume a floor-state
  thread only if it **already contains a prior `(by Claude)` handback of yours** — you're
  resuming a handback you made, not adopting a floor-state thread the agent never touched
  (e.g. Tim manually parks an issue in In Review and comments on it). The "fresh ask — never
  commented at all" branch of the pending rule above stays exclusive to the **primary**
  Agent-Queue path; it never triggers a secondary auto-resume.
- **Loop breaker (SAT-525) — per thread, progress-aware; evaluated here in B2, not A1.** A1's
  secondary query does **not** filter on question count (it only fetches floor-state issues by
  `updatedAt`), so this check always runs *after* candidate selection and the parking handback
  below is always reachable. Before auto-resuming a thread, count your **consecutive
  `> question:` (Needs-input) handbacks in it since your last `✅ Ready for review` / `✅ Done`
  handback** (or since the thread began). A Ready-for-review or Done handback **resets** that
  count — forward progress like a fresh set of mock-ups is *never* throttled, so multi-round
  iteration keeps working. If the count is already **≥3**, you're likely stuck misreading the
  same reply: don't silently auto-resume again. Post one `🔴 Needs input — I've gone {n} rounds
  without converging; please restate the goal, or move this to Agent Queue to force another
  pass. [model: {model}, effort: {effort}] (by Claude)` — **that parking comment is itself the
  persisted parked marker** (it's now the newest comment in the thread, so the thread reads as
  answered): treat the thread as **parked** and don't auto-pick it up again on a reply that
  just re-litigates the same point; only genuinely new direction or an explicit move to Agent
  Queue resumes it. (Note: each auto-resume already requires a *fresh* human reply — the
  agent's own reply becomes the newest comment and clears "pending" — so a runaway with no
  human in the loop can't happen; this cap only guards a human-fed misread loop.)
- **Reply targets:** record the specific pending thread(s) — you answer **each** as a nested
  reply inside its own thread (B5), not as one new top-level comment.
- **No actionable content?** If the newest human reply in a floor-state thread is pure
  acknowledgment with **no** request or correction (e.g. "thanks", "looks good"), don't invent
  work: post a one-line `(by Claude)` acknowledgment (so your comment becomes newest and the
  thread stops re-triggering every tick) that nudges Tim to promote to Done when he's ready,
  then hand back. Don't skip without commenting, or the same reply re-fires on the next tick.
- **Mode:** *Fresh* if you have no prior `(by Claude)` `> question:` on the issue · *Resume* if you do.
- **Auto-resume gesture (SAT-525):** there is no agent assignee to reassign to anymore —
  assignee never leaves the human user (see B4/B6). Tim resumes an issue simply by **replying
  to your handback comment** while it's in the state floor; the next tick's secondary path
  (A1) detects the reply (newer than your last `(by Claude)` comment in that thread) and picks
  it up. The detection is **date-scoped by your last handback** — "newer than my last
  `(by Claude)` reply in this thread" is exactly the last-handoff timestamp comparison — and
  authorship is read from the `(by Claude)` **body marker**, not Linear's author field (every
  comment posts under Tim's account). Moving the state back to Agent Queue still works as a
  manual override, but is no longer required for the back-and-forth.
- **Task input:** the newest human comment(s) **in each pending thread** since your last
  action there, plus the description for background (and your prior question, on resume).

### B3. Run the profile for your track
Use the **track handed to you** by the orchestrator. Only if it's genuinely ambiguous, post a
`> question:` asking which, set `assigneeId` = `HUMAN_USER_ID`, and end.

| Track | Profile |
|---|---|
| coding | **Resolve the repo from the issue's Project first** (SAT-365): each coding-track Project — flagged with `CODING_PROJECT_LABEL` — has its *own* repo. Look up `project.name` in the `CODING_REPO_ROOT` mapping (workspace config, above) to get this issue's repo; if the Project isn't listed, treat it as a config gap and ask Tim (`> question:`) rather than guessing a path. The ticket's work is a branch within *that* Project's repo — not a separate per-ticket repo, and not one repo shared across all coding Projects. Before branching, state the ticket's **completion condition** as a happy path — the primary user-facing flow, in plain language, plus the **verifiable test** (existing or new) whose pass/fail proves it holds. If the ticket already states its condition that way, restate it in your own words; if it's vague or purely technical/internal, reframe it as a happy path yourself from the description — don't block on this, it sharpens framing rather than gating work. Say it in the B4 "On it" comment so it's visible, not just an internal step. Then branch → change → run tests/lint → run `coderabbit review`; if it reports findings, apply fixes and re-run until clean → commit → push → open a PR with `gh`. **Never push to main.** A clean CodeRabbit review is a **hard merge-gate requirement**, same as tests/lint — not optional. Apply the Karpathy guidelines throughout. **Output:** the PR's **full clickable GitHub URL** (never a bare `PR #<N>`) — the **B6 coding-PR handback template** is the single source of truth for its exact shape and how to resolve `<owner>/<repo>`, so follow that. *(Parallel/gated industrial coding is out of scope — [SAT-364](https://linear.app/sophia-xyz/issue/SAT-364).)* |
| writing | Load the **`agent-writing`** skill (Skill tool) — classify research vs draft, route to the matching skill, post inline (short) or to a linked vault note (long). **Output:** the draft or a vault-note link. |
| admin | Load the **`agent-admin`** skill (Skill tool) — route by sub-type (email/vault/logseq); email is Gmail **draft-only, never send**; vault uses `inbox-triage` + `move-to-obsidian` (PARA) with CHANGELOG logging; LogSeq todos in `03-LogSeq` are **proposed as a batch and only become Linear Todo issues (assigned to Tim, matching project or none) on his explicit approval**. **Output:** a Done / Pending Approval / Skipped report. |

**Image capability (any track).** When a ticket on *any* track needs a generated or
edited image, load the **`capability-image`** skill (Skill tool) and follow its pipeline
(generate → download → host → attach → report cost) rather than reinventing the steps —
it's a capability, not a fourth track, so dispatch is unchanged ([SAT-491](https://linear.app/sophia-xyz/issue/SAT-491)).

### B4. Start work (both modes)
- Post a comment: fresh → `🤖 On it — {track}. [model: {model}, effort: {effort}] (by Claude)` ·
  resume → `🤖 Resuming — got your reply. [model: {model}, effort: {effort}] (by Claude)`.
  `{model}`/`{effort}` are the values the orchestrator handed you in A3 — fill them in from
  that, not from self-introspection.
  **Coding track only:** append the happy-path + verifiable-test statement from B3 to this
  same comment (or a line right after it) — e.g. "Happy path: {plain-language flow}. Proof:
  {test name/path}." — so the completion condition you're about to work toward is on the
  record before B5 starts, not just something you reasoned through silently.
- `LINEAR_UPDATE_ISSUE`: set `stateId` = `STATE_IN_PROGRESS` only — **do not set
  `assigneeId`**. Assignee stays on the human user permanently; this call's only job is to
  move the issue out of `STATE_AGENT_QUEUE` so A1 stops re-selecting it on the next tick.
  If the issue still carries a stale `agent-ready` / `agent-needs-human` label, drop it from
  `labelIds` (keep the routing label) — Tim never relabels.
- **Progress file — initial phase plan (SAT-508 ticket 2, local only, zero Linear calls).**
  Write the issue's progress file with the SAT-546 writer:
  ```
  python3 tests/lib/progress_file.py write --dir state --issue <identifier> \
    --phases-total <N> --now "<what you're about to do first>"
  ```
  `--dir state` is the repo-root-relative registry dir (created if missing — same one
  `scripts/dispatch-worker.sh` writes `worker-registry.jsonl` into); this writes
  `state/<identifier>.progress.json`. `started_at` is stamped automatically on this first
  write and preserved on every later one. `phases_total` is your own honest count of the
  natural checkpoints in the B3 profile you're about to run (e.g. coding: resolve repo →
  implement → tests/lint/coderabbit clean → PR opened is a natural 4 — pick whatever's
  honest for the track and don't relitigate it later). This is a **heartbeat aid for a
  later sweeper ticket, not a Linear call and not a gate** — if `state/` isn't writable for
  some reason, note it and continue; never block the tick on it.

### B5. Do the work
Run the matching profile against the task input — which now **includes the layered context
assembled in B1** (project/epic descriptions, resolved `CLAUDE.md` rules, and any advisory
knowledge snippets). Keep every layer's context stacked and co-present; compact only verbose
prose if over budget, never a hard rule. Precedence (`ticket > epic > project > vault >
global`) is the tie-breaker **only** for a genuine same-point hard-rule contradiction.

**Progress file — phase boundaries (SAT-508 ticket 2).** As you clear each natural
checkpoint of the plan you set in B4 (a "phase boundary" — e.g. for coding: context loaded,
change written, tests/lint/coderabbit clean, PR opened), rewrite the same local file:
```
python3 tests/lib/progress_file.py write --dir state --issue <identifier> \
  --phases-done <n> --completed "<what's finished so far>" \
  --now "<what's in flight right now>" --estimate "<phase n/total, roughly ...>"
```
Fields you don't pass keep their prior value (merge semantics) — only pass what changed at
that boundary; `updated_at` refreshes automatically and the writer sanitizes
`completed`/`now`/`estimate` for you (don't hand-escape shell-like tokens yourself). Same
best-effort rule as B4: this is a local heartbeat aid, not a Linear call — never block the
tick on it.

**Threaded replies — post each answer inside its thread (SAT-480).** When your response
addresses a **specific human reply in a thread** (a pending thread from B2), post it as a
**nested reply in that same thread**, not as a new top-level comment — that's what keeps the
conversation granular per thread:
- Set the new comment's `parentId` to that thread's **root** comment id: the human comment's
  `parent` id, or its own id if it started the thread. (Threads are single-level, so
  `parentId` is always the thread root — never a mid-thread reply id.)
- **`LINEAR_CREATE_LINEAR_COMMENT` has no `parentId` parameter** — it only posts top-level
  comments. For a threaded reply, use `LINEAR_RUN_QUERY_OR_MUTATION` running
  `commentCreate(input: { issueId, body, parentId })`, passing `body` via GraphQL variables
  (inlining large markdown can trip `GRAPHQL_VALIDATION_FAILED`).
- Answer **each** pending thread in its own thread — multiple pending threads → one nested
  reply per thread.
- **Issue-level status comments stay top-level** (`LINEAR_CREATE_LINEAR_COMMENT`, no
  `parentId`): the B4 "On it"/"Resuming" pickup marker, and the B6 handback for a *fresh ask*
  worked from the description. Only substantive answers to a specific threaded human comment
  are nested; a `> question:` about a specific thread is nested in that thread, a fresh
  issue-level question stays top-level.

### B5.5. Self-review gate (before handback)
Before posting the B6 handback, pause for **one lightweight self-check**: re-read
the ticket's own acceptance criteria / completion condition (for coding, the
happy-path + verifiable-test statement from B3) plus the track's profile rules, and
confirm your B5 output actually satisfies them. This is a sanity check, not a second
QA pass — no new tooling, no formal test harness, one pass through the checklist.
- **Pass** → proceed to B6 as normal — post whichever B6 success wording applies
  (`✅ Done —` or `✅ Ready for review —`, per the terminal-state rule there).
- **Fail** → don't hand back a false success. Either close the gap yourself (iterate
  on B5) or convert the handback into the matching [B6 open-loop
  path](#b6-report--hand-back-the-state-change-is-the-handback) instead — **Needs input**
  (what's missing is an answer Tim can type in a reply: post the `🔴 Needs input —` /
  `> question:` marker) or **Blocked** (what's missing is an external dependency or a
  real-world action only Tim can take: post the `⛔ Blocked —` marker, SAT-553). Either way
  set `priority` = Urgent and skip the `Done`/`Ready for review` wording entirely (see the
  respective bullets under B6 for the exact templates).

### B6. Report & hand back (the state change is the handback)

> **Legibility rules (SAT-596):** apply to all handback comments and ticket descriptions, every track. Canonical rules and examples are in the global `CLAUDE.md` → Handback Rules → Legibility rules, and the `agent-writing` skill.

---

The **`stateId` transition** is what returns the turn to Tim and removes the issue from
your queue — not assignee, which stays on the human user throughout (see B4). The
`assigneeId = HUMAN_USER_ID` set in the bullets below is now a no-op in the common case
(nothing in this file ever moves assignee off the human user anymore); it's kept only as
a defensive no-op in case something upstream — e.g. a manual edit — ever changes it.

**Progress file — terminal marker (SAT-508 ticket 2).** Whichever path below you take —
Needs input or Success — write the terminal marker to the same local file before or
alongside posting your comment:
```
python3 tests/lib/progress_file.py write --dir state --issue <identifier> --state done
```
This is about *this dispatch's* local worker session ending, not the Linear ticket's own
status — write it on a Needs-input handback too, since your turn in this dispatch is over
either way; the `stateId` transition (In Review / Needs-input) below is what still governs
the ticket's Linear-visible status. Same best-effort rule as B4/B5: local heartbeat aid,
not a Linear call, never a gate on the real handback.

**Thread placement (SAT-480):** when this handback answers a *specific* threaded human
comment (a pending thread from B2), post the comment as a nested reply in that thread per
the B5 threaded-replies rule (`commentCreate` with `parentId`); a handback for a fresh,
issue-level ask stays top-level.

**Pick exactly one primary handback path (SAT-553).** Every handback's *primary* outcome is
exactly one of **Success**, **Needs input**, or **Blocked** — each with its own state
transition and comment template, so Tim can tell them apart from the board alone — that's
the "coloring against the ticket status" he asked for. The **Human-action Todo spin-out** is
not a fourth primary outcome: it's an optional addendum that *composes with* Success (spin
out the action, then hand the original back through Success). Route the primary outcome by
what the ticket *needs from Tim next*:
1. **Success** (→ `STATE_IN_REVIEW`) — the work is done as far as the agent can take it;
   Tim's next move is to *review* and promote to Done. This is the default: almost
   everything should land here. Optionally paired with a Todo spin-out (below) when part of
   the conclusion is "Tim must go do X in the real world."
2. **Needs input** (→ `STATE_NEEDS_INPUT`) — a question answerable inline with a typed reply.
3. **Blocked** (→ `STATE_BLOCKED`) — the work *stopped* and cannot proceed until Tim acts
   or decides something no typed reply alone can fix. (**Needs input** above is the
   lightweight sibling for a question answerable inline; it keeps its In Review state for
   SAT-525 compatibility.)
- **Needs input** (critical input needed from Tim) → post an **unmistakable needs-input
  marker**. Use this when what's missing is an **answer Tim can type in a reply** — a
  clarification, a preference, a yes/no. When what's missing is an external dependency or a
  real-world action only he can perform, use the **Blocked** path below instead; the two are
  distinct on purpose (SAT-553). The marker matters (SAT-525): in this workspace
  `STATE_NEEDS_INPUT` and `STATE_IN_REVIEW`
  are the **same** Linear state ("In Review"), so the state alone can't tell Tim an open
  question apart from a finished handback — that's why he reported never "seeing needs-input
  markers." The **comment body** has to carry it. Use this exact shape:
  ```text
  🔴 Needs input — {one-line what you're waiting on}
  > question: {the specific question}
  [Full session →](https://www.blocks.team/app/{BLOCKS_WORKSPACE_ID}/sessions/{CLAUDE_CODE_SESSION_ID})
  [model: {model}, effort: {effort}] (by Claude)
  ```
  The `🔴 Needs input` headline is the human-visible marker; the `> question:` blockquote +
  `priority` = 1 (Urgent) are the machine-legible ones (an "open question" = a thread whose
  latest agent comment is this marker). Set `assigneeId` = `HUMAN_USER_ID`, `priority` = 1
  (Urgent), `stateId` = `STATE_NEEDS_INPUT` (skip the state change if `STATE_NEEDS_INPUT` is
  `none`). Return `needs-input: {issue}`. **Resuming is automatic now (SAT-525):** Tim just
  replies under the `> question:` and the next tick's secondary path auto-resumes it (A1 + B2)
  — he no longer has to move the state back to `STATE_AGENT_QUEUE`, though that manual move
  still works as an override.
- **Blocked (SAT-553)** — the work **stopped** on something no typed reply alone can fix: an
  external dependency failed (service outage, exhausted balance/quota, missing access or
  credentials), or a real-world action/decision only Tim can take stands between here and
  the finish line. Post an unmistakable blocked marker whose body is **two structured
  bullets** — what occurred, and what unblocks it — so Tim can act without re-reading the
  thread:
  ```
  ⛔ Blocked — {one-line: what stopped the work}
  - What happened: {bulleted summary of what occurred — what was attempted, in order, and
    where/why it stopped}
  - To unblock: {the specific action or decision Tim must take, stated so he can act on it
    directly}
  [Full session →](https://www.blocks.team/app/{BLOCKS_WORKSPACE_ID}/sessions/{CLAUDE_CODE_SESSION_ID})
  [model: {model}, effort: {effort}] (by Claude)
  ```
  Set `assigneeId` = `HUMAN_USER_ID`, `priority` = 1 (Urgent), `stateId` = `STATE_BLOCKED` —
  a **real team workflow state** resolved from the workspace config (Satchel's is
  `f68b9fad-0d13-4397-b1e0-97f6e7216e52`, introspected from the team's states — never invent
  a state id; if `STATE_BLOCKED` is `none`, fall back to the Needs-input state behavior —
  i.e. `stateId` = `STATE_NEEDS_INPUT` if that's configured, else skip the state change
  entirely and leave it wherever B4 put it (`STATE_IN_PROGRESS`); the `⛔ Blocked` marker
  still carries the distinction in the comment either way). Return `blocked: {issue}`.
  **Turn-by-turn:** when `STATE_BLOCKED` (or its Needs-input fallback) is a **floor state**
  (A1/B2), this stays an open loop — Tim replies with the unblocking action or decision (or
  just "done, go ahead") and the next tick auto-resumes the ticket, exactly like a
  Needs-input answer; the difference is purely the at-a-glance visibility of *Blocked* vs
  *In Review* on the board. **If both `STATE_BLOCKED` and `STATE_NEEDS_INPUT` resolve to
  `none`**, the issue stays in `STATE_IN_PROGRESS` (outside the floor), so this auto-resume
  promise does **not** hold — the `⛔ Blocked` marker and Urgent priority are still visible
  on the board, but Tim must manually move the issue back to `STATE_AGENT_QUEUE` to resume
  it. That double-`none` case is a workspace-config gap, not the common path.
- **Success** (any completion, deterministic or judgment-bearing) → post a comment, set
  `assigneeId` = `HUMAN_USER_ID`, `stateId` = `STATE_IN_REVIEW` (never `STATE_DONE` — see the
  terminal-state rule below), `priority` = normal
  (reserve Urgent for the Needs-input and Blocked paths).
  Return `done: {issue}`. The comment wording still signals your own confidence, so Tim can
  tell at a glance how much scrutiny to apply, even though the Linear state is the same either way.
  **Every success comment carries two structured bullets right after the headline**, so Tim
  can act on the handback without re-reading the diff or the thread:
  - **What changed:** {short summary of what was done or changed, and
    why it's considered done (SAT-553)}
  - **Decision needed to move to Done:** {what Tim needs to decide or verify before promoting
    to Done — or `none — safe to promote` if the work is fully deterministic and there's
    nothing to weigh}

  Full templates:
  - Deterministic / final (coding → open PR, deterministic admin):
    ```
    ✅ Done — {summary + links}.
    - What changed: {short summary}
    - Decision needed to move to Done: {none — safe to promote, or the specific check}
    [Full session →](https://www.blocks.team/app/{BLOCKS_WORKSPACE_ID}/sessions/{CLAUDE_CODE_SESSION_ID})
    [model: {model}, effort: {effort}] (by Claude)
    ```
    **For a coding PR handback (SAT-551):** `{links}` **must** be the PR's **full clickable
    URL** — the complete `https://github.com/<owner>/<repo>/pull/<N>` (resolve `<owner>/<repo>`
    with `gh repo view --json owner,name` in the issue's repo, or take the URL `gh pr create`
    prints) — **never** a bare `PR #<N>`, so Tim can click straight through to review. Add one
    adjacent line naming **where review happens** so he isn't left guessing which surface to
    open. Concrete shape:
    ```
    ✅ Done — opened PR https://github.com/<owner>/<repo>/pull/<N> fixing {what}.
    - What changed: {short summary}
    - Decision needed to move to Done: none — safe to promote once the PR is merged.
    - Review on: the GitHub PR page linked above — open it to read the diff (CodeRabbit has
      already reviewed) and merge; Linear just tracks status, review the code on GitHub.
    [Full session →](https://www.blocks.team/app/{BLOCKS_WORKSPACE_ID}/sessions/{CLAUDE_CODE_SESSION_ID})
    [model: {model}, effort: {effort}] (by Claude)
    ```
  - Judgment-bearing (writing, admin that needs your eyes):
    ```
    ✅ Ready for review — {summary + links}.
    - What changed: {short summary}
    - Decision needed to move to Done: {what Tim needs to decide or verify}
    [Full session →](https://www.blocks.team/app/{BLOCKS_WORKSPACE_ID}/sessions/{CLAUDE_CODE_SESSION_ID})
    [model: {model}, effort: {effort}] (by Claude)
    ```
- **Human-action Todo spin-out (SAT-553)** — *composes with* Success above, it doesn't
  replace it. Use it when the work's conclusion is that **Tim personally must execute
  something in the real world** — make a purchase after a decision is reached, have a
  conversation, sign up for or cancel a service. Don't bury that action inside a handback
  comment where it can't be tracked: spin it out as its **own new issue** so it surfaces in
  Tim's Todo list as a first-class action item. **If `STATE_TODO` is `none`, skip the
  spin-out entirely** and fold the requested action into the handback comment instead —
  never call `issueCreate` with a `none`/empty `stateId`.
  - **Idempotency check first, with an orphan fallback:** before creating anything, search
    for an existing spin-out from a prior, possibly-crashed attempt. First check for one
    already **linked** to the original: `issue(id: original) { relations { nodes {
    relatedIssue { id identifier title state { id } } } } }`. A crash can happen *between*
    `issueCreate` and `issueRelationCreate`, though, leaving a spin-out issue that exists but
    isn't linked yet — the relations check alone would miss it and create a duplicate
    orphan. So also search by a **deterministic fallback**: `issues(filter: { team: { id: {
    eq: "<TEAM_ID>" } }, state: { id: { eq: "<STATE_TODO>" } }, title: { startsWith: "Action
    (Tim): " }, description: { contains: "<original identifier>" } }, first: 5)` — a Todo
    issue whose description already links back to this original issue's identifier is that
    same crashed attempt. If either check finds one, reuse it — link it (if not yet linked)
    and hand back against it — instead of creating a duplicate.
  - Otherwise create it with `issueCreate`: `teamId` = `TEAM_ID`, `stateId` = `STATE_TODO`,
    `assigneeId` = `HUMAN_USER_ID`, `projectId` = the original issue's project (omit if the
    original has none), title = `Action (Tim): {imperative action}`.
  - The **description carries the agent's reasoning** so Tim can execute without
    re-deriving it: bullets for the **decision/recommendation**, **why** (the key
    trade-offs), the **concrete steps to execute**, and a Markdown link back to the
    originating issue.
  - **Link the two issues**: `issueRelationCreate` with type `related` between spin-out and
    original (plus the Markdown cross-links in both descriptions/comments). If this step
    fails after the spin-out issue was created, retry the link before proceeding — don't
    hand back the original with a dangling, unlinked spin-out.
  - **Division-of-labor rule: reasoning is agent work, execution is Tim's.** The spin-out
    must **not** carry any `ROUTING_LABELS` / `MODEL_LABELS` / `EFFORT_LABELS` label, and it
    lands in `STATE_TODO` — outside `STATE_AGENT_QUEUE` and outside the auto-resume floor —
    so **neither A1 path can ever select it**: it is never auto-dispatched to any agent
    (whatever model tier did the reasoning, Fable included). If, while executing, Tim
    decides some sub-step *should* get agent help after all, he explicitly moves the
    spin-out (or a new ticket) into Agent Queue — a deliberate human act, never automatic.
  - Only after the spin-out issue exists and is linked, hand the **original** issue back
    through the **Success** path above, linking the spin-out in its `What changed` bullet
    (as a clickable issue link, per the comment conventions). Return `done: {issue} (spun
    out {new-identifier})`.
  - **Turn-by-turn, end to end:** agent reasons and hands the original back for review →
    Tim reviews the plan (In Review) → Tim executes the Todo himself and closes it → any
    reply Tim leaves on the *original* still auto-resumes the agent for follow-up
    reasoning (SAT-525). Each turn is one tick; the agent side never silently crosses from
    planning into executing the human-action item.

`{model}`/`{effort}` here are the same values you were handed at dispatch (A3) — use
those, not a fresh self-report.

**Terminal-state rule:** the agent never sets `STATE_DONE` itself, no matter how
deterministic or final the work looks (coding tickets never merge their own PR either — see
B3 — so "Done" here is only ever the agent's own assessment, not an objective fact). Every
successful completion — deterministic or judgment-bearing — hands back with `stateId` =
`STATE_IN_REVIEW`; only the comment wording (`Done —` vs `Ready for review —`) distinguishes
the two. For the **original** issue, Tim promotes it to `STATE_DONE` himself once he's
reviewed it. A **SAT-553 Todo spin-out is different**: the agent creates it in `STATE_TODO`
and never moves it again, and reviewing the plan is not the bar — it reaches `STATE_DONE`
only once Tim has actually **executed** the real-world action and closes it himself. Only
the open-loop paths — a Needs-input question or a Blocked handback — use Urgent priority.
