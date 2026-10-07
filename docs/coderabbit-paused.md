# CodeRabbit paused: how to restore it

CodeRabbit was removed from the global post-clone script because the subscription was cancelled.
The API key then became invalid ("owner does not have an active seat"), and `set -e` made the
failed `cr auth login` abort every clone.

## What changed

| File | Change |
|---|---|
| `.blocks/post-clone` | Removed the CLI install and the `cr auth login` step |
| `CLAUDE.md` | "Code Review (CodeRabbit)" section rewritten as "paused" |

Not changed (still present, inert without the `cr` CLI / CodeRabbit app):
- `.claude/skills/coderabbit/`, `coderabbit-linear-handoff/`, `onboard-coderabbit/`
- `.github/workflows/*coderabbit*`, `.coderabbit.yaml`, `github-actions/examples/`

## Restore

1. Resubscribe at coderabbit.ai and confirm your account has an active seat.
2. Create a new API key (Account Settings → API Keys). Old keys do not revive.
3. Set it as the `CODERABBIT_API_KEY` secret in the Blocks environment.
4. Revert the PR that added this file, or re-add this block to `.blocks/post-clone`
   before the `Global post-clone setup complete!` line:

   ```bash
   # Install CodeRabbit CLI if not already present
   if ! command -v cr &>/dev/null; then
     echo "Installing CodeRabbit CLI..."
     curl -fsSL https://cli.coderabbit.ai/install.sh | sh
     echo "CodeRabbit CLI installed."
   else
     echo "CodeRabbit CLI already installed: $(cr --version 2>/dev/null || echo 'ok')"
   fi

   # Authenticate headlessly using API key if provided
   if [ -n "$CODERABBIT_API_KEY" ]; then
     echo "Authenticating CodeRabbit CLI with API key..."
     cr auth login --api-key "$CODERABBIT_API_KEY"
     echo "CodeRabbit CLI authenticated."
   else
     echo "CODERABBIT_API_KEY not set — skipping CodeRabbit auth (agent will need to authenticate manually or the key must be added to Blocks secrets)."
   fi
   ```

   Optional hardening: wrap `cr auth login` in `if ... then ... else echo "WARNING: ..."; fi`
   so an expired seat cannot break a clone again.
5. Restore the "Code Review (CodeRabbit)" section in `CLAUDE.md` from git history
   (`git log -p -- CLAUDE.md`).
6. Re-install the CodeRabbit GitHub app on the repos you want reviewed.

## Also remove the stale secret

Delete `CODERABBIT_API_KEY` from the blocks.org environment secrets while CodeRabbit is paused.
