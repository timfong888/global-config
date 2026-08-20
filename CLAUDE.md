# Global Blocks Agent Instructions

This file contains global instructions that apply to every Blocks agent session launched from this repository.

## Tone and Communication

- Be concise and direct. Avoid unnecessary preamble or filler.
- Use plain Markdown in responses — assume it renders correctly.
- Do not ask follow-up questions unless absolutely necessary or explicitly instructed.
- Attempt task completion before asking for help.

## Signing Convention

When committing code associated with a Linear ticket, include the ticket identifier in the commit message:

```
SAT-123: Brief description of the change
```

## Handback Rules

- When a task is complete, summarize what changed and what is next in one or two sentences.
- Post comments on Linear issues as a human engineer would: note when starting significant work, post a brief status when completing milestones, and ask questions when blocked. Keep comments concise and substantive — skip trivial one-liners.
- Detailed reports, analyses, and research findings go in the assistant response; brief status updates and handback notes go as Linear comments.
- Updating issue state (status, description, labels) is allowed only when explicitly instructed.

### Legibility rules — comments and descriptions (SAT-596)

The reader is on a phone. Apply these to every comment and ticket description you write.

- **Answer first.** Line 1 = the outcome or decision. The reader should be able to stop there.
- **One idea per bullet, ≤ 20 words.** N items → N bullets, never a run-on sentence.
- **Bold the 2–4 load-bearing words** in each bullet so a skim-reader catches the gist. Don't bold full sentences.
- **No inline walls of code or long paths.** Put them on their own line or behind a Markdown link.
- **Depth goes behind a link, not inline.** The comment is the glance; the PR/vault note is the deep-dive.
- **Target: 5–8 short lines** per handback comment.

## Skills

Individual skill files live in `.claude/skills/`. Each skill is loaded via the `Skill` tool using its directory name. Skills in this repo are available globally to all Blocks agent sessions.

## Code Review (CodeRabbit)

Before creating any pull request, run the CodeRabbit review skill to catch bugs, security issues, and logic errors:

```
Skill: coderabbit
```

This runs a review-fix loop (at most 2 iterations) on uncommitted changes. Fix all critical and high findings before opening the PR. Skip only if `cr doctor` reports auth/config issues — in that case note it in the PR description.

The `cr` CLI is pre-installed and authenticated via the `CODERABBIT_API_KEY` environment variable in every Blocks session. If auth fails, add the key to Blocks secrets at **coderabbit.ai → Account Settings → API Keys**.

## Constraints

- Work only within the `workspace` directory. Create subfolders per cloned repository.
- Never commit to a repository's default branch unless explicitly instructed.
- Always clone repositories using `mcp__blocks-internal-mcp__clone_repository_into_folder`.
- Always create a pull request after pushing a new branch with code changes.
- Never force push. Never skip hooks (`--no-verify`).

## Checkpoint Protocol (SAT-922)

Commit and push after each discrete sub-task so partial progress is always visible on the branch.

### When to checkpoint

- After completing a data/model layer
- After completing an API endpoint or route
- After completing the UI for a feature
- After a test suite passes
- Before switching tickets

### Commit format

```
SAT-XXX: [milestone] brief description
```

Example: `SAT-123: [api] add expense upload endpoint`

### Checkpoints must be user-facing

**Work backwards from the customer experience.** A backend milestone alone is not a complete checkpoint.

- If a feature has a UI requirement, **don't stop at the API** — continue until the frontend is also done before marking the milestone.
- If the backend is not yet complete, **create a frontend mockup** (e.g., using WireMock or static fixtures) so the feature is demonstrable against a simulated backend.
- The deliverable at each checkpoint is something the user can see and interact with — not an internal service layer.

### Why

Long-running sessions risk losing all progress on crash or timeout. Frequent pushes convert an overnight run from "all or nothing" into incremental, reviewable progress visible in the morning.

## Agent Poll Configuration

Satchel workspace values for the `linear-agent-poll` skill. The skill reads this block
when invoked from any project that does not define its own `## Agent Poll Configuration`
in its local `CLAUDE.md`.

| Variable | Value |
|---|---|
| `LINEAR_ACCOUNT` | `satchel-linear` |
| `TEAM_ID` | `88661a7f-d07e-4590-9724-b8f69e30556e` |
| `TEAM_KEY` | `SAT` |
| `WORKSPACE_SLUG` | `sophia-xyz` |
| `STATE_AGENT_QUEUE` | `73be9b83-4bd2-4ef1-97a7-0ff6e6ff5339` |
| `STATE_IN_PROGRESS` | `8439671f-0e5d-4a08-ba98-d3bf5b758d16` |
| `STATE_IN_REVIEW` | `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` |
| `STATE_DONE` | `299e627d-3989-40c4-8aea-b9d56209fa39` |
| `STATE_NEEDS_INPUT` | `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` |
| `STATE_BLOCKED` | `f68b9fad-0d13-4397-b1e0-97f6e7216e52` |
| `STATE_TODO` | `4dfa455d-9248-4b2b-b3de-4d0d343efe21` |
| `HUMAN_USER_ID` | `aa3fb002-ba6c-440f-8837-cc5c92a3c748` |
| `ROUTING_LABELS` | agent-coding `b4c6b47e-0ded-4468-a68c-4d3a5b58ec33` · agent-writing `79adef88-4350-48c2-a1da-31137a2dfbc8` · agent-admin `a1a9437b-8c75-4cd5-ba6b-5c1fb4443f00` |
| `CODING_REPO_ROOT` | `Claude and Local Agentic System` → `/home/user/workspace/global-config` |
