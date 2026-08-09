# global-config

Global configuration repository for Blocks agent sessions.

## Purpose

This repository provides shared, reusable configuration that Blocks loads into every agent session. It centralises:

- **Global instructions** (`CLAUDE.md`) — tone, commit conventions, handback rules, and constraints that apply to every session.
- **Skills** (`.claude/skills/`) — individual skill files that agents can load on demand via the `Skill` tool.

## How Blocks Picks This Up

Blocks is configured to mount this repo as a global config source. When an agent session starts, Blocks reads `CLAUDE.md` from this repo and injects it as standing instructions. Skills in `.claude/skills/` become available to the `Skill` tool across all sessions.

## Repository Structure

```
global-config/
├── CLAUDE.md               # Global agent instructions
├── README.md               # This file
└── .claude/
    └── skills/             # Individual skill files
        └── canvas/
            └── SKILL.md    # FlutterFlow Designer canvas skill
```

## Adding a New Skill

1. Create a directory under `.claude/skills/<skill-name>/`.
2. Add a `SKILL.md` file with a YAML frontmatter block:
   ```yaml
   ---
   name: <skill-name>
   description: <one-line description used to decide relevance>
   ---
   ```
3. Write the skill content below the frontmatter.
4. Open a PR — once merged, the skill is available globally.

## Related Issues

- Parent: Enable Blocks to use the skills and capabilities of the linear-agent-poller
- SAT-636: Add compact canvas skill
- SAT-639: Initialize this repo structure (this ticket)
