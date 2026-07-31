---
name: mem0
description: Cross-platform persistent memory via mem0 Platform, shared across Claude Code, Claude Desktop, and other connected AI tools. Activate when user says "mem0", "remember this across tools", "cross-platform memory", or "/mem0".
---

# mem0 — Cross-Platform Memory

## Tools

`mcp__mem0__mem0_add`, `mcp__mem0__mem0_search`, `mcp__mem0__mem0_get_all`, `mcp__mem0__mem0_delete`, `mcp__mem0__mem0_update`

## Commands

- `/mem0 remember <text>` → `mem0_add(text)`. Confirm what was stored.
- `/mem0 recall <query>` or `/mem0 search <query>` → `mem0_search(query)`. Show content, ID, creation date.
- `/mem0 list` → `mem0_get_all()`. Numbered list with IDs.
- `/mem0 delete <memory_id>` → `mem0_delete(id)`. Confirm deletion.
- `/mem0 update <memory_id> <new text>` → `mem0_update(id, text)`.
- `/mem0` alone → show this summary.

## Output format

```text
1. [memory content] (id: abc123..., created: 2026-03-13)
2. [memory content] (id: def456..., created: 2026-03-12)
```

## Notes

- Resolve `user_id` at runtime — prefer the authenticated account identity (OS user / `$USER` / an explicit identity the user gives you). Use the literal `"tim"` only as an explicit fallback when no identity resolves and this is a known single-user install; never hardcode it for a shared or multi-user install, or every user reads and writes the same memory namespace.
- For project- or workspace-scoped recall, namespace the identity instead of using a bare `user_id`, e.g. `"<identity>:<project-or-workspace>"`, so unrelated projects don't collide in the same memory pool.
- Separate from Claude Code's file-based project memory (`~/.claude/projects/.../memory/`) — mem0 is the cross-tool layer; project memory is Claude-Code-only.
