---
name: checkin
description: High-level project check-in — review all tickets in a Linear project, surface blockers and stalled work, identify the nearest path to user-visible MVP value, post a project activity comment, and create blocker tickets assigned to the user. Designed for use at the start of a session or mid-flight during a long-running agent job.
whenToUse: Run when the user invokes `/checkin`, asks for a project overview or status review, or when a long-running agent session needs to surface current progress before continuing. Works on a named Linear project or the active project inferred from the current context.
---

# /checkin — Project Status Review

You are running a **high-level check-in** between the agent and the engineering leader.
The goal is a rapid, honest picture of where the project stands, what's blocking it,
and what the clearest path to user-visible value is — delivered in one compact comment.

This skill is **read-heavy and action-light**: fetch, analyze, and report. Create new
issues only for confirmed blockers. Never push code or rewrite tickets without being
told to.

---

## Step 1 — Identify the target project

Determine which Linear project to check in on:

1. **Explicit argument**: if `/checkin <project-name>` or `/checkin <KEY-NNN>` was
   passed, use that.
2. **Current issue context**: if invoked from inside a Linear issue, use that issue's
   `project`.
3. **Active workspace default**: if neither applies, check the invoking project's
   `CLAUDE.md` for a `## Checkin Configuration` block with a `PROJECT_ID` field.
4. **Ask**: if no project can be resolved, post one `> question:` and stop.

Resolve the project to its Linear `id` (UUID) before continuing — use
`mcp__linear__linear_searchIssues` or `mcp__linear__linear_getProjects` as needed.

---

## Step 2 — Load project context

Fetch the project and its issues in a single pass:

```graphql
query ProjectCheckin($projectId: String!, $teamId: String!) {
  project(id: $projectId) {
    id name description
    state { type }
    progress
  }
  issues(filter: {
    project: { id: { eq: $projectId } }
    team:    { id: { eq: $teamId } }
  }, first: 100, orderBy: updatedAt) {
    nodes {
      id identifier title
      state { name type }
      priority
      assignee { name }
      updatedAt
      comments(first: 1, orderBy: createdAt) {
        nodes { body createdAt user { name } }
      }
    }
  }
}
```

Use `mcp__linear__linear_getWorkflowStates` to resolve state names → types if needed.

---

## Step 3 — Analyze tickets

Classify every issue into one of four buckets:

| Bucket | Criteria |
|---|---|
| **Active** | State type `started`, updated in last 7 days |
| **Stalled** | State type `started` but **no activity > 7 days** |
| **Blocked / at-risk** | Explicitly marked Blocked, or priority Urgent with no recent progress |
| **Not started** | State type `unstarted` (Todo, Backlog, Agent Queue) |

Then answer these five questions from the data:

1. **What is actually moving?** (Active bucket — any real commits/comments in the last week?)
2. **What has silently stopped?** (Stalled bucket — time since last update)
3. **What's blocking the project?** (Blocked/at-risk bucket — root cause if inferable)
4. **What's the shortest path to a user-visible MVP change?** Identify the single ticket
   (or small set) whose completion would produce something a real user could touch. Prefer
   concrete over theoretical.
5. **What must happen first / in what order?** Synthesize a priority order (max 5 items).

---

## Step 4 — Create blocker tickets (if any)

For each confirmed blocker where **no ticket already exists**:

- **Idempotency check first**: search for an existing open ticket with a matching title
  or description before creating anything.
- Create with `mcp__linear__linear_createIssue`:
  - `teamId` = current team id
  - `projectId` = target project id
  - `stateId` = Todo state id (resolved via `mcp__linear__linear_getWorkflowStates`)
  - `assigneeId` = `HUMAN_USER_ID` (the invoking user — from workspace config or
    `mcp__linear__linear_getViewer`)
  - `priority` = 1 (Urgent)
  - `title` = `Blocker: <concise description>`
  - `description` = what's blocked, why, and what would unblock it

Link the new blocker ticket back to the blocked issue via `mcp__linear__linear_createIssueRelation`
(type `blocks`).

---

## Step 5 — Post the check-in comment

Post the summary as a **top-level comment on the project's parent epic** (the highest-level
issue in the project), or as a comment on the issue that triggered the checkin if no
parent epic is identifiable. Use `mcp__linear__linear_createComment`.

Apply the **legibility rules** from the global CLAUDE.md — answer first, one idea per
bullet, bold the 2–4 load-bearing words, no walls of code or long paths, depth behind
a link.

### Comment template

```
**<Date> check-in — <one-line verdict>.**

- **Velocity**: <Active count> tickets moving / <Stalled count> stalled / <Blocked count> blocked
- **Nearest user value**: <ticket id + title — the one change a real user would notice>
- **Top stalls**: <ticket id(s) + how long since last update>
- **Blockers**: <ticket id(s) + root cause, or "none">

**Priority order:**
1. <SAT-NNN> — <why first>
2. <SAT-NNN> — <why second>
3. <SAT-NNN> — <why third>
(up to 5)

<New blocker tickets created: [SAT-NNN](link), … — or omit line if none.>

(by Claude)
```

Keep it under **15 lines**. The reader is on a phone. Every link must be a clickable
Markdown link — `[SAT-NNN](https://linear.app/<workspace-slug>/issue/SAT-NNN)`.

---

## Step 6 — Testable conditions (optional, when asked)

If the user asks for testable conditions alongside the check-in (e.g. `/checkin --goals`),
for each ticket in the **priority order** add one line:

```
- [SAT-NNN] ✅ passes when: <deterministic condition a non-engineer can verify>
```

This maps each feature to a verifiable goal, usable with `/goal` setting or future
automated validation.

---

## Step 7 — Handback

After posting the comment, report the summary back inline in the assistant response
(not as another Linear comment — the assistant response is the detailed view; the
Linear comment is the glance).

If running inside a long-running job (not a standalone `/checkin` invocation), **resume
the job** after the check-in is posted — the check-in is a waypoint, not a stop.

---

## Configuration block

Projects that want custom checkin targets can add this block to their `CLAUDE.md`:

```
## Checkin Configuration
| Variable       | Value                                  |
|---|---|
| `PROJECT_ID`   | <Linear project UUID>                  |
| `TEAM_ID`      | <Linear team UUID>                     |
| `WORKSPACE_SLUG` | <linear.app workspace slug>          |
| `HUMAN_USER_ID` | <assignee for new blocker tickets>   |
```

If absent, values are inferred from the global Agent Poll Configuration defaults.

---

## Constraints

- **Never self-certify Done** for any ticket — that's the human's call.
- **Never push code** — this skill reads and reports only.
- **Never create more than 3 blocker tickets in one run** — if there are more, list
  the remainder in the comment and note they were not auto-created to avoid noise.
- **Never rewrite ticket descriptions** unless explicitly asked.
- Sign every comment `(by Claude)`.
