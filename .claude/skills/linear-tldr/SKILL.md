---
name: linear-tldr
description: Post a brief TLDR handback comment to a Linear issue after completing a directly-delegated session — especially when the full output lives in the assistant response rather than as a Linear comment. Transitions the ticket to In Review and subscribes the user. Load at the end of any directly-delegated session before ending (see COMPLETION ENFORCEMENT in CLAUDE.md).
whenToUse: Load at the end of every directly-delegated session to post a compact summary comment and transition state to In Review. Especially important for writing/research/admin tracks where the detailed output is in the assistant response, not posted to Linear. The linear-worker handback path handles poller-dispatched tickets; this skill covers direct @blocks mentions that don't go through the full worker flow.
---

# /linear-tldr — compact handback comment + state transition

## When to use

Call this skill before ending any directly-delegated session (direct `@blocks` mention or direct comment). It is the counterpart to the In Progress enforcement: just as the first tool call must set In Progress, the last substantive action must post a TLDR and set In Review.

**Skip only if `linear-handback` was already called this session** — that skill owns the state transition and comment in the full poller worker flow. Do not call both.

Signs that `linear-handback` already ran this session:
- The session was dispatched via the poller (`linear-agent-poll` or `linear-worker` skills were loaded)
- A `✅ Done —` or `⛔ Blocked —` comment was already posted to the Linear issue this session

If neither sign is present, call this skill.

## Inputs

Resolve from the session's `<formatted_context>` or the workspace `## Agent Poll Configuration` block:

| Input | Source |
|---|---|
| `issue_identifier` | `formatted_context.issue_identifier` (e.g. `SAT-1047`) |
| `STATE_IN_REVIEW` | Config block or `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` (Satchel default) |
| `HUMAN_USER_ID` | Config block or `aa3fb002-ba6c-440f-8837-cc5c92a3c748` (Satchel default) |
| `BLOCKS_WORKSPACE_ID` | env var `$BLOCKS_WORKSPACE_ID` |
| `CLAUDE_CODE_SESSION_ID` | env var `$CLAUDE_CODE_SESSION_ID` |
| `model` | Describe the active model (e.g. `claude-sonnet-4-6`, `claude-opus-4-8`) |
| `effort` | Describe the active effort level (e.g. `high`, `medium`) |

If `issue_identifier` is not available in `<formatted_context>`, skip posting the comment but still note the omission in your response.

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
- **Needs input:** `🔴 Needs input — {one-line question}` — set priority Urgent
- **Blocked:** `⛔ Blocked — {one-line what stopped it}` — set priority Urgent

Content by track:
- **Research/analysis:** bullets summarize key findings, not methodology
- **Admin:** bullets list what changed/created/filed
- **Coding:** include a hyperlinked PR reference if one was created

### 2. Post the comment

Use `mcp__linear__linear_createComment` with `issueId` = the issue identifier and `body` = the composed comment.

### 3. Transition state and subscribe

Call `mcp__linear__linear_updateIssue` with:
- `id`: the issue identifier
- `stateId`: `STATE_IN_REVIEW`
- `subscriberIds`: [`HUMAN_USER_ID`]

For Needs input or Blocked outcomes, also set `priority: 1` (Urgent).

### 4. Return

Return `tldr-posted: {issue_identifier}` to signal completion.

## What not to do

- **Do not paste the full session output into the comment.** The TLDR is the comment; the full detail is in the Blocks session (linked via the session URL).
- **Do not set `STATE_DONE`.** Only Tim promotes to Done.
- **Do not skip subscribing the user.** A state change the user never sees is not a handback (SAT-762).
- **Do not call this if `linear-handback` was already called** — that skill owns the state transition for the full poller worker path.
