---
name: skills-diagnostic
description: Validates a repo's skills directory — SKILL.md present, frontmatter parses, name matches folder, no duplicate names across skill roots, no broken symlinks. Activate when user says "check skills health", "diagnose skills", "validate skills", or "check for skill issues".
---

# Skills Diagnostic

Validates a skills tree (check whichever of `.claude/skills/`, `.codex/skills/`, `.agents/skills/` exist in the repo) rather than a single machine's symlink setup.

## Checks

For every `<root>/skills/*/SKILL.md`:

1. **File exists**: `<skill-dir>/SKILL.md` present. Flag any skill folder without one.
2. **Frontmatter parses**: starts on line 1 with `---`, has a closing `---` within the first ~15 lines, and the YAML between them parses.
   ```bash
   head -1 SKILL.md                                 # must be "---"
   awk 'NR>1 && /^---$/{print NR; exit}' SKILL.md    # line number of closing ---
   ```
3. **`name:` present and matches the folder name** exactly.
   ```bash
   yaml_name=$(grep '^name:' SKILL.md | cut -d: -f2- | xargs)
   [ "$yaml_name" = "$(basename "$(dirname SKILL.md)")" ] || echo "mismatch"
   ```
4. **`description:` present**, non-empty, single line (no `>`/`>-` block scalar).
5. **Name format**: `^[a-z0-9][a-z0-9-]*$` — `echo "$yaml_name" | grep -qE '^[a-z0-9][a-z0-9-]*$'`.
6. **Unique across all skill roots in the repo.** A name collision across `.claude/skills/`, `.codex/skills/`, `.agents/skills/`, or between a project root and a merged/global root gets silently auto-suffixed (`name2`) by Blocks — flag collisions rather than relying on that.
   ```bash
   find . -path '*/skills/*/SKILL.md' -exec dirname {} \; | xargs -n1 basename | sort | uniq -d
   ```
7. **No broken symlinks** anywhere under the skill roots:
   ```bash
   find . -path '*/skills/*' -type l ! -exec test -e {} \; -print
   ```

## Report format

List each skill as `✓ <name>: valid` or `✗ <name>: <specific problem>`. End with counts: total skills, critical issues, name collisions, broken symlinks. Report only — don't fix anything automatically.
