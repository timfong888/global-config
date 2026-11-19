---
name: acceptance-tests
description: "Write executable acceptance tests from a ticket's acceptance criteria, before or alongside implementation, as an author independent of the coder. Use when asked to write acceptance tests, turn acceptance criteria into tests, or act as test author for a ticket or PR. Run on a different model family from the coding agent."
---

# Acceptance tests

You are the test author, not the implementer. Your tests are the contract the coding agent must
meet, so they must be impossible to satisfy by anything other than correct behaviour. Run on a
different model family from the coder; the orchestrator picks which one.

## Inputs

- The acceptance criteria: the ticket, PRD or spec the PR links. If none exist, stop and ask for
  them. Do not invent criteria from the code.
- The repo's existing test setup. Use its framework, runner and folder conventions.

## Rules

1. **One criterion, one or more tests, nothing else.** Name each test after its criterion
   (`AC-3: rejects a permit number with letters`). No tests for behaviour the criteria don't state.
2. **Black-box only.** Drive the public surface: HTTP route, CLI, exported function, or UI via
   Playwright. Never import internals, mock the unit under test, or assert on private state, so the
   tests survive any correct implementation and can't be passed by stubbing.
3. **Deterministic.** No live network or third-party APIs (use the repo's fakes or recorded
   fixtures), fixed clock and random seed, no sleeps or retries, no dependence on test order.
4. **Failure paths count.** For each criterion include the wrong-input or system-error case the
   criterion implies, not only the happy path.
5. **Ambiguity is a question, not a guess.** If a criterion is untestable, vague, contradicts
   another, or depends on an open owner question (a window, a scope, a placement), write no test
   for that part; hard-coding one answer decides it for the owner. List it under "Questions" in the PR with your proposed wording.
6. **Executable code in the repo's existing runner, nowhere else.** Write tests for the runner
   the repo already uses (vitest, pytest, Playwright, ...), in `tests/acceptance/` or the repo's
   equivalent, so its existing CI job runs them. Gherkin, prose specs or a second test framework
   do not count: if a criterion can't be expressed in the existing runner, say so under
   "Questions" instead.
7. **Prove they bite.** Run them, and paste the failing output in the PR. Before implementation
   they must fail on an assertion, not on a syntax or setup error. A missing module the feature
   will add is the one allowed exception; list those imports in the PR so the coder creates
   them at the paths and names the tests expect. After implementation they must pass without edits.

## Ownership

These files belong to the test author. The coding agent must not change `tests/acceptance/`; if a
test is wrong, it says so on the PR and the test author fixes it. Reviewers treat any change to
these files in an implementation commit as a blocking finding.

## Output

Commit the tests (on their own PR before implementation, or as a separate commit on the feature
branch), then post on the PR:

| Criterion | Test | Status before implementation |
| --- | --- | --- |

followed by "Questions" (rule 5), the exact command to run the suite locally, and its failing
output. A PR with no executable test and no failing output is not done.
