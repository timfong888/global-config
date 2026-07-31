# global-config

Global configuration and skills for Claude Code / Blocks agents.

## Repository Structure

```
.claude/skills/       — Blocks skill definitions (loaded automatically by Claude Code)
shell/                — Shell aliases and setup scripts for workspace switching
```

## Shell Aliases (`shell/`)

Provides `cc`, `cc-aurora`, and `aurora` aliases for switching between the personal
Claude subscription workspace and the Aurora inference endpoint workspace.

See [`shell/README.md`](shell/README.md) for full setup instructions.

## Blocks Skills (`.claude/skills/`)

| Skill | Description |
|---|---|
| `canvas` | FlutterFlow Designer via canvas MCP — session setup, Lua scripting, API reference |

Skills are auto-loaded by Claude Code from `.claude/skills/<name>/SKILL.md`.
