---
name: pm-1-1-prep
description: Prepares 1:1 meeting agendas by pulling context from Linear (assigned issues - in progress, blocked, overdue, recently completed, upcoming) and Slack (last 7 days - blockers, questions, wins) via the Composio CLI, then generates a structured agenda. Activate for "prep 1:1 with [name]", "prepare for 1:1", "1:1 agenda", "meeting prep".
---

# PM 1:1 Prep

## Gather context

### 0. Resolve identifiers

The trigger arrives as a bare `[name]`, but every query below needs a concrete Linear email and Slack handle, not a name. Before building any query:

- Resolve the person's Linear email — look them up (`LINEAR_LIST_LINEAR_USERS` or a GraphQL `users` query filtered by name) rather than guessing `firstname@company.com`.
- Resolve their Slack handle — `composio search slack` then a user-search tool, or ask the user directly if the match is ambiguous.
- Confirm both resolved identifiers with the user before running any Linear or Slack query below.

**Linear** — issues assigned to the person: In Progress / Blocked / Overdue, completed in the last 7 days, due in the next 7 days. `LINEAR_LIST_ISSUES` supports neither state nor date filters, so use `LINEAR_RUN_QUERY_OR_MUTATION` with a GraphQL query instead, run as separate filter branches per category rather than one combined `or`:

```bash
composio search linear   # confirm the exact slug for this connection first
```

- **Active** — `filter: { assignee: { email: { eq: "<email>" } }, state: { type: { eq: "started" } } }`
- **Blocked** — `state.type` has no "blocked" value, and `unstarted` covers backlog and planned work too, not just blocked issues. Blocked is normally a named workflow state (e.g. "Blocked") or a label — resolve the exact name for this workspace first (`LINEAR_LIST_LINEAR_STATES`, or ask) rather than assuming. `filter: { assignee: { email: { eq: "<email>" } }, state: { name: { eq: "<resolved-blocked-state>" } } }` (swap for `labels: { name: { eq: "<blocked-label>" } }` if this workspace flags blocked work with a label instead).
- **Overdue** — same assignee filter + `dueDate: { lt: "<today>" }`, `state: { type: { nin: ["completed", "canceled"] } }`
- **Upcoming (next 7 days)** — same assignee filter + `dueDate: { gte: "<today>", lt: "<today+7>" }`, `state: { type: { nin: ["completed", "canceled"] } }` — exclude finished work; the due-date filter alone doesn't drop issues that closed early. Half-open on purpose: `gte today, lte today+7` spans **eight** calendar dates, not seven.
- **Recently completed (last 7 days)** — same assignee filter + `completedAt: { gte: "<today-6T00:00 local, as UTC>", lt: "<tomorrow T00:00 local, as UTC>" }` — the seven dates ending today, today included.

Every boundary above is a date in the **local reporting timezone** (America/Los_Angeles unless the invoking CLAUDE.md says otherwise), converted to a UTC instant before it goes into the query. `completedAt` is a timestamp, so a bare `YYYY-MM-DD` is midnight UTC and drops or adds most of a local day. `dueDate` is a plain date and needs no conversion.

Watch for patterns: items stuck in review, repeat blockers.

**Slack** — last 7 days, from this person only: messages containing "blocker"/"stuck"/"help", threads with unanswered questions from them, and any wins they shared. Always scope with `from:` — without a person filter, other people's messages land in the agenda.

Slack's `after:`/`before:` are **exclusive** — they omit the dates you name. To cover the same seven
dates as the Linear windows (today-6 through today inclusive), pass `after:<today-7>` and
`before:<tomorrow>`; using `after:<today-7> before:<today>` silently drops today, and
`after:<today-6>` drops the oldest day.

```bash
composio search slack
composio execute SLACK_SEARCH_MESSAGES -d @payload.json
# query: from:<slack_handle> after:<today-7> before:<tomorrow> (blocker OR stuck OR help OR question OR win)
# dates YYYY-MM-DD in the local reporting timezone, and both bounds are exclusive
```

`SLACK_SEARCH_MESSAGES` returns matching messages, not the surrounding thread — a hit on a question doesn't tell you whether it was answered. For each question-shaped hit, fetch its thread with `SLACK_FETCH_MESSAGE_THREAD_FROM_A_CONVERSATION` using the channel ID and `thread_ts ?? ts` from the hit — top-level messages that haven't been replied to have no `thread_ts`, so fall back to `ts`. Check the replies: if someone else replied after the person's message, classify it answered and leave it off the agenda; only genuinely unanswered questions go on.

Both lookups go through the Composio CLI, authed as `timfong888` in project `timfong888_org`. Resolve the live tool slug with `composio search <app>` before executing — do not hardcode a slug from memory.

## Generate the agenda

Sections, in order:

1. Quick check-in (2 min) — energy, concerns, anything on their mind.
2. Their updates (10 min) — leave blank, let them lead.
3. Items to discuss (10 min) — blockers pulled from Linear/Slack, each with a "what support do you need" question; plus any pending decisions.
4. Celebrate (2 min) — a recent win from Linear/Slack.
5. Support ask (5 min) — "what can I unblock this week?"
6. Notes — blank, filled live.
7. Action items — table: Item | Owner | Due.

**Manager/CEO variant** (reporting up instead of down): replace "Their updates" with "My updates" (wins, OKR progress), add "Decisions I need" (options + your recommendation), and close with an alignment check instead of a support ask.

## Quick commands

| Trigger | Action |
|---|---|
| `prep 1:1 [name]` | Full prep with Linear + Slack context |
| `1:1 agenda [name]` | Agenda template only, no context pull |
| `manager 1:1 prep` | Manager-variant template |

Review the generated agenda before the meeting — add your own items, don't read it verbatim, and don't skip letting them lead in "their updates."
