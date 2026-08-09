---
name: update-linear-status
description: ALWAYS invoke at the end of every @blocks task. Updates the Linear issue status to reflect the current state of work — Done, In Review, or Blocked. Never leave an issue in Agent Queue or In Progress after completing or handing off work.
---

# Update Linear Issue Status

Every @blocks agent session MUST update the Linear issue status before finishing. This is a required step, not optional.

## When to Update

Update the status at the **end of every session**, based on what was accomplished:

| Outcome | New Status | When to use |
|---|---|---|
| Work is fully complete, no PR needed | **Done** | API operations, research, config changes, investigations |
| A pull request was created | **In Review** | Any task that produces a PR |
| Waiting for user input to proceed | **Blocked** | Ambiguity, missing credentials, explicit blocker |

## How to Update

Use `mcp__linear__linear_updateIssue` with the issue identifier and the appropriate `stateId`:

```
mcp__linear__linear_updateIssue
  issueId: <issue-identifier, e.g. SAT-123>
  stateId: <id from table below>
```

### Satchel Team State IDs

| State | ID |
|---|---|
| Done | `299e627d-3989-40c4-8aea-b9d56209fa39` |
| In Review | `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` |
| Blocked | `f68b9fad-0d13-4397-b1e0-97f6e7216e52` |
| In Progress | `8439671f-0e5d-4a08-ba98-d3bf5b758d16` |

For teams other than Satchel, call `mcp__linear__linear_getWorkflowStates` with the team ID to get the correct state IDs, then match by `name`.

## Rules

- **Do this last** — after committing, pushing, creating the PR, or completing the final action.
- **Never skip** — leaving an issue in "Agent Queue" or "In Progress" after finishing is the failure mode this skill prevents.
- If the issue identifier is not known, check the `<formatted_context>` block in the session for `issue_identifier`.
- Do not move to Done if a PR is open and awaiting review — use In Review instead.
- Do not move to Blocked unless you genuinely cannot proceed without the user.
