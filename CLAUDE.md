# Global Agent Standards

These conventions apply to all Blocks agent responses posted back to Linear, GitHub, or any other surface. They are inherited by every project that references this repo.

## PR and issue references

Always hyperlink PR and issue references — never use raw URLs or plain `#N` numbers alone.

| Context | Format |
|---|---|
| Referencing a PR | `[PR #N: Title](https://github.com/owner/repo/pull/N)` |
| Referencing a commit | `[\`abc1234\`](https://github.com/owner/repo/commit/full-sha)` |
| Referencing a Linear issue | `[SAT-N: Title](https://linear.app/.../issue/SAT-N/...)` |

**Correct:**
> PR is live at [PR #5: Add CodeRabbit → Linear workflow](https://github.com/timfong888/global-config/pull/5).

**Incorrect:**
> PR is live at **https://github.com/timfong888/global-config/pull/5**.
> PR is live at PR #5.

## Comment structure

When reporting completed work back to Linear, structure comments as:

1. One-sentence summary with hyperlinked PR/resource
2. What was built (bulleted, concrete)
3. Setup steps for the human (if any)

## Branch naming

Follow the Linear-derived convention in effect for the project:
- Feature: `feature/<TEAM>-<N>-<slug>` or `blocks/<TEAM>-<N>-<slug>`
- Fix: `fix/<TEAM>-<N>-<slug>`
