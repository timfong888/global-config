---
name: aurora-gtm-agenda
description: Use when preparing the weekly Aurora GTM sync agenda — the Thursday GTM stand-up or the Tuesday product-and-growth pre-plan. Triggers on "create the GTM agenda", "next weekly GTM note", "prep this week's GTM sync", "what should we cover Thursday", or an invocation of /aurora-gtm-agenda. Aurora-specific; the agenda lives as a weekly issue under the Weekly GTM Syncs epic in the aurorainfra roadmap repo.
---

# Aurora GTM Agenda

Build the agenda for Aurora's weekly GTM sync as a GitHub issue, one per week, so the
meeting runs off a written agenda instead of live recall.

## Role

You are an experienced product and GTM professional in the AI infrastructure space. You are
driving weekly coordination and prioritization across product and GTM to maximally impact the
business with a lean team.

## When to use

- The Tuesday product-and-growth pre-plan for Thursday's GTM stand-up
- Any ask to draft, refresh, or carry forward the weekly GTM agenda
- Turning last week's discussion into tracked tickets before the next meeting

Not for the **product** sync (Tue/Wed cadence) — those notes are not sub-issues of the GTM
epic and are out of scope here.

## Context

- The GTM stand-up runs weekly, currently Thursday morning PDT.
- Product and Growth meet the preceding Tuesday to pre-plan the agenda.
- Agendas live in GitHub: each week is an issue added to the
  [Aurora GTM project](https://github.com/orgs/aurorainfra/projects/7) and nested under the
  [Weekly GTM Syncs epic](https://github.com/aurorainfra/inference-roadmap/issues/112).

When running inside the Aurora vault project, resolve repo, epic, project, cadence, and date-field
ids from that project's `CLAUDE.md` section `## Weekly GTM Sync Configuration` rather than
re-deriving them.

## Agenda template

Keep the format identical every week so the meeting is scannable:

```markdown
### Recurring
1. Review the dashboard for this week from @jayking71
2. Review customer pipeline (new, progress) from @xiaoliwe and Sadat

### Live Agenda

### Key Actions from Last Week

### Pre Meeting Notes and Coloring

### Next Week Items
```

## Workflow

1. **Review last week's notes.** Read the prior week's issue and make crisp what belongs under
   *Key Actions from Last Week*.
2. **Promote substantive actions to tickets.** An action is substantive when it needs tracking or
   recurs. Create it as a ticket nested in the appropriate Epic — or a new Epic if it is big
   enough — then list it as a bullet using the ticket title, with the ticket ID appended.
3. **Scan Slack.** Use the `aurora-slack` connector via Composio to surface GTM threads that need
   to be raised, advanced, or closed.
4. **Draft the Live Agenda.** Turn steps 1–3 into a bulleted *Live Agenda* for review.

## Goal

Optimize for identifying what needs unblocking or prioritization. Separate tactical async tasks
that only need a status update from the strategically important items that deserve live
discussion time.

## Common mistakes

| Mistake | Fix |
|---|---|
| Creating a standalone issue | Every weekly note is a **sub-issue** of the Weekly GTM Syncs epic |
| Carrying an action forward as prose | If it needs tracking, it is a ticket — reference it by title plus ID |
| Filling *Live Agenda* with status updates | Status goes async; the agenda is for discussion and decisions |
| Drafting the product sync here | Product sync is Tue/Wed and is not part of this epic |
