---
name: linear-sanitize
description: Detect and interactively fix Linear hygiene gaps — missing due dates, stale past-due items, and unanswered comments — for the XFN team. Run standalone or as pre-flight before weekly prep. Activate when user says "linear sanitize", "linear hygiene", "clean up linear", or invokes /linear-sanitize.
---

# linear-sanitize

Detects and interactively remediates 3 Linear hygiene gaps for the XFN team.

## Invocation

```text
/linear-sanitize [due-dates|past-due|awaiting]
```

No argument → run all 3 checks sequentially.

## Constants

```text
XFN_TEAM_ID     = ea67e122-903e-4e23-aa1d-a2394d0c9aa5
TIM_USER_ID     = bcc5fef5-896e-4c24-9523-724bee8a9053
STATE_DONE      = 71be65f4-9d2b-47ad-aa35-af419f148a09
STATE_CANCELED  = 8a00f39d-58df-4378-a2e9-c92f8ceb3dce
LABEL_MOLLY     = 20b1b023-4a7e-4f84-bea7-8dbab8c0ac6e   # "Molly Input" escalation label
```

## Access

Run all Linear queries/mutations via the Composio CLI (`composio execute LINEAR_RUN_QUERY_OR_MUTATION -d @payload.json`). Verified fallback: direct GraphQL via `$LINEAR_API_KEY`. Run mutations sequentially, never in parallel — Linear rate-limits.

## Next-Friday calculation

`today` is the current date in the **local reporting timezone** (America/Los_Angeles unless the
invoking CLAUDE.md says otherwise) — not UTC, which rolls over a day early in the evening. All
`dueDate` and "N days overdue" arithmetic in the checks below uses that same date.

The formula assumes **Sunday = 0 … Friday = 5**. Python's `date.weekday()` is Monday-based, so
convert first (`dow = (d.weekday() + 1) % 7`) or use `d.isoweekday() % 7`; feeding a Monday-based
value in silently returns the wrong date.

```text
daysUntilFriday = (5 - dowSundayZero + 7) % 7; if 0, use 7
nextFriday = today + daysUntilFriday days   → format as YYYY-MM-DD
```

Check both branches before relying on it: from a Wednesday (`dow` 3) it must return that same
week's Friday (+2); from a Friday (`dow` 5) it must return the *following* Friday (+7), never today.

## Query plan (2 API calls for a full pass)

**Query A** (shared by Check 1 + Check 2) — active XFN issues with `dueDate`:

```graphql
issues(filter: {
  team: { id: { eq: "ea67e122-903e-4e23-aa1d-a2394d0c9aa5" } }
  state: { id: { nin: ["71be65f4-9d2b-47ad-aa35-af419f148a09","8a00f39d-58df-4378-a2e9-c92f8ceb3dce"] } }
}, first: 250) {
  nodes { id identifier title url dueDate state{name} assignee{id name} project{name} }
  pageInfo { hasNextPage endCursor }
}
```

Paginate on `hasNextPage`/`endCursor`. Partition client-side: `dueDate === null` → Check 1; `dueDate <= today-7d` → Check 2. Run once even for a single-section invocation.

**Query B** (Check 3 only) — Tim's comments 7+ days old on active XFN issues:

```graphql
comments(filter: {
  user: { id: { eq: "bcc5fef5-896e-4c24-9523-724bee8a9053" } }
  issue: { team: { id: { eq: "<XFN_TEAM_ID>" } }, state: { id: { nin: ["<STATE_DONE>","<STATE_CANCELED>"] } } }
  createdAt: { lte: "<7_DAYS_AGO_ISO>" }
}, first: 50, after: "<CURSOR>", orderBy: createdAt) {
  nodes { id body createdAt issue { id identifier title url assignee{id name} } }
  pageInfo { hasNextPage endCursor }
}
```

Paginate on `hasNextPage`/`endCursor` until exhausted — `first: 50` alone can omit matching comments on a busy team. Dedupe the results by `issue.id`, keeping only Tim's most recent comment per issue. Then, for each unique issue, fetch its full comment history separately, also paginated:

```graphql
issue(id: "ISSUE_ID") {
  comments(first: 50, after: "<CURSOR>", orderBy: createdAt) {
    nodes { id createdAt user{id name} }
    pageInfo { hasNextPage endCursor }
  }
}
```

Sort each issue's comments by `createdAt` ascending and classify (Check 3 logic) only once the full history is fetched — a truncated page can hide a later reply and cause a false ping or escalation.

## Check 1: Missing Due Dates

Filter Query A to `dueDate === null`. Group by project (ungrouped → "No Project"). Zero results → print "All active issues have due dates set." and skip.

Table: `Issue | Assignee | Status | Proposed Due` (next Friday). Ask per project group: accept all (set to next Friday) / skip all / mixed (e.g. `"1: accept, 2: 2026-03-14, 3: skip"`).

## Check 2: Past Due (7+ days overdue)

Filter Query A to `dueDate` set and `<= today - 7 days` (includes issues due exactly seven days ago). Compute `daysOverdue`, sort descending (most overdue first). Zero results → print "No issues are 7+ days past due." and skip.

Table: `Issue | Assignee | Due Date | Days Over | Status | Project`. Ask: extend all to next Friday / close all (state → `STATE_DONE`) / skip all / mixed (e.g. `"1: e, 2: c, 3: s, 4: e 2026-03-14"` — e=extend, c=close, s=skip; bare "e" defaults to next Friday).

## Check 3: Awaiting Response (Tim's unanswered comments)

Per issue, using its full fetched comment history (sorted by `createdAt`): find Tim's comment, flag if no comment from a **different** user comes after it. If Tim posted several in a row unanswered, flag only the earliest. Snippet = first 40 chars of Tim's comment, markdown stripped. Sort by days-waiting descending. Zero results → print "No unanswered comments older than 7 days." and skip.

Table: `Issue | Assignee | Comment Date | Days | Snippet`. Ask: ping all / skip all / mixed (e.g. `"1: p, 2: e, 3: s"` — p=ping, e=escalate, s=skip).

## Mutations

```graphql
issueUpdate(id: "ISSUE_ID", input: { dueDate: "YYYY-MM-DD" })          # set / extend due date
issueUpdate(id: "ISSUE_ID", input: { stateId: "71be65f4-...48a09" })   # close (→ Done)
commentCreate(input: { issueId: "ISSUE_ID", body: "Following up — @[ASSIGNEE_NAME](mention://user/ASSIGNEE_ID), any update on this?" })
issueAddLabel(id: "ISSUE_ID", labelId: "20b1b023-4a7e-4f84-bea7-8dbab8c0ac6e")   # escalate — pair with an explanatory commentCreate
```

`commentCreate` ping: use the `assignee.id`/`assignee.name` from the widened Query A or B result to build the mention so the assignee is actually notified. If `assignee` is null, use generic body `"Following up — any update on this?"` instead.

## Summary

Track counts: `dueDatesSet`, `dueDatesExtended`, `followUpsPosted`, `escalated`, `issuesClosed`, `skipped`. Present after all checks:

```markdown
## Sanitize Summary
| Action | Count |
|--------|-------|
| Due dates set | X |
| Due dates extended | X |
| Follow-ups posted | X |
| Escalated | X |
| Issues closed | X |
| Skipped | X |
```
