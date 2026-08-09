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

**stdio (local process)** — pin an exact version, never a mutable tag (see "Before installing or building" below):

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "package-name@1.2.3"],
      "env": { "API_KEY": "${API_KEY}" }
    }
  }
}
```

Local git-clone variant: `"command": "node", "args": ["/abs/path/dist/index.js"]` (built from a pinned tag/commit — see Install methods).

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

## Before installing or building

Every method below runs third-party code with your privileges. Before running any of them:
1. Pin an exact version — npm: `npm view <pkg> versions` then use `package-name@X.Y.Z`, never an unpinned `@latest`; git: pin a tagged release or commit SHA, never a branch HEAD.
2. Review the source (npm: `npm view <pkg> repository`, then read it; git: read the README and entry point) for anything that shells out, reads unrelated env vars, or phones home.
3. Get explicit user confirmation before installing, building, or executing.

## Install methods

| Method | When | Command |
|---|---|---|
| npx (preferred) | Published npm package | `npx -y package-name@X.Y.Z --help` to smoke-test the pinned version; no install step |
| npm global | Package has no npx entry | `npm install -g package-name@X.Y.Z && which package-name` |
| Local clone | Unpublished / dev server | `git clone <url> ~/.claude/mcp-servers/<name> && cd ~/.claude/mcp-servers/<name> && git checkout <pinned-tag-or-sha> && npm install && npm run build`; point `args` at the built entry file |
| Remote | Hosted/cloud MCP | No install — validate before sending any credential, see below |

**Validating a remote endpoint**: if the URL is user-supplied, a malicious or mistyped endpoint can collect the token. Probe without credentials first, against the exact HTTPS host the user explicitly confirmed (not a redirect target, not a URL scraped from an untrusted page):

```bash
curl --connect-timeout 5 --max-time 15 -I <url>/health   # unauthenticated reachability check
```

Confirm the response looks like the expected server (not a generic 404 or an unrelated service) and that `<url>`'s host matches what the user confirmed. Only after that validation, send the credential:

```bash
curl --connect-timeout 5 --max-time 15 -H "Authorization: Bearer $KEY" <url>/health
```

## Source parsing quirks

- **Smithery.ai page**: WebFetch it; the config JSON lives in a "Claude Code"/"Claude Desktop" tab, env vars are listed separately from the JSON block.
- **npmjs.com page**: `npm view <pkg> --json` for metadata is more reliable than scraping the page.
- **Code snippet** (imports `@modelcontextprotocol/sdk` or `mcp`): ask for a server name, save under `~/.claude/mcp-servers/<name>/`, build, then treat as local-clone method.
- **GitHub repo**: clone to a scratch dir only to read the README for install method + required env vars; don't leave the clone there unless it's the actual local-clone install target.

## Verify it loaded

1. Validate JSON syntax on whichever file you actually edited (see Config locations — not necessarily `~/.claude/settings.json`) before restarting: `python3 -m json.tool "$CONFIG_FILE" > /dev/null && echo valid`.
2. Claude Code must be restarted to pick up new/changed MCP servers — there is no hot reload.
3. After restart, confirm the server's tools appear in the tool list (`mcp__<server-name>__*`).
4. If tools don't appear: re-check JSON validity first (one malformed server entry can block Claude Code from starting), then confirm the command/binary actually resolves on PATH.

## Gotchas

- Invalid JSON anywhere in the config file blocks Claude Code from starting — always validate after editing.
- Config path is not universal across installs — check which of `~/.claude/settings.json`, `~/.claude/config.json`, `~/.config/claude/config.json` actually exists.
- Remote MCPs almost always use `"transport": "sse"`.
- Never commit `.claude/settings.local.json` if it contains secrets — gitignore it explicitly.
