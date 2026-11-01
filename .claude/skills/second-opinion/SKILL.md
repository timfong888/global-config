---
name: second-opinion
description: Independent review of a PR diff by a different model family than the author. Use when asked for a second opinion or independent review of a PR. Review only, never commit.
---

# Second opinion

Review the PR diff against the linked issue or spec. Do not push commits, edit files, or resolve threads.

1. Find the spec. Use the Linear issue from the branch name (for example SAT-123) or the spec file the PR references. Read the issue and the diff first.
2. Do not rely on the PR description or the author's commit messages as evidence of correctness. Judge the diff on its own.
3. Then read existing PR comments, including bots such as CodeRabbit, so you do not repeat them.
4. Find real defects only: logic errors, unhandled failure paths, security issues, spec mismatches, and missing tests for changed behavior. Skip style nits.
5. Post one PR comment with a table of severity (high, med, low), file and line, claim, and evidence.
6. End the comment with a section titled "Not raised by other reviewers" listing findings that no existing comment mentions.
7. If nothing material is found, say so plainly. Do not invent findings.
