---
name: pr-review
description: "Independent pull request review and merge gate: gathers repo context around the diff, posts severity-tagged inline findings and one summary with a 0-5 score and a PASS/FAIL verdict. Use when the Blocks PR automation fires, or when asked to review, re-review or gate a PR. Review only: never push, edit files or merge. Run on a different model family from the PR's author."
---

# PR review

You review; you never push commits, edit files, approve, or merge. Run on a different model family
from the author; the skill is the same whichever model runs it. Research behind this design:
`docs/pr-review-research.md` in global-config.

## 0. One review per head commit

Blocks can start two runs for the same commit (a push and "ready for review" together). Before
anything else:

1. Get the PR's current head SHA.
2. If a summary by you starting with `Verdict:` already shows `Head: <that short sha>`, post
   nothing, end with a `CI determination:` line (step 6) that matches its verdict, and stop.
3. Otherwise claim the head: post a comment that is exactly `PR Review claim · Head: <short sha>`
   and keep its ID. Re-list the PR's comments. Ignore claims older than 30 minutes with no
   matching `Verdict:` (a run that died). If another claim for this SHA has a lower comment ID
   than yours, another run owns this head: delete your claim, wait for its summary for this SHA
   (check every minute, up to 20 minutes), then end with a `CI determination:` that matches it and
   stop. If none appears, end with `CI determination: FAIL` and say the duplicate run never
   finished.
4. Lowest claim wins, so carry on with the review. Delete your claim after posting the summary.

A new commit has a new SHA, so it is always reviewed.

## 1. Gather context before judging

- Read the PR, its linked issue or spec (from the description or branch name, e.g. `SAT-123`), and
  the repo's `CLAUDE.md`/`AGENTS.md`. The spec defines correct; the PR description is a claim.
- For every changed function, type or route: find its callers, callees and similar code elsewhere
  (grep or the language server), at least two hops out. Check the change is consistent with them.
- `git log -L` or blame risky helpers, and `git log --grep=revert` for past breakage nearby.
- Load repo rules from `.blocks/review.md` if present (format below).

## 2. Find real defects, one hypothesis at a time

List suspected bugs, then try to disprove each against the code. Keep only findings you can pin to
`file:line` with a concrete failure (input or state, then wrong result). Target: logic errors,
unhandled failure paths, security (auth, injection, secrets), data loss, race conditions, spec
mismatches, missing tests for changed behaviour, and any edit to `tests/acceptance/` in an
implementation commit (always P1). Skip style unless a repo rule requires it. Never drop a security,
data-loss or input-validation finding to reduce noise.

Re-read the whole diff once before posting, so a later run does not "discover" what this one missed.

## 3. Post

Inline review comments, one per finding: `**P0|P1|P2 · logic|security|data|test|rule:<id>**`,
the failure in one or two sentences, then a `suggestion` block when the fix is small.
P0 = breaks production, security or data. P1 = a real bug or spec mismatch. P2 = worth fixing,
not blocking.

Then exactly one summary comment per PR. If a comment by you starting with `Verdict:` already
exists on the PR, **edit that comment** (update it in place) instead of posting a new one:

```
Verdict: PASS|FAIL · Score: N/5 · Head: <short sha>
```

then a findings table (severity, file:line, claim, link to the comment), "Outside the diff" for
issues in unchanged code, and "What I checked" when there are no findings.

Score (the `Score:` field; it is not your confidence), computed from your own findings only:
5 = no findings. 4 = P2 only. 3 = one P1. 2 = several P1 or a design problem. 0-1 = any P0. A P1 or P0 finding means the score is 3 or lower.
**PASS = score 4 or 5 on the current head with no unresolved P0/P1 thread.** Otherwise FAIL.
Changes to `.github/workflows/`, database migrations, auth, or anything the repo's CLAUDE.md
reserves for the owner are FAIL with "needs owner review" regardless of score.

## 4. On a new push

Review the full diff again, mark which findings are new, and check each earlier thread against the
head: if fixed, reply with the fixing commit and resolve it; if not, keep it in the summary. Do not
repeat a finding a human rebutted or reacted 👎 to; if you still think it matters, say so once in
the summary.

## 5. Hand a failing Blocks PR back to Blocks

Last action on GitHub, only when **all** of these hold:

- the verdict is FAIL and there is **no P0** finding (security and data-loss go to a human);
- the PR's author is the Blocks bot (`blocksorg[bot]`); never for PRs by people or Claude cloud
  sessions, which watch their own PRs;
- the PR is not a test-author PR (only adds `tests/acceptance/` or equivalent): those are red by
  design, and asking a coder to turn them green invites weakening the tests.

Count the PR's earlier comments containing `@blocks address the review comments`. Fewer than 3:
post exactly `@blocks address the review comments and update the PR` as its own comment. 3 or
more: do not mention @blocks; add the `needs-human` label and post a short summary of what still
fails after three rounds.

This needs Dashboard → Settings → GitHub → **Bot Invocations** on, because Blocks ignores
mentions from bot accounts by default. With it off the comment does nothing; say so in the summary.

## 6. Final reply: the CI determination

Blocks sets the "PR Review" check from your final reply, so end the run with a reply whose
**first line** is exactly one of:

```
CI determination: FAIL
CI determination: PASS
```

FAIL whenever any P0 or P1 is open on the current head (or the change needs owner review);
PASS only when there are none. It must match the summary's `Verdict:` line. Before replying,
check the score against your findings (any P0 → 0-1, any P1 → 3 or lower). Then list the
findings briefly. Never describe a FAIL as expected, successful or done "as intended", even
when the PR says its bugs are deliberate: the determination is about the code, not your task.

## Repo rules: `.blocks/review.md`

Optional, per repo. One rule per line:

```
- id: no-direct-db | scope: src/routes/** | severity: P1 | rule: routes call the data layer, never the DB client
```

Cite the rule id in the finding's tag. When humans repeatedly dismiss a kind of finding, propose a
rule for it in the summary for the owner to add; do not apply it yourself.
