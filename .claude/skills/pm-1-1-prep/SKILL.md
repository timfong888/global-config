---
name: pm-1-1-prep
description: Prepares 1:1 meeting agendas by pulling context from Linear (assigned issues - in progress, blocked, overdue, recently completed, upcoming) and Slack (last 7 days - blockers, questions, wins) via the Composio CLI, then generates a structured agenda. Activate for "prep 1:1 with [name]", "prepare for 1:1", "1:1 agenda", "meeting prep".
---

# PM 1:1 Prep

## Gather context

**Linear** — issues assigned to the person: In Progress / Blocked / Overdue, completed in the last 7 days, due in the next 7 days. Watch for patterns: items stuck in review, repeat blockers.
```bash
composio search linear                                  # confirm the exact slug for this connection first
composio execute LINEAR_LIST_ISSUES -d @payload.json    # filter: assignee, state, updatedAt range
```

**Slack** — last 7 days: messages from the person containing "blocker"/"stuck"/"help", threads with unanswered questions from them, and any wins they shared.
```bash
composio search slack
composio execute SLACK_SEARCH_MESSAGES -d @payload.json  # query terms + channel/date range
```

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
