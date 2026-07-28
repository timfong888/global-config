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
- Do not post comments on Linear issues unless explicitly asked to do so.
- Return reports, summaries, and analyses in the assistant response — not via Linear comment tools.
- Updating issue state (status, description, labels) is allowed only when explicitly instructed.

## Skills

Individual skill files live in `.claude/skills/`. Each skill is loaded via the `Skill` tool using its directory name. Skills in this repo are available globally to all Blocks agent sessions.

## Constraints

- Work only within the `workspace` directory. Create subfolders per cloned repository.
- Never commit to a repository's default branch unless explicitly instructed.
- Always clone repositories using `mcp__blocks-internal-mcp__clone_repository_into_folder`.
- Always create a pull request after pushing a new branch with code changes.
- Never force push. Never skip hooks (`--no-verify`).
