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

### Blocks session link (SAT-889)

Every handback comment posted on a Linear issue **must include a link to the current Blocks session** as the last line before the model/effort tag. This lets Tim open the full session response directly from Linear without navigating the Blocks sidebar separately.

Construct the URL from two env vars available in every Blocks session:

```text
https://www.blocks.team/app/$BLOCKS_WORKSPACE_ID/sessions/$CLAUDE_CODE_SESSION_ID
```

Add it as a Markdown link on its own line:

```text
[Full session →](https://www.blocks.team/app/$BLOCKS_WORKSPACE_ID/sessions/$CLAUDE_CODE_SESSION_ID)
```

Replace `$BLOCKS_WORKSPACE_ID` and `$CLAUDE_CODE_SESSION_ID` with their actual runtime values — do not leave the `$VAR` placeholders in the comment. These env vars are always set in Blocks sessions; if either is missing, omit the link rather than posting a broken URL.

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
