---
name: canvas
description: Use when working with FlutterFlow Designer via the canvas MCP. Covers session setup, Lua scripting, and the compact API reference for all modules.
---

# FlutterFlow Designer — Canvas Skill

## Session Setup

```
mcp__flutterflow-designer__create_session
  agent_name: "<short task name>"
  integration_host: "claudeCode"
```

Returns `sessionId` (not `session_id`) and `toolGuideMarkdown` (large — skip reading it; use this reference + `help.*` instead).

One session per agent. Reuse `sessionId` for all `call_design_script` calls in the conversation.

```
mcp__flutterflow-designer__call_design_script
  session_id: <sessionId from above>
  script: <Lua>
  args: <optional JSON → available as `args` in Lua>
```

## Prerequisites

- FlutterFlow Designer desktop app must be running locally. If session/script calls fail, tell the user to open it — do not retry.

---

## Lua API — Compact Reference

Explore any module on demand instead of loading the full guide:

```lua
help.modules()          -- list all available modules
help.module("design")   -- list functions in a module
help.fn("node", "get")  -- get signature for a specific function
```

### Module Overview

| Module | Purpose |
|---|---|
| `design` | Document-level info (name, pages, project metadata) |
| `frame` | Frames/screens — list, get, create, update |
| `node` | Widget nodes inside frames — get, list, create, update, delete |
| `selection` | Read/set the current canvas selection |
| `theme` | Colors, typography, and theme tokens |
| `asset` | Project asset management (images, fonts, etc.) |
| `image` | Upload or resolve image assets |
| `capture` | Screenshot frames or selections |
| `history` | Undo/redo stack |
| `pv` | Preview mode control |
| `output` | Export / generated-code retrieval |
| `check` | Design validation and error reporting |
| `help` | API exploration (see above) |

### Common Patterns

**Read canvas state**
```lua
local d = design.get()          -- {name, pageCount, ...}
local frames = frame.list()     -- [{id, name, ...}, ...]
local nodes = node.list(frame_id)
local n = node.get(node_id)
```

**Modify nodes**
```lua
node.update(node_id, { text = "Hello", color = "#FF0000" })
node.create(parent_id, "Text", { text = "New widget" })
node.delete(node_id)
```

**Selection**
```lua
local sel = selection.get()     -- [{id, type, ...}]
selection.set({ id1, id2 })
selection.clear()
```

**Theme tokens**
```lua
local colors = theme.get_colors()       -- {primary, secondary, ...}
local typo   = theme.get_typography()   -- {headline1, body1, ...}
```

**Capture**
```lua
local png = capture.frame(frame_id)     -- base64 PNG
```

**When unsure of exact API** — call `help.fn("module", "functionName")` to get the signature before using it. This is cheaper than reading the full guide.

---

## Notes

- Each sub-agent needs its own `create_session` call — never share `sessionId` across agents.
- The `toolGuideMarkdown` field returned by `create_session` contains the full API reference (~85 KB). Do **not** load it into context — use `help.*` or this skill instead.
