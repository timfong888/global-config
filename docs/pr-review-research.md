# How the `pr-review` skill was designed

`pr-review` replaces Greptile (cancelled 2026-11-16 for cost) with a skill run by the Blocks PR
automation (Codex since 2026-11-17; Kimi before that). If the automation can't run, wait and report; use Kimi only when asked for high-value work (Tim, 2026-11-18, on cost). This note records what Greptile publicly says about its approach and what the
skill takes from it. Public sources only; no prompts were copied. Researched 2026-11-16.

## What Greptile does

| Area | Greptile's approach | Source |
|---|---|---|
| Repo context | Parses the repo into a graph of files, functions, classes and their calls/imports; for each changed function it looks up callers, callees and similar code. Search embeds per-function natural-language descriptions, not raw code. | [graph context](https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context.md), [semantic search](https://www.greptile.com/blog/semantic-codebase-search) |
| Agentic review | v3 replaced a fixed pipeline with an agent loop that searches, follows calls several files deep, reads git history and learned rules. v5 runs parallel sub-agents, each testing one suspected bug. | [v3](https://www.greptile.com/blog/greptile-v3-agentic-code-review), [changelog](https://www.greptile.com/changelog) |
| Project knowledge | Keeps an architecture index, per-module risk notes and a list of past revert/incident PRs; reads CLAUDE.md, .cursorrules and linked tickets. | [knowledge bases](https://www.greptile.com/docs/how-greptile-works/knowledge-bases.md), [series A](https://www.greptile.com/blog/series-a) |
| Confidence score | 0-5: 5 merge, 4 minor polish, 3 address feedback, 2 significant bugs, 0-1 critical. Based on issue count and severity, change complexity and fit with existing patterns. | [first PR review](https://www.greptile.com/docs/code-review/first-pr-review.md) |
| Merge gate | Auto-approve only on 5/5 within a risk ceiling; never on drafts, mid-review pushes or `do-not-merge` labels; a new push withdraws approval. | [auto-approve](https://www.greptile.com/docs/code-review/auto-approve-prs.md) |
| Output | Summary with score and verdict first, findings by severity linked to inline comments, a section for issues outside the diff, "what we checked" when clean, an optional diagram. Inline comments carry P0/P1/P2 and logic/syntax/style plus a suggested fix. | [first PR review](https://www.greptile.com/docs/code-review/first-pr-review.md), [changelog](https://www.greptile.com/changelog) |
| Noise control | Strictness 1-3, comment-type filters, ignore patterns. Main precision gain: the agent challenges its own hypotheses before commenting. Reviewing with a different model family from the author raised catch rate about 10%. | [nitpickiness](https://www.greptile.com/docs/code-review/controlling-nitpickiness.md), [build a review agent](https://www.greptile.com/blog/how-to-build-a-code-review-agent) |
| Learning | 👍/👎 and replies; a comment type ignored 3+ times is suppressed, except security, null-pointer and validation; proposes rules from human reviews for an admin to approve. | [training](https://www.greptile.com/docs/code-review/training-the-learning-system.md), [nitpicks](https://www.greptile.com/docs/how-greptile-works/nitpicks.md), [memory](https://www.greptile.com/docs/how-greptile-works/memory-and-learning.md) |
| Custom rules | `.greptile/` per directory (`config.json`, `rules.md`, `files.json`); rules have id, rule, scope globs and severity; nearest config wins, rules accumulate. | [config](https://www.greptile.com/docs/code-review/greptile-config.md), [custom standards](https://www.greptile.com/docs/code-review/custom-standards.md) |
| Evaluation | Own benchmark: 50 real bug-fix PRs, 82% caught. Independent tests rank it lower (Macroscope 23.6% with access cut mid-test; Signal65 fewest true positives, 86% precision). | [benchmarks](https://www.greptile.com/benchmarks), [Macroscope](https://macroscope.com/blog/code-review-benchmark), [Signal65](https://signal65.com/wp-content/uploads/2026/03/Signal65-Insights_Evaluating-AI-Code-Review-Tools.pdf) |

## What `pr-review` keeps, and what it drops

Kept: context gathering two hops out from each changed symbol, plus git history and the linked
spec; hypothesis-then-disprove before commenting; P0/P1/P2 severity and finding type; one
summary with a 0-5 score, verdict and head SHA; "outside the diff" and "what I checked"; full
re-review on each push that resolves fixed threads and never repeats rebutted findings; path-scoped
repo rules with ids; proposing (not silently applying) rules learned from dismissals; never
suppressing security, data-loss or validation findings.

Dropped: a persistent code graph and embeddings index (the agent greps and reads the checkout on
each run instead; slower, no infrastructure); automatic suppression from reaction history (no
store to keep it in); diagrams (low value for these repos).

Repo rules live in `.blocks/review.md`, the file Blocks' own PR Review setting uses as its prompt.
Keep that setting off while the automation runs `pr-review`, or the repo rules become a second,
conflicting prompt.
