---
name: agent-admin
description: Admin handler for the Linear agent poller — routes email triage, Obsidian vault filing, and LogSeq todo processing. Email is draft-only (never send). Vault uses inbox-triage + move-to-obsidian (PARA) with CHANGELOG logging. LogSeq todos are proposed as a batch and only become Linear issues on explicit approval.
whenToUse: Load this skill when the linear-agent-poll tick routes an issue to the admin track (agent-admin label or inferred from description as email triage, vault filing, or LogSeq todo processing).
---

# Profile: agent-admin (email / vault / LogSeq handler)

The admin handler for `/linear-agent-poll` (Satchel SAT-349). The tick routes here
when the picked-up issue carries the `agent-admin` label (or the request is
inferred as email triage, vault filing, or LogSeq todo processing). You have
already posted the pickup comment and moved the issue to In Progress — this
profile is step 6 ("Do the work") and step 7 ("Report").

**Reuse, don't reimplement** where a skill already exists (`move-to-obsidian`).
Work from the ticket description + its comments only — never load the whole vault
or the whole mailbox. Sign every comment `(by Claude)`.

**Image capability.** If an admin ticket needs a generated or edited image, load the
**`capability-image`** skill (Skill tool) and follow its pipeline
(generate → download → host → attach → report cost) rather than reinventing it —
[SAT-491](https://linear.app/sophia-xyz/issue/SAT-491).

**The trust boundary is the point.** Draft-only email and propose-first LogSeq are
not friction to route around — they're why this handler is safe to leave
unattended. Never send mail, never delete/archive without listing it as a proposal
first, never create a Linear/GitHub item off a LogSeq todo without Tim's explicit
approval of that batch.

## 1. Sub-type router

Classify the ticket (description + newest comment) into exactly one of `email` /
`vault` / `logseq` by intent keywords (inbox, thread, reply → email; file, note,
organize, PARA, inbox-triage → vault; journal, todo, TODO, LogSeq → logseq). Honor
an explicit `subtype: email|vault|logseq` token in the ticket if present — it
overrides inference.

**Ambiguous → stop.** Post one `> question:` naming the sub-types you can't choose
between, set `priority` = 1 (Urgent), `stateId` = In Review, end the tick. Don't guess
a sub-type — a wrong guess on this branch means wrong tools and wrong guardrails downstream.

## 2. (a) Email procedure — DRAFT ONLY, NEVER SEND

- **Account:** `composio-personal` Gmail. **Tools:** `GMAIL_FETCH_EMAILS` (search) →
  `GMAIL_CREATE_EMAIL_DRAFT`. Never a send tool, never a browser into Gmail.
- **Scope:** take the search query from the ticket (e.g.
  `is:unread newer_than:7d -category:promotions`). If the ticket gives no scope,
  ask via `> question:` rather than guessing a window — an unscoped fetch can pull
  in anything.
- **Per thread**, classify into exactly one of **needs-reply · needs-read ·
  ignore**. For `needs-reply`, create a Gmail **draft** reply (never send). For
  `needs-read` / `ignore`, no draft — just report.
- **Archive / label / delete are proposals only.** List each in the report; execute
  none of them.
- **Idempotency:** before drafting, check for an existing draft on the thread (a
  prior `GMAIL_CREATE_EMAIL_DRAFT` already targeted it) — skip if found so re-runs
  don't stack duplicate drafts on the same thread.
- **Standing rule:** never drive a browser into a bank/brokerage/financial portal
  (per `feedback_no_agent_financial_browser` — Tim downloads, the agent files).
  This never applies to Gmail itself, only to any financial site a thread might
  link to.
- **Edge cases:** Gmail auth failure → `> question:` + Urgent handback, don't
  retry silently. Zero matching threads → not an error; report "no matching
  threads" and proceed to the structured report (§5).
- **Report contribution:** a table — `subject · recipient · 1-line gist` — for
  every draft created, plus a bullet list of proposed archive/label/delete actions.

## 3. (b) Vault procedure

- **Source:** `inbox-triage` over `01-Inbox/`. For each item, run `move-to-obsidian`
  to resolve its PARA destination.
- **Confident match** (clear PARA category, per `move-to-obsidian`'s classification
  rules) → move the file and **log it to `CLAUDE-CHANGELOG.md`** in the same run,
  newest entry on top, per the vault's mutation-logging convention.
- **Ambiguous** → do **not** guess. Leave the file in `01-Inbox/`, add/confirm
  `needs_review: true` in its frontmatter, and list it in the report instead of
  moving it.
- **Deletes are proposals only** — never delete a vault file; list it as a proposed
  delete in the report.
- **Idempotency:** a file that has already been moved is gone from `01-Inbox/`, so
  a re-run naturally can't re-move it. A file left flagged `needs_review: true`
  will keep surfacing in the report until Tim resolves it — that's expected
  re-surfacing, not a duplicate-write bug; don't suppress it.

## 4. (c) LogSeq procedure — personal, propose-first

Do **not** use the `logseq-todo-process` skill — it is retired. This procedure
replaces it for personal use.

**Where the list lives:** aged todos stay a list *in LogSeq* —
`03-LogSeq/journals/`. This procedure reads that list; it does not move or copy it
elsewhere in the vault.

**Where they now land:** each aged todo becomes a Linear **Todo**-state issue,
assigned to Tim, in the matching Satchel project if one can be confidently
inferred — or with **no project set** if it can't (Satchel does not have Triage
enabled, so "no project" is the practical equivalent of triage: it's an unsorted
issue Tim can re-project himself). Never guess a project.

### Step 1 — Scan (build the list)

Read `03-LogSeq/journals/*.md` for unresolved `TODO` / `DOING` lines dated more
than **3 days** ago (override with a `logseq_age_days: N` token in the ticket).
Skip any line that:
- is already `DONE`, or
- already carries an inline Linear link (`[SAT-`), meaning it was already
  processed by a prior run.

Consult `03-LogSeq/CLAUDE.md`'s tag → folder routing map for any `#tag` on the
todo — it's a signal for project inference in Step 2, not an instruction to move
content.

### Step 2 — Infer a project (confidently, or not at all)

For each surviving todo, query the Satchel team's live project list
(`LINEAR_RUN_QUERY_OR_MUTATION`, `team.projects`) and look for an unambiguous
textual match between the todo's content/tag and a project name (e.g. a todo
tagged `#401k` pointing at retirement planning, or a todo whose text names a
project verbatim). Require a clear, single match — if two projects are
plausible, or nothing clearly fits, leave the project unset. **Never guess.**

### Step 3 — Propose the batch (propose-first gate — US-4)

Build one batch table, one row per surviving todo:

| # | Todo | Journal date | Proposed project | Notes |
|---|------|--------------|------------------|-------|
| 1 | <todo text> | 2026-06-25 | Admin: Email, Calendar, Scheduling *(or "— none, needs triage")* | <tag/signal used, if any> |

Post it as **one** `> question:` ("Approve creating these N Linear Todo issues?
Reply with approve-all, a list of row numbers to approve, or edits."), set
`priority` = 1 (Urgent), `stateId` = In Review, end the tick. **Create nothing yet.**
This is the hard gate — no Linear or GitHub item exists until Tim's explicit approval
comment lands.

### Step 4 — Create on approval (resume)

On resume, read Tim's reply. Create a Linear issue (`issueCreate`) only for the
approved rows:
- `teamId`: Satchel `88661a7f-d07e-4590-9724-b8f69e30556e`
- `assigneeId`: @timfong888 `aa3fb002-ba6c-440f-8837-cc5c92a3c748` (always Tim —
  never @agentfong; these are his personal todos, not agent work)
- `stateId`: Todo `4dfa455d-9248-4b2b-b3de-4d0d343efe21`
- `projectId`: the inferred project from Step 2, or omit entirely if none
- `title` / `description`: the todo text, plus the source journal date and an
  `obsidian://` link back to the journal file for traceability

Before each create, defensively search for an existing issue with the same title
in Satchel (`searchIssues`) to guard against a double-approval or a re-run
re-processing the same reply — skip if found.

**Update the journal (idempotency + audit):** after a successful create, append
the new issue's link inline to that TODO line in the journal file, e.g.
`- TODO <text> [SAT-123](https://linear.app/sophia-xyz/issue/SAT-123)`. This is
what Step 1's "already processed" skip checks on the next scan, and it's how the
todo stays traceable from LogSeq. Rejected/edited-out rows get **no** link and
will resurface in the next scan unless Tim resolves them directly in LogSeq.

**No GitHub issues.** This procedure creates Linear issues only.

## 5. Cross-cutting

- **Idempotency:** every sub-type checks for prior work before acting (existing
  draft, file no longer in inbox, existing Linear link) so a re-run of the same
  tick is a no-op on anything already done.
- **Headless:** any genuine missing-input/confirm moment (missing email scope,
  ambiguous sub-type, the LogSeq approval gate) is exactly **one** `> question:` +
  set `priority` = 1 (Urgent), `stateId` = In Review, and end the tick. Never stall
  silently, never ask more than once per blocker.
- **Audit:** vault file mutations → `CLAUDE-CHANGELOG.md` (same run). Email drafts
  and LogSeq proposals/creates → enumerated in the report comment (§6) — there's
  no vault file for those, so the comment *is* the audit trail.

## 6. Report & hand back (tick step 7)

Every run — regardless of sub-type — closes with one structured comment, three
labeled sections (US-5), signed `(by Claude)`:

```
## Done
- <drafts created / files moved / issues created, one line each, with links>

## Pending Approval
- <the LogSeq batch table, if awaiting Tim's reply — omit section if none>

## Skipped
- <ambiguous inbox items left in 01-Inbox/, ignored email threads, todos with no
  confident project — one line each, with reason>
```

Omit a section entirely if it's empty rather than showing it blank.

Handback = set `stateId` to `STATE_IN_REVIEW` — never change the assignee (per B6 in the `linear-agent-poll` skill):
- **Pending Approval is non-empty** (the LogSeq gate, or missing scope) →
  `> question:` with the batch/ask, `priority` = 1 (Urgent), `stateId` = In
  Review. Return `needs-input: {issue}`.
- **Otherwise** (Done and/or Skipped only — no open question) → `✅ Ready for
  review — {one-line summary}. (by Claude)`, `stateId` = In Review, `priority` =
  normal. Admin output bears judgment (a filed note, a drafted reply) even when
  nothing is blocked, so it goes to **In Review**, not Done — Tim still looks.

Cross-issue references use a clickable Markdown link, never a bare identifier —
see `linear-agent-poll`'s link convention.

## Acceptance criteria (SAT-349)

1. Email ticket → Gmail drafts only, 0 sends, each reported with subject+recipient
   — §2, §6.
2. Missing input → exactly one `> question:`, set `priority` = 1 (Urgent), `stateId` = In Review, end — no
   silent stall — §1, §2, §5.
3. Vault ticket → every moved/created file has a same-run `CLAUDE-CHANGELOG.md`
   entry; ambiguous notes stay in `01-Inbox/` flagged `needs_review` — §3.
4. LogSeq ticket → no Linear/GitHub item created until Tim approves the proposed
   batch table — §4 Step 3/4.
5. Every run ends with a Done / Pending Approval / Skipped report comment — §6.
6. Re-running the same ticket produces no duplicate drafts/moves/tickets — §2, §3,
   §4 idempotency notes, §5.
7. This skill exists and the `linear-agent-poll` skill's B3 row points to it.
