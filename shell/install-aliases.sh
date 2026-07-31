#!/usr/bin/env bash
# Installs the Claude workspace aliases by adding a source line to ~/.zshrc and/or ~/.bashrc

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ALIASES_FILE="$SCRIPT_DIR/claude-workspace-aliases.sh"
SOURCE_LINE="source \"$ALIASES_FILE\""

install_to() {
  local rc_file="$1"
  if [ ! -f "$rc_file" ]; then
    return
  fi
  if grep -qF "$ALIASES_FILE" "$rc_file"; then
    echo "Already installed in $rc_file — skipping."
  else
    echo "" >> "$rc_file"
    echo "# Claude Code workspace aliases (SAT-676)" >> "$rc_file"
    echo "$SOURCE_LINE" >> "$rc_file"
    echo "Installed into $rc_file"
  fi
}

install_to "$HOME/.zshrc"
install_to "$HOME/.bashrc"

echo ""
echo "Done. Reload your shell:"
echo "  source ~/.zshrc    # zsh"
echo "  source ~/.bashrc   # bash"
echo ""
echo "Available aliases:"
echo "  cc          — launch Claude (subscription, personal workspace)"
echo "  cc-aurora   — launch Claude via Aurora endpoint (set AURORA_API_KEY first)"
echo "  aurora      — cd ~/aurora-workspace && launch Claude"
