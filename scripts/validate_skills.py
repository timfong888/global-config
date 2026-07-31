#!/usr/bin/env python3
"""Validate that every skill in this repo is loadable by Blocks.

Blocks discovers skills at `<root>/<skill-name>/SKILL.md` for each of the roots
`.claude/skills`, `.codex/skills`, `.agents/skills`, and turns the *folder name*
into the `/<skill-name>` slash command. When two sources define the same name it
silently appends a number (`review-security2`), so duplicate names are a real bug.

Checks, per skill directory:
  1. SKILL.md exists and is non-empty.
  2. The file opens with a `---` fenced YAML frontmatter block that closes.
  3. Frontmatter is flat `key: value` scalars (no block scalars, no nesting) and
     parses. Every key is on the allowlist.
  4. `name` and `description` are present and non-empty.
  5. `name` equals the directory name, so the slash command matches the folder.
  6. Directory names are unique across all skill roots.
  7. No references to retired infrastructure.
  8. Directory name is a valid slash-command slug.

Exit code 0 = clean, 1 = at least one error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOTS = (".claude/skills", ".codex/skills", ".agents/skills")

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REQUIRED_KEYS = ("name", "description")
ALLOWED_KEYS = {"name", "description", "allowed-tools", "license"}
MAX_DESCRIPTION_CHARS = 1024

# Infrastructure this workspace has retired. A skill that still names one of
# these will send the agent down a dead path, so treat it as an error.
RETIRED = {
    "rube-personal": "Rube MCP was sunset 2026-05-15; use the Composio CLI",
    "rube_personal": "Rube MCP was sunset 2026-05-15; use the Composio CLI",
    "composio-personal": "no such MCP server exists; use the Composio CLI",
    "composio_personal": "no such MCP server exists; use the Composio CLI",
    "pipedream-filoz": "pipedream MCP servers are retired",
    "pipedream-timfong888": "pipedream MCP servers are retired",
    "greptile": "Greptile was retired 2026-05-27; use the CodeRabbit CLI",
}


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.checked = 0

    def error(self, where: Path, msg: str) -> None:
        self.errors.append(f"{where.relative_to(REPO_ROOT)}: {msg}")


def split_frontmatter(text: str, path: Path, out: Findings) -> dict[str, str] | None:
    """Return the frontmatter mapping, or None if the block is malformed."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        out.error(path, "missing YAML frontmatter (file must start with `---`)")
        return None

    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        out.error(path, "frontmatter block is never closed with `---`")
        return None

    fields: dict[str, str] = {}
    for lineno, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            out.error(path, f"line {lineno}: nested/indented frontmatter is not allowed — "
                            "use flat `key: value` scalars")
            return None
        key, sep, value = line.partition(":")
        if not sep:
            out.error(path, f"line {lineno}: not a `key: value` pair")
            return None
        key, value = key.strip(), value.strip()
        if value in (">", ">-", "|", "|-"):
            out.error(path, f"line {lineno}: block scalars are not allowed — "
                            f"put `{key}` on one line")
            return None
        if key in fields:
            out.error(path, f"line {lineno}: duplicate key `{key}`")
            return None
        fields[key] = value.strip("'\"")
    return fields


def check_skill(skill_dir: Path, out: Findings) -> str | None:
    """Validate one skill directory. Returns its declared name on success."""
    out.checked += 1
    dir_name = skill_dir.name

    if not SLUG_RE.match(dir_name):
        out.error(skill_dir, "folder name is not a valid slash-command slug "
                             "(lowercase letters, digits, hyphens)")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        out.error(skill_dir, "no SKILL.md — Blocks will not discover this skill")
        return None

    text = skill_md.read_text(encoding="utf-8")
    if not text.strip():
        out.error(skill_md, "file is empty")
        return None

    fields = split_frontmatter(text, skill_md, out)
    if fields is None:
        return None

    for key in sorted(set(fields) - ALLOWED_KEYS):
        out.error(skill_md, f"unsupported frontmatter key `{key}` — "
                            f"allowed: {', '.join(sorted(ALLOWED_KEYS))}")

    for key in REQUIRED_KEYS:
        if not fields.get(key):
            out.error(skill_md, f"frontmatter `{key}` is missing or empty")

    name = fields.get("name")
    if name and name != dir_name:
        out.error(skill_md, f"frontmatter name `{name}` != folder name `{dir_name}` — "
                            f"the slash command comes from the folder, so these must match")

    description = fields.get("description", "")
    if len(description) > MAX_DESCRIPTION_CHARS:
        out.error(skill_md, f"description is {len(description)} chars "
                            f"(max {MAX_DESCRIPTION_CHARS})")

    lowered = text.lower()
    for needle, why in RETIRED.items():
        if needle in lowered:
            out.error(skill_md, f"references retired `{needle}` — {why}")

    return name or dir_name


def main() -> int:
    out = Findings()
    seen: dict[str, Path] = {}

    for root_name in SKILL_ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        for skill_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            name = check_skill(skill_dir, out)
            if name is None:
                continue
            if name in seen:
                out.error(skill_dir, f"duplicate skill name `{name}` (also at "
                                     f"{seen[name].relative_to(REPO_ROOT)}) — Blocks would "
                                     f"rename one to `{name}2`")
            else:
                seen[name] = skill_dir

    if not out.checked:
        print("No skills found — expected at least one under "
              f"{', '.join(SKILL_ROOTS)}", file=sys.stderr)
        return 1

    for err in out.errors:
        print(f"ERROR  {err}", file=sys.stderr)

    print(f"\nChecked {out.checked} skill(s); {len(out.errors)} error(s).")
    return 1 if out.errors else 0


if __name__ == "__main__":
    sys.exit(main())
