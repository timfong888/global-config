# Shell Aliases

Shell configuration helpers for Claude Code workspace switching.

## Files

| File | Purpose |
|---|---|
| `claude-workspace-aliases.sh` | Shell aliases — source this from `~/.zshrc` or `~/.bashrc` |
| `install-aliases.sh` | One-time installer — appends the source line automatically |

## Aliases

| Alias | Command | When to use |
|---|---|---|
| `cc` | `claude` | Personal workspace via Claude subscription |
| `cc-aurora` | `ANTHROPIC_BASE_URL=… ANTHROPIC_API_KEY=… claude` | Aurora inference endpoint from any directory |
| `aurora` | `cd ~/aurora-workspace && claude` | Jump into Aurora workspace (picks up project settings) |

## Setup

```bash
# One-time install
bash shell/install-aliases.sh

# Reload shell
source ~/.zshrc    # or source ~/.bashrc

# Set Aurora key (add this to ~/.zshrc permanently)
export AURORA_API_KEY="your-aurora-key"
```

## Notes

- `cc` requires no API key — Claude subscription auth is handled natively by Claude Code.
- `cc-aurora` reads `$AURORA_API_KEY` from your environment; no credential is stored in the alias itself.
- `aurora` assumes your Aurora project lives at `~/aurora-workspace` and has a `.claude/settings.local.json` with Aurora credentials (see SAT-675).
