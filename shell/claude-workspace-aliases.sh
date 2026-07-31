# ─── Claude Code workspace aliases ──────────────────────────────────────────
#
# Source this file from ~/.zshrc or ~/.bashrc:
#   source ~/path/to/global-config/shell/claude-workspace-aliases.sh
#
# Prerequisites:
#   - Claude Code CLI installed: npm install -g @anthropic-ai/claude-code
#   - Personal workspace: uses Claude subscription (no API key needed)
#   - Aurora workspace:   set AURORA_API_KEY in your environment or
#                         ~/.claude/settings.local.json in ~/aurora-workspace

# Personal workspace: Claude subscription — no API key override needed
alias cc='claude'

# Aurora workspace: route to Aurora inference endpoint from any directory
# Set AURORA_API_KEY in your environment before using, or hardcode below.
alias cc-aurora='ANTHROPIC_BASE_URL="https://api.aurora-provider.com" \
  ANTHROPIC_API_KEY="${AURORA_API_KEY}" \
  claude'

# Jump into Aurora workspace and launch Claude (picks up project settings)
alias aurora='cd ~/aurora-workspace && claude'
