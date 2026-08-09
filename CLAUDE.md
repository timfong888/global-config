# Global Config — CLAUDE.md

Shared configuration reference for all Blocks agents in the Satchel workspace.

---

## Linear MCP

### Connection

Linear is available in every Blocks agent session via the **`@blocksuser/mcp-linear`** package
(v1.1.2), configured at the Blocks global level (`~/.config/blocks/mcp.json`) — not
session-specific. No per-project setup is required.

```
MCP server name : linear
Package         : @blocksuser/mcp-linear
Auth            : LINEAR_API_TOKEN (OAuth token injected by Blocks at session start)
```

### Available tools (minimum set for skill profiles)

| Tool | Purpose |
|---|---|
| `linear_getIssueById` | Fetch a single issue by ID or identifier (e.g. `SAT-646`) |
| `linear_createComment` | Post a comment on an issue |
| `linear_updateIssue` | Update issue fields (state, assignee, labels, description, …) |
| `linear_getComments` | List comments on an issue |

The full `linear` MCP exposes many more tools (search, labels, cycles, projects, initiatives,
attachments, users). The four above are the minimum needed by all agent skill profiles.

### Composio account convention

The `linear-agent-poller` command convention names the Composio Linear connection
**`satchel-linear`** (see `LINEAR_ACCOUNT` in `linear-agent-poll.md`). When invoking
Composio-backed Linear tools (server `d9fdab16-6cb6-4bad-a42b-8ab966060cbb`), pin calls with
`account: satchel-linear`. The Blocks-native `@blocksuser/mcp-linear` server does not require
an account pin — it authenticates directly via `LINEAR_API_TOKEN`.

---

## Satchel Workspace Reference

Pre-resolved IDs so agents don't need to look them up:

| Key | Value |
|---|---|
| Workspace slug | `sophia-xyz` |
| Issue base URL | `https://linear.app/sophia-xyz/issue/` |
| Team name | Satchel |
| Team key | `SAT` |
| Team ID | `88661a7f-d07e-4590-9724-b8f69e30556e` |

### Users

| Handle | Linear user ID |
|---|---|
| @timfong888 (Tim) | `aa3fb002-ba6c-440f-8837-cc5c92a3c748` |
| @agentfong (agent) | `41903248-8c2b-41e4-a7fb-f00f4feb9ba4` |

### Workflow states

| State | ID | Type |
|---|---|---|
| Agent Queue | `73be9b83-4bd2-4ef1-97a7-0ff6e6ff5339` | unstarted |
| Todo | `4dfa455d-9248-4b2b-b3de-4d0d343efe21` | unstarted |
| In Progress | `8439671f-0e5d-4a08-ba98-d3bf5b758d16` | started |
| In Review | `21d53c23-57ce-4f72-aaf1-2c6d104f6e02` | started |
| Blocked | `f68b9fad-0d13-4397-b1e0-97f6e7216e52` | started |
| Done | `299e627d-3989-40c4-8aea-b9d56209fa39` | completed |

### Labels

| Label | ID |
|---|---|
| agent-coding | `b4c6b47e-0ded-4468-a68c-4d3a5b58ec33` |
| agent-writing | `79adef88-4350-48c2-a1da-31137a2dfbc8` |
| agent-admin | `a1a9437b-8c75-4cd5-ba6b-5c1fb4443f00` |

---

## Model Tier Selection

Default dispatch: **Sonnet** (inherited session default). Override per-ticket via Linear
routing labels (`MODEL_LABELS`) or the `effort:` parameter. See `linear-agent-poll.md` for
the full label → model mapping.
