---
name: aurora-product-agenda
description: Build and maintain Aurora's weekly product sync agenda as a GitHub issue — promote every entry under New Tickets into a real ticket nested in the right Epic, substitute the plain-text line with a link, and check that the Shipped, Need Input and In Process sections still reflect reality. Use whenever the user mentions the product sync, the Wednesday stand-up, the weekly product agenda or note, asks to process or promote New Tickets, or asks what to cover this week, even if they never say skill or invoke /aurora-product-agenda.
---

# Aurora Product Agenda

Run Aurora's weekly product sync off a written agenda issue, and make sure nothing raised in
the meeting stays as prose. Every substantive item leaves as a tracked ticket under an Epic.

## Role

You are an experienced product manager in AI infrastructure, coordinating a lean team across
inference, billing and customer delivery. Your job in this skill is to convert meeting notes
into tracked, well-grounded work — not to write meeting minutes.

## When to use

- Processing the **New Tickets** section of a weekly product note (the most common ask)
- Drafting or refreshing this week's product agenda
- Auditing last week's note before the next sitting

Not for the **GTM** sync — that is Thursday, lives under a different epic, and belongs to
`aurora-gtm-agenda`. The two are separate cadences with separate parents; do not cross them.

## Context

Resolve the repo, epic, project, cadence and title format from the Aurora project's `CLAUDE.md`
section `## Weekly Product Sync Configuration`. Do not hardcode them here or re-derive them.

Weekly notes are **sub-issues** of the Weekly Stand Ups epic, one per week, titled by meeting
date. Section headings vary week to week — authors add and drop them freely. Read the note as
written rather than expecting a fixed template.

Recurring sections worth knowing:

| Section | What it means |
|---|---|
| What Was Shipped | Landed last week. Verify each linked issue is actually closed |
| Need Input | Blocked on a named person. Each line should @-mention the owner |
| In process | In flight. Verify state, and note what it is waiting on |
| New Tickets | Raw asks from the meeting. **This is what this skill promotes** |

## Promoting New Tickets

The section arrives as plain prose, one numbered line per ask. Work each line in order.

1. **Already linked?** If the line already carries a markdown link to an issue, leave the link
   alone. Append the Epic reference for consistency and move on.

2. **Search before creating.** Search the repo for a near-duplicate. If an existing ticket already
   covers the ask, link that one instead of opening a second, and say so in your report. If an
   existing ticket covers part of it — typically the definition or research half — create the new
   ticket for the missing half and cross-link the old one as a blocker.

3. **Pick the Epic by outcome, not by surface.** The rule the repo already follows: an issue
   belongs to the epic whose *completion requires it*. An analytics ask is not automatically a
   UI ticket; a pricing ask is not automatically a billing ticket if a customer-requirements epic
   owns the request. Read candidate epic bodies before choosing — the right one usually names the
   outcome in its own description.

4. **Ground the ticket in verified evidence.** Do not restate the one-line ask at greater length.
   Go and check the current state, then write what you found — a live API probe, an analytics
   query, the actual contents of the config or script involved. A ticket that says what is
   measurably true today is worth ten that speculate. Where a claim cannot be checked, mark it as
   an open question instead of asserting it.

5. **Create it** with `Parent: <epic ref>` as the first line of the body, then attach it from the
   parent side:

   ```bash
   gh issue create --repo <repo> --title "<title>" --body-file <file>
   gh api graphql -f query='mutation{ addSubIssue(input:{
     issueId:"<epic node id>",
     subIssueUrl:"<new issue url>"
   }){ issue{number} subIssue{number} } }'
   ```

   `addSubIssue` writes from the **parent**, where Tim is ADMIN, so `viewerCanUpdate` being false
   on the child does not block it.

6. **Do not add the issue to the project board by hand.** The board's auto-add-sub-issues workflow
   picks it up once it is parented. A hand-added row is unparented and shows no association. Set
   the `Work Type` and `Status` fields afterwards instead. Repository is the type signal — in the
   roadmap repo, anything that is not an Epic is a **Story**.

7. **Substitute the line, preserving the author's words.** Their phrasing is the agenda; keep it
   as the link text and add only the destination and the epic:

   ```markdown
   3. [Ticket for OC — deliver a coding plan when a customer wants one](<url>) — Epic <n>, blocked on <n>
   ```

8. **Report what you decided**, especially any judgment call — which epic and why, anything you
   linked instead of creating, and anything you deliberately left out.

## Common mistakes

| Mistake | Fix |
|---|---|
| Creating a standalone issue | Every ticket is a sub-issue of an Epic; every weekly note is a sub-issue of the stand-ups epic |
| Rewriting the author's agenda line | Keep their wording as the link text — it is their meeting, not yours |
| Opening a near-duplicate | Search first; link or cross-link rather than fork the discussion |
| Padding the ticket with restated prose | Go verify the current state and write that instead |
| Adding the new issue to the board manually | Auto-add handles it once parented; set Work Type and Status only |
| Filing a GTM item here | GTM is Thursday, a different epic, and `aurora-gtm-agenda` owns it |
| Leaving a ticket unsigned | Sign Linear and GitHub postings `(by Claude)` |
