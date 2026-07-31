---
name: add-mcp-server
description: Installs and configures MCP servers for Claude Code from a GitHub repo, Smithery.ai page, npm package, remote endpoint, or code snippet — writes the config block and verifies it loads. Activate when user says "add MCP server", "install MCP server", "configure MCP", "set up MCP for...", or provides an MCP source URL/snippet.
---

# Add MCP Server

## Config locations

MCP servers are **not** configured in `settings.json` / `settings.local.json` — an `mcpServers`
key there is silently ignored. Three scopes, two files:

| Scope | File | Applies to |
|---|---|---|
| Local (default) | `~/.claude.json`, under the entry for the current project | This project, this user only — private, never committed |
| Project | `./.mcp.json` at the project root | Everyone who clones the project; requires one-time in-session approval |
| User (global) | `~/.claude.json`, under the top-level `mcpServers` key | All of this user's projects |

**Precedence, highest first: local → project → user.** Duplicates are matched by server name,
and the winning entry is used whole — fields are never merged across scopes.

Prefer the CLI over hand-editing, since it writes the right file for the scope:

```bash
claude mcp add <name> --scope local   -- npx -y package-name@1.2.3   # default
claude mcp add <name> --scope project -- npx -y package-name@1.2.3   # writes ./.mcp.json
claude mcp add <name> --scope user    -- npx -y package-name@1.2.3
claude mcp list && claude mcp get <name>                             # inspect what resolved
```

## House rule — secrets

`~/.claude.json` and `./.mcp.json` both frequently sit inside a **git-tracked vault/repo** (and `.mcp.json` is meant to be committed). Never put API keys, tokens, or connection strings inline in an MCP `env` block — they will get committed. Instead:
1. Export the secret in the shell profile: `export FOO_API_KEY=...` in `~/.zshrc`.
2. Reference it in the config as `"env": { "FOO_API_KEY": "${FOO_API_KEY}" }`, or omit `env` entirely if the server reads the variable straight from the process environment. (`.mcp.json` expands `${VAR}` and `${VAR:-default}`.)

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

Every value below (`NAME`, `PKG`, `PIN`, `REPO_URL`, `ENDPOINT`) arrives from a URL, a page, or a
snippet the user pasted — untrusted for shell purposes. **Validate each one against the pattern
in the table, then always pass it as a quoted `"$VAR"` argument. Never paste an unvalidated value
into a command line.** Anything that fails its pattern stops the install with a message, rather
than being escaped and used anyway.

```bash
set -euo pipefail
NAME=...; PKG=...; PIN=...            # PIN is an exact version, tag, or 40-hex SHA
[[ "$NAME" =~ ^[a-z0-9][a-z0-9-]*$ ]]              || { echo "bad server name"; exit 1; }
[[ "$PKG"  =~ ^(@[a-z0-9._-]+/)?[a-z0-9._-]+$ ]]   || { echo "bad package name"; exit 1; }
[[ "$PIN"  =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]      || { echo "bad version pin"; exit 1; }
DEST="$HOME/.claude/mcp-servers/$NAME"             # $NAME is slug-checked, so no traversal
```

| Method | When | Command |
|---|---|---|
| npx (preferred) | Published npm package | `npx -y "$PKG@$PIN" --help` to smoke-test the pinned version; no install step |
| npm global | Package has no npx entry | `npm install -g "$PKG@$PIN" && command -v "$PKG"` |
| Local clone | Unpublished / dev server | see below; point `args` at the built entry file |
| Remote | Hosted/cloud MCP | No install — validate before sending any credential, see below |

Local clone — require an `https://` git URL, and confirm the clone landed inside
`~/.claude/mcp-servers` before building anything from it:

```bash
[[ "$REPO_URL" =~ ^https://[A-Za-z0-9._~:/?#@=%-]+$ ]] || { echo "bad repo URL"; exit 1; }
git clone --depth 50 -- "$REPO_URL" "$DEST"
cd "$DEST"
[[ "$(pwd -P)" == "$(cd "$HOME/.claude/mcp-servers" && pwd -P)"/* ]] || { echo "clone escaped"; exit 1; }
git checkout --detach "$PIN"          # PIN is pattern-checked, so it can't start with `-`
npm install && npm run build
```

**Validating a remote endpoint**: if the URL is user-supplied, a malicious or mistyped endpoint can collect the token. Require `https://`, then probe without credentials first, against the exact host the user explicitly confirmed (not a redirect target, not a URL scraped from an untrusted page):

```bash
[[ "$ENDPOINT" =~ ^https://[A-Za-z0-9._~:/?#@=%-]+$ ]] || { echo "bad endpoint"; exit 1; }
curl --connect-timeout 5 --max-time 15 -I -- "$ENDPOINT/health"   # unauthenticated, no redirects followed
```

Confirm the response looks like the expected server (not a generic 404 or an unrelated service) and that `$ENDPOINT`'s host matches what the user confirmed. Only after that validation, send the credential:

```bash
curl --connect-timeout 5 --max-time 15 -H "Authorization: Bearer $KEY" -- "$ENDPOINT/health"
```

## Source parsing quirks

- **Smithery.ai page**: WebFetch it; the config JSON lives in a "Claude Code"/"Claude Desktop" tab, env vars are listed separately from the JSON block.
- **npmjs.com page**: `npm view <pkg> --json` for metadata is more reliable than scraping the page.
- **Code snippet** (imports `@modelcontextprotocol/sdk` or `mcp`): ask for a server name, save under `~/.claude/mcp-servers/<name>/`, build, then treat as local-clone method.
- **GitHub repo**: clone to a scratch dir only to read the README for install method + required env vars; don't leave the clone there unless it's the actual local-clone install target.

## Verify it loaded

1. Validate JSON syntax on whichever file you actually edited (see Config locations) before
   restarting — set `CONFIG_FILE` to that path first, don't copy the command with the variable
   unset:

   ```bash
   CONFIG_FILE="$HOME/.claude.json"        # or ./.mcp.json for a project-scoped server
   python3 -m json.tool "$CONFIG_FILE" > /dev/null && echo "valid: $CONFIG_FILE"
   ```
2. Claude Code must be restarted to pick up new/changed MCP servers — there is no hot reload.
3. After restart, confirm the server's tools appear in the tool list (`mcp__<server-name>__*`).
4. If tools don't appear: re-check JSON validity first (one malformed server entry can block Claude Code from starting), then confirm the command/binary actually resolves on PATH.

## Gotchas

- Invalid JSON anywhere in the config file blocks Claude Code from starting — always validate after editing.
- An `mcpServers` block in `settings.json`/`settings.local.json` is ignored without error. If a server never appears, check that it's in `~/.claude.json` or `./.mcp.json`, not a settings file.
- A server that resolves to the wrong definition is almost always a scope collision — `claude mcp get <name>` shows which scope won (local beats project beats user).
- Remote MCPs almost always use `"transport": "sse"`.
- `./.mcp.json` is committed by design, so it must contain `${VAR}` references only — never a literal secret.
