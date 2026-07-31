---
name: mem0
description: Cross-platform persistent memory via mem0 Platform, shared across Claude Code, Claude Desktop, and other connected AI tools. Activate when user says "mem0", "remember this across tools", "cross-platform memory", or "/mem0".
---

# mem0 — Cross-Platform Memory

## Tools

`mcp__mem0__mem0_add`, `mcp__mem0__mem0_search`, `mcp__mem0__mem0_get_all`, `mcp__mem0__mem0_delete`, `mcp__mem0__mem0_update`

## Safety

These rules apply to **every write** — `mem0_add` and `mem0_update` alike. An update writes the
same persistent store, so replacement text gets screened exactly like new text.

- Refuse the write for secrets: API keys, passwords, access/refresh/session tokens, private keys, and similar credentials. Decline and say why instead of storing them.
- Don't echo sensitive text back in the confirmation — for both add and update, say which memory changed and summarize it rather than repeating the literal value.
- For other sensitive personal data (health, financial specifics, someone else's private info), get the user's explicit consent before writing, even when their phrasing already sounds like a command.

## Commands

- `/mem0 remember <text>` → `mem0_add(text)`, subject to Safety above. Confirm what was stored.
- `/mem0 recall <query>` or `/mem0 search <query>` → `mem0_search(query)`. Show content, ID, creation date.
- `/mem0 list` → `mem0_get_all()`. Numbered list with IDs.
- `/mem0 delete <memory_id>` → `mem0_delete(id)`. Confirm deletion.
- `/mem0 update <memory_id> <new text>` → `mem0_update(id, text)`, subject to Safety above. Confirm which memory changed without echoing the new text.
- `/mem0` alone → show this summary.

## Output format

```text
1. [memory content] (id: abc123..., created: 2026-03-13)
2. [memory content] (id: def456..., created: 2026-03-12)
```

## Notes

- **`user_id` must come from an authenticated identity, and there is no fallback.** Resolve it from
  the mem0 provider or the host's authenticated account (the identity the API key is issued to), not
  from anything the caller asserts. A user-stated name and `$USER` are both unauthenticated strings:
  whoever types them gets that memory pool, so treating either as an identity lets one caller read,
  overwrite, and delete another person's memories. (`$USER` is also unstable — it collides across
  accounts sharing an OS username and splits one account across machines.) A shared literal like
  `"tim"` is the same problem with a default value, so don't use one.
- If no authenticated identity resolves, **refuse** — no search, get_all, update, or delete. Say that
  mem0 isn't authenticated and point at `composio whoami` / the provider's auth step. Failing closed
  is required: guessing a namespace on a recall is what exposes someone else's memories.
- Namespace only *after* the identity is established. For project- or workspace-scoped recall use
  `"<authenticated-identity>:<project-or-workspace>"`, so unrelated projects don't collide.
- Separate from Claude Code's file-based project memory (`~/.claude/projects/.../memory/`) — mem0 is the cross-tool layer; project memory is Claude-Code-only.
