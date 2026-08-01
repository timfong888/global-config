---
name: mem0
description: Cross-platform persistent memory via mem0 Platform, shared across Claude Code, Claude Desktop, and other connected AI tools. Activate when user says "mem0", "remember this across tools", "cross-platform memory", or "/mem0".
---

# mem0 — Cross-Platform Memory

## Tools

`mcp__mem0__mem0_add`, `mcp__mem0__mem0_search`, `mcp__mem0__mem0_get_all`, `mcp__mem0__mem0_delete`, `mcp__mem0__mem0_update`

## Safety

- Refuse `mem0_add` for secrets: API keys, passwords, access/refresh/session tokens, private keys, and similar credentials. Decline and say why instead of storing them.
- Don't echo sensitive text back in the stored-confirmation — summarize what was stored rather than repeating the literal value when content is sensitive.
- For other sensitive personal data (health, financial specifics, someone else's private info), get the user's explicit consent before calling `mem0_add`, even when their phrasing already sounds like a command.

## Commands

- `/mem0 remember <text>` → `mem0_add(text)`, subject to Safety above. Confirm what was stored.
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

- Resolve `user_id` at runtime from a stable, explicitly configured identity (a documented account/config value, or an identity the user states outright) — not `$USER`. `$USER` is a local process value, not a provider identity: it collides when two accounts share an OS username, and splits one person's memories when the same account runs under different usernames across machines. Use the literal `"tim"` only as a last-resort fallback when nothing else resolves, and say explicitly that you're falling back — that pool is shared by anyone else who also has no configured identity, not private to one person.
- For project- or workspace-scoped recall, namespace the identity instead of using a bare `user_id`, e.g. `"<identity>:<project-or-workspace>"`, so unrelated projects don't collide in the same memory pool.
- Separate from Claude Code's file-based project memory (`~/.claude/projects/.../memory/`) — mem0 is the cross-tool layer; project memory is Claude-Code-only.
