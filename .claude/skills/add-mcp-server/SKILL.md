---
name: add-mcp-server
description: Installs and configures MCP servers for Claude Code from a GitHub repo, Smithery.ai page, npm package, remote endpoint, or code snippet — writes the config block and verifies it loads. Activate when user says "add MCP server", "install MCP server", "configure MCP", "set up MCP for...", or provides an MCP source URL/snippet.
---

# Add MCP Server

## Config locations

| Scope | File | Applies to |
|---|---|---|
| User (global) | `~/.claude/settings.json` (some installs use `~/.claude/config.json` or `~/.config/claude/config.json` — check which exists before assuming) | All sessions, under the `mcpServers` key |
| Project | `./.claude/settings.local.json` | Current project only; gitignore it if it holds secrets |

Project-level config overrides user-level for a server with the same name.

## House rule — secrets

`~/.claude/settings.json` is frequently a **symlink into a git-tracked vault/repo**. Never put API keys, tokens, or connection strings inline in an MCP `env` block in settings.json — they will get committed. Instead:
1. Export the secret in the shell profile: `export FOO_API_KEY=...` in `~/.zshrc`.
2. Reference it in the config as `"env": { "FOO_API_KEY": "${FOO_API_KEY}" }`, or omit `env` entirely if the server reads the variable straight from the process environment.

## Config shape

**stdio (local process)**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name"],
      "env": { "API_KEY": "${API_KEY}" }
    }
  }
}
```
Local git-clone variant: `"command": "node", "args": ["/abs/path/dist/index.js"]`.

**Remote (HTTP/SSE)**
```json
{
  "mcpServers": {
    "server-name": {
      "transport": "sse",
      "url": "https://api.example.com/mcp",
      "headers": { "Authorization": "Bearer ${API_KEY}" }
    }
  }
}
```

## Install methods

| Method | When | Command |
|---|---|---|
| npx (preferred) | Published npm package | `npx -y package-name --help` to smoke-test; no install step |
| npm global | Package has no npx entry | `npm install -g package-name && which package-name` |
| Local clone | Unpublished / dev server | `git clone <url> ~/.claude/mcp-servers/<name> && npm install && npm run build`; point `args` at the built entry file |
| Remote | Hosted/cloud MCP | No install — just validate the endpoint: `curl -H "Authorization: Bearer $KEY" <url>/health` |

## Source parsing quirks

- **Smithery.ai page**: WebFetch it; the config JSON lives in a "Claude Code"/"Claude Desktop" tab, env vars are listed separately from the JSON block.
- **npmjs.com page**: `npm view <pkg> --json` for metadata is more reliable than scraping the page.
- **Code snippet** (imports `@modelcontextprotocol/sdk` or `mcp`): ask for a server name, save under `~/.claude/mcp-servers/<name>/`, build, then treat as local-clone method.
- **GitHub repo**: clone to a scratch dir only to read the README for install method + required env vars; don't leave the clone there unless it's the actual local-clone install target.

## Verify it loaded

1. Validate JSON syntax before restarting: `python3 -m json.tool ~/.claude/settings.json > /dev/null && echo valid`.
2. Claude Code must be restarted to pick up new/changed MCP servers — there is no hot reload.
3. After restart, confirm the server's tools appear in the tool list (`mcp__<server-name>__*`).
4. If tools don't appear: re-check JSON validity first (one malformed server entry can block Claude Code from starting), then confirm the command/binary actually resolves on PATH.

## Gotchas

- Invalid JSON anywhere in the config file blocks Claude Code from starting — always validate after editing.
- Config path is not universal across installs — check which of `~/.claude/settings.json`, `~/.claude/config.json`, `~/.config/claude/config.json` actually exists.
- Remote MCPs almost always use `"transport": "sse"`.
- Never commit `.claude/settings.local.json` if it contains secrets — gitignore it explicitly.
