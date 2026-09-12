---
name: linear-tldr
description: Post a brief TLDR handback comment to a Linear issue after completing a directly-delegated session — especially when the full output lives in the assistant response rather than as a Linear comment. Transitions the ticket to In Review and subscribes the user. Load at the end of any directly-delegated session before ending (see COMPLETION ENFORCEMENT in CLAUDE.md).
whenToUse: Load at the end of every directly-delegated session to post a compact summary comment and transition state to In Review. Especially important for writing/research/admin tracks where the detailed output is in the assistant response, not posted to Linear. The linear-worker handback path handles poller-dispatched tickets; this skill covers direct @blocks mentions that don't go through the full worker flow.
---

# /linear-tldr — compact handback comment + state transition

## When to use

Call this skill before ending any directly-delegated session (direct `@blocks` mention or direct comment). It is the counterpart to the In Progress enforcement: just as the first tool call must set In Progress, the last substantive action must post a TLDR and set In Review.

**Skip only if `linear-handback` was already called this session** — that skill owns the state transition and comment in the full poller worker flow. Do not call both.

Signs that `linear-handback` already ran and this skill should be skipped:
- A `✅ Done —`, `✅ Ready for review —`, `⛔ Blocked —`, or `🔴 Needs input —` comment was already posted to the Linear issue this session

Poller-origin alone is not sufficient evidence — `linear-handback` must have actually completed and posted its outcome marker. If no outcome comment exists yet, call this skill regardless of how the session was dispatched.

## Inputs

Resolve from the workspace `## Agent Poll Configuration` block in CLAUDE.md first; fall back to `<formatted_context>` in the session. Use the Satchel defaults below only when neither source provides a value:

| Input | Source |
|---|---|
| `issue_identifier` | `formatted_context.issue_identifier` (e.g. `SAT-1047`) |
| `STATE_IN_REVIEW` | Config block → `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` (Satchel) |
| `STATE_BLOCKED` | Config block → `f68b9fad-0d13-4397-b1e0-97f6e7216e52` (Satchel) |
| `HUMAN_USER_ID` | Config block → `aa3fb002-ba6c-440f-8837-cc5c92a3c748` (Satchel) |
| `BLOCKS_WORKSPACE_ID` | env var `$BLOCKS_WORKSPACE_ID` |
| `CLAUDE_CODE_SESSION_ID` | env var `$CLAUDE_CODE_SESSION_ID` |
| `model` | Describe the active model (e.g. `claude-sonnet-4-6`, `claude-opus-4-8`) |
| `effort` | Describe the active effort level (e.g. `high`, `medium`) |

If `issue_identifier` is not available in `<formatted_context>`, skip posting the comment but note the omission in your response.

For non-Satchel teams, call `mcp__linear__linear_getWorkflowStates` with the team ID and match by name to get the correct state IDs.

## Steps

### 1. Compose the TLDR comment

Distill the session's work into 5–8 lines following the legibility rules (CLAUDE.md → Legibility rules):

- **Line 1: Answer first** — one sentence stating the outcome or decision. Reader should be able to stop here.
- **Bullets:** 2–4 load-bearing bullets. Bold 2–4 words per bullet. One idea per bullet, ≤ 20 words.
- **Session link:** `[Full session →](https://www.blocks.team/app/{BLOCKS_WORKSPACE_ID}/sessions/{CLAUDE_CODE_SESSION_ID})` — substitute real env var values; omit the line if either env var is missing.
- **Sign-off:** `[model: {model}, effort: {effort}] (by Claude)`

**Template:**

```text
✅ Done — {one-sentence outcome}.
- **{Key result 1}:** {what was found/done, ≤ 20 words}
- **{Key result 2}:** {what was found/done, ≤ 20 words}
- **Next:** {what Tim should do or decide}
[Full session →](https://www.blocks.team/app/{BLOCKS_WORKSPACE_ID}/sessions/{CLAUDE_CODE_SESSION_ID})
[model: {model}, effort: {effort}] (by Claude)
```

Adapt the opener for non-success outcomes:
- **Needs input:** `🔴 Needs input — {one-line question}` — use when the question can be answered by a typed reply inline; state = `STATE_IN_REVIEW`, priority = Urgent
- **Blocked:** `⛔ Blocked — {one-line what stopped it}` — use when work stopped on something a typed reply alone cannot fix (external dependency, missing access, purchase); state = `STATE_BLOCKED`, priority = Urgent

Content by track:
- **Research/analysis:** bullets summarize key findings, not methodology
- **Admin:** bullets list what changed/created/filed
- **Coding:** include a hyperlinked PR reference if one was created

### 2. Transition state and subscribe

**State before comment** — call `mcp__linear__linear_updateIssue` first:

| Outcome | `stateId` | `priority` |
|---|---|---|
| Success | `STATE_IN_REVIEW` | normal (3) |
| Needs input | `STATE_IN_REVIEW` | Urgent (1) |
| Blocked | `STATE_BLOCKED` | Urgent (1) |

Always include:
- `id`: the issue identifier
- `subscriberIds`: [`HUMAN_USER_ID`]

### 3. Post the comment

Use `mcp__linear__linear_createComment` with `issueId` = the issue identifier and `body` = the composed comment.

### 4. Return

Return `tldr-posted: {issue_identifier}` to signal completion.

## What not to do

- **Do not paste the full session output into the comment.** The TLDR is the comment; the full detail is in the Blocks session (linked via the session URL).
- **Do not set `STATE_DONE`.** Only Tim promotes to Done.
- **Do not skip subscribing the user.** A state change the user never sees is not a handback ([SAT-762](https://linear.app/sophia-xyz/issue/SAT-762)).
- **Do not call this if `linear-handback` was already called** — that skill owns the state transition for the full poller worker path.
