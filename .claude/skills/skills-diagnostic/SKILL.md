---
name: skills-diagnostic
description: Validates a repo's skills directory — SKILL.md present, frontmatter parses, name matches folder, no duplicate names across skill roots, no broken symlinks. Activate when user says "check skills health", "diagnose skills", "validate skills", or "check for skill issues".
---

# Skills Diagnostic

Validates a skills tree (check whichever of `.claude/skills/`, `.codex/skills/`, `.agents/skills/` exist in the repo) rather than a single machine's symlink setup.

**If this repo has `scripts/validate_skills.py`, just run it** (`python3 scripts/validate_skills.py`) — it covers all the checks below plus frontmatter-key allowlisting and retired-reference scanning. Use the manual checks here only when auditing a repo that has no validator script.

## Checks

Iterate only over the roots that exist in this repo (`.claude/skills`, `.codex/skills`, `.agents/skills`). Don't `find` the whole working tree for `*/skills/*` — it also matches vendored, nested, or generated `skills/` directories and produces false duplicates and false broken-link reports.

For every `<root>/*/SKILL.md` under those roots:

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

4. **`description:` present**, non-empty, single line — no block scalar (`>`, `>-`, `>+`, `|`, `|-`, `|+`), no inline `[...]`/`{...}` collection, no unbalanced quotes. This mirrors `scripts/validate_skills.py`; when the two disagree, trust the validator.

5. **Name format**: `^[a-z0-9][a-z0-9-]*$` — `echo "$yaml_name" | grep -qE '^[a-z0-9][a-z0-9-]*$'`.

6. **Unique across all skill roots in the repo.** A name collision across `.claude/skills/`, `.codex/skills/`, `.agents/skills/`, or between a project root and a merged/global root gets silently auto-suffixed (`name2`) by Blocks — flag collisions rather than relying on that.

   ```bash
   for root in .claude/skills .codex/skills .agents/skills; do
     [ -d "$root" ] && find "$root" -mindepth 2 -maxdepth 2 -name SKILL.md -exec dirname {} \;
   done | xargs -n1 basename | sort | uniq -d
   ```

7. **No broken symlinks** anywhere under the roots that exist:

   ```bash
   for root in .claude/skills .codex/skills .agents/skills; do
     [ -d "$root" ] && find "$root" -type l ! -exec test -e {} \; -print
   done
   ```

## Report format

List each skill as `✓ <name>: valid` or `✗ <name>: <specific problem>`. End with counts: total skills, critical issues, name collisions, broken symlinks. Report only — don't fix anything automatically.
