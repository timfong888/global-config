---
name: linear-handback
description: Handback protocol for any Linear agent work cycle — posts Success/Needs-input/Blocked comment with correct state transition, optional Todo spin-out, and enforces the terminal-state rule. Callable from linear-worker, agent-writing, agent-admin, or any coding work cycle.
whenToUse: Load after completing work on a Linear issue to post the outcome comment and set the correct workflow state. Use from any track (writing, admin, coding), not just from the poller.
---

# /linear-handback — post outcome and hand back

## Inputs

Receive: issue `identifier`, `id`, `track`, `model`, `effort`, `HUMAN_USER_ID`, and the resolved
state IDs (`STATE_IN_REVIEW`, `STATE_NEEDS_INPUT`, `STATE_BLOCKED`, `STATE_TODO`, `TEAM_ID`)
from workspace config. When called from `linear-worker` these are handed in. When called
directly from a track skill, resolve them from the `## Agent Poll Configuration` block in the
project CLAUDE.md, or use the Satchel defaults in `linear-agent-poll`.

## Legibility rules (SAT-596)

Apply to all handback comments and descriptions. Canonical rules: global `CLAUDE.md` →
Handback Rules → Legibility rules.

## Progress file — terminal marker (SAT-508)

Write the terminal marker before posting the handback comment:
```shell
python3 tests/lib/progress_file.py write --dir state --issue <identifier> --state done
```
Best-effort only — never block the handback on it.

## Thread placement (SAT-480)

When this handback answers a specific threaded human comment, post as a nested reply in that
thread (`commentCreate` with `parentId` = thread root id). A handback for a fresh issue-level
ask stays top-level.

## Pick exactly one primary path

Route by what the ticket needs from Tim next:

1. **Success** (→ `STATE_IN_REVIEW`) — work done; Tim reviews and promotes to Done.
2. **Needs input** (→ `STATE_NEEDS_INPUT`) — a question answerable inline with a typed reply.
3. **Blocked** (→ `STATE_BLOCKED`) — work stopped; an external dependency or real-world action only Tim can perform stands between here and the finish line.

Optionally pair **Success** with a **Human-action Todo spin-out** when part of the conclusion is "Tim must go do X in the real world."

---

### Needs input

Use when what's missing is an answer Tim can type in a reply (not an external dependency — that's Blocked). Post exactly:

```text
🔴 Needs input — {one-line what you're waiting on}
> question: {the specific question} [model: {model}, effort: {effort}] (by Claude)
```

Set `assigneeId` = `HUMAN_USER_ID`, `priority` = 1 (Urgent), `stateId` = `STATE_NEEDS_INPUT`
(skip state change if `STATE_NEEDS_INPUT` is `none`). Return `needs-input: {issue}`.

Tim resumes by replying; the next tick's secondary path (A1+B2 in `linear-agent-poll`) auto-picks it up.

---

### Blocked (SAT-553)

Use when work stopped on something no typed reply can fix. Post exactly:

```text
⛔ Blocked — {one-line: what stopped the work}
- What happened: {what was attempted, in order, and where/why it stopped}
- To unblock: {the specific action or decision Tim must take}
[model: {model}, effort: {effort}] (by Claude)
```

Set `assigneeId` = `HUMAN_USER_ID`, `priority` = 1 (Urgent), `stateId` = `STATE_BLOCKED`.
If `STATE_BLOCKED` is `none`, fall back to `STATE_NEEDS_INPUT`; if that's also `none`, skip
state change and leave the issue in `STATE_IN_PROGRESS`. The `⛔ Blocked` marker still
distinguishes it in the comment either way. Return `blocked: {issue}`.

---

### Success

Set `assigneeId` = `HUMAN_USER_ID`, `stateId` = `STATE_IN_REVIEW` (never `STATE_DONE` — see
terminal-state rule), `priority` = normal. Return `done: {issue}`.

Every success comment carries two structured bullets right after the headline:

- **Deterministic / final** (coding PR, deterministic admin):
  ```text
  ✅ Done — {summary + links}.
  - What changed: {short summary}
  - Decision needed to move to Done: {none — safe to promote, or the specific check}
  [model: {model}, effort: {effort}] (by Claude)
  ```
  For a coding PR handback: `{links}` must be the full clickable URL —
  `https://github.com/<owner>/<repo>/pull/<N>` (never a bare `PR #<N>`). Add:
  ```text
  - Review on: the GitHub PR page linked above — open it to read the diff (CodeRabbit has
    already reviewed) and merge; Linear just tracks status.
  ```

- **Judgment-bearing** (writing, admin that needs your eyes):
  ```text
  ✅ Ready for review — {summary + links}.
  - What changed: {short summary}
  - Decision needed to move to Done: {what Tim needs to decide or verify}
  [model: {model}, effort: {effort}] (by Claude)
  ```

---

### Human-action Todo spin-out (SAT-553) — composes with Success

Use when the work's conclusion is that Tim must personally execute something in the real world.
**If `STATE_TODO` is `none`, skip and fold the action into the handback comment instead.**

1. **Idempotency check first.** Before creating, look for an existing spin-out:
   - Linked: `issue(id: original) { relations { nodes { relatedIssue { id identifier title state { id } } } } }`
   - Orphan fallback: `issues(filter: { team: { id: { eq: "<TEAM_ID>" } }, state: { id: { eq: "<STATE_TODO>" } }, title: { startsWith: "Action (Tim): " }, description: { contains: "<original identifier>" } }, first: 5)`
   If found, reuse it (link if not yet linked); don't create a duplicate.

2. **Create** with `issueCreate`: `teamId` = `TEAM_ID`, `stateId` = `STATE_TODO`,
   `assigneeId` = `HUMAN_USER_ID`, `projectId` = original issue's project (omit if none),
   title = `Action (Tim): {imperative action}`. Description: bullets for decision/recommendation,
   why (key trade-offs), concrete steps, and a Markdown link back to the originating issue.

3. **Link** with `issueRelationCreate` (type `related`). If this step fails after `issueCreate`,
   retry before proceeding — never hand back with a dangling unlinked spin-out.

4. The spin-out **must not** carry any routing/model/effort labels and lands in `STATE_TODO` —
   outside both A1 paths — so it is never auto-dispatched to any agent.

5. Hand the **original** back through the Success path, linking the spin-out in the
   `What changed` bullet. Return `done: {issue} (spun out {new-identifier})`.

---

## Terminal-state rule

The agent **never** sets `STATE_DONE` itself, no matter how deterministic the work looks.
Every successful completion hands back with `stateId` = `STATE_IN_REVIEW`. Only the comment
wording (`Done —` vs `Ready for review —`) signals confidence. Tim promotes to `STATE_DONE`
manually once he's reviewed it.

Only Needs-input and Blocked paths use Urgent priority. Success always uses normal priority.
