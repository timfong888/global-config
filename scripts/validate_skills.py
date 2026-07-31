#!/usr/bin/env python3
"""Validate that every skill in this repo is loadable by Blocks.

Blocks discovers skills at `<root>/<skill-name>/SKILL.md` for each of the roots
`.claude/skills`, `.codex/skills`, `.agents/skills`, and turns the *folder name*
into the `/<skill-name>` slash command. When two sources define the same name it
silently appends a number (`review-security2`), so duplicate names are a real bug.

Checks, per skill directory:
  1. The directory is not a broken symlink, and SKILL.md exists and is non-empty.
  2. The file opens with a `---` fenced YAML frontmatter block that closes.
  3. Frontmatter is a flat mapping of `key: value` scalars that parses. Inline
     collections, block scalars, nesting, and unbalanced quotes are rejected.
  4. Every key is on the allowlist; `name` and `description` are non-empty.
  5. `name` equals the directory name, so the slash command matches the folder.
  6. Directory names are unique across all skill roots.
  7. No references to retired infrastructure.
  8. Directory name is a valid slash-command slug.

Run `--selftest` to exercise the frontmatter parser against known-bad inputs.
Exit code 0 = clean, 1 = at least one error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:  # Optional: cross-check with a real YAML parser when one is available.
    import yaml  # type: ignore
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOTS = (".claude/skills", ".codex/skills", ".agents/skills")

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REQUIRED_KEYS = ("name", "description")
ALLOWED_KEYS = {"name", "description", "allowed-tools", "license"}
MAX_DESCRIPTION_CHARS = 1024
BLOCK_SCALARS = {">", ">-", ">+", "|", "|-", "|+"}

# Infrastructure this workspace has retired. A skill that still names one of
# these sends the agent down a dead path, so treat it as an error. Patterns are
# matched case-insensitively against the whole file, including prose.
RETIRED = (
    (r"\brube[-_ ]personal\b", "Rube MCP was sunset 2026-05-15; use the Composio CLI"),
    (r"\brube\s+mcp\b", "Rube MCP was sunset 2026-05-15; use the Composio CLI"),
    (r"\bcomposio[-_]personal\b", "no such MCP server exists; use the Composio CLI"),
    (r"\bpipedream\b", "the pipedream MCP servers are retired"),
    (r"\bgreptile\b", "Greptile was retired 2026-05-27; use the CodeRabbit CLI"),
)


class Findings:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.checked = 0

    def error(self, where: Path, msg: str) -> None:
        try:
            label = where.relative_to(REPO_ROOT)
        except ValueError:
            label = where
        self.errors.append(f"{label}: {msg}")


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    """Parse a flat `key: value` frontmatter block.

    Returns (fields, error). Deliberately stricter than YAML: this repo's
    frontmatter contract is a flat mapping of scalars, so anything else is
    rejected rather than silently accepted.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing YAML frontmatter (file must start with `---`)"

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return None, "frontmatter block is never closed with `---`"

    body = lines[1:end]
    fields: dict[str, str] = {}
    for offset, line in enumerate(body):
        lineno = offset + 2
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t-":
            return None, (f"line {lineno}: indented or list frontmatter is not allowed — "
                          "use flat `key: value` scalars")
        key, sep, raw = line.partition(":")
        if not sep:
            return None, f"line {lineno}: not a `key: value` pair"
        key, value = key.strip(), raw.strip()
        if not key:
            return None, f"line {lineno}: empty key"
        if key in fields:
            return None, f"line {lineno}: duplicate key `{key}`"
        if value in BLOCK_SCALARS:
            return None, (f"line {lineno}: block scalars are not allowed — "
                          f"put `{key}` on one line")
        if value[:1] in "[{":
            return None, (f"line {lineno}: inline collections are not allowed — "
                          f"`{key}` must be a scalar")
        if value[:1] in "\"'":
            quote = value[0]
            if len(value) < 2 or value[-1] != quote or value.count(quote) % 2 != 0:
                return None, f"line {lineno}: unbalanced {quote} quote in `{key}`"
            value = value[1:-1]
        elif value.count('"') % 2 or value.count("'") % 2:
            # An unpaired quote inside a bare scalar is almost always a typo that
            # a real YAML parser would either reject or reinterpret.
            if value.count('"') % 2:
                return None, f"line {lineno}: unbalanced \" quote in `{key}`"
        fields[key] = value

    if yaml is not None:
        try:
            loaded = yaml.safe_load("\n".join(body))
        except yaml.YAMLError as exc:  # pragma: no cover - depends on optional dep
            return None, f"frontmatter is not valid YAML: {exc}"
        if loaded is not None and not isinstance(loaded, dict):
            return None, "frontmatter must be a mapping"

    return fields, None


def check_skill(skill_dir: Path, out: Findings) -> str | None:
    """Validate one skill directory. Returns its declared name on success."""
    out.checked += 1
    dir_name = skill_dir.name

    if skill_dir.is_symlink() and not skill_dir.exists():
        out.error(skill_dir, "broken symlink — target does not exist")
        return None

    if not SLUG_RE.match(dir_name):
        out.error(skill_dir, "folder name is not a valid slash-command slug "
                             "(lowercase letters, digits, hyphens)")

    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_symlink() and not skill_md.exists():
        out.error(skill_md, "broken symlink — target does not exist")
        return None
    if not skill_md.is_file():
        out.error(skill_dir, "no SKILL.md — Blocks will not discover this skill")
        return None

    text = skill_md.read_text(encoding="utf-8")
    if not text.strip():
        out.error(skill_md, "file is empty")
        return None

    fields, err = parse_frontmatter(text)
    if err is not None:
        out.error(skill_md, err)
        return None
    assert fields is not None

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

    for pattern, why in RETIRED:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            out.error(skill_md, f"references retired `{match.group(0)}` — {why}")

    return name or dir_name


def selftest() -> int:
    """Exercise the frontmatter parser against inputs it must reject/accept."""
    bad = {
        "no fence": "name: x\n",
        "unclosed fence": "---\nname: x\n",
        "block scalar": "---\nname: x\ndescription: >\n  hi\n---\n",
        "inline list": "---\nname: x\ndescription: [a, b]\n---\n",
        "inline map": "---\nname: x\ndescription: {a: b}\n---\n",
        "nested": "---\nname: x\nmcpServers:\n  foo: bar\n---\n",
        "unbalanced quote": '---\nname: x\ndescription: "oops\n---\n',
        "duplicate key": "---\nname: x\nname: y\n---\n",
        "not a pair": "---\nname: x\njust-text\n---\n",
        "list item": "---\nname: x\n- item\n---\n",
    }
    good = {
        "plain": "---\nname: x\ndescription: A thing. Use when Y.\n---\n# x\n",
        "quoted": '---\nname: x\ndescription: "A: thing"\n---\n# x\n',
        "colon in value": "---\nname: x\ndescription: Use for a: b mappings.\n---\n# x\n",
    }

    failures = []
    for label, text in bad.items():
        fields, err = parse_frontmatter(text)
        if err is None:
            failures.append(f"should have been rejected: {label}")
    for label, text in good.items():
        fields, err = parse_frontmatter(text)
        if err is not None:
            failures.append(f"should have been accepted: {label} ({err})")
        elif fields.get("name") != "x":
            failures.append(f"wrong parse for {label}: {fields}")

    for line in failures:
        print(f"SELFTEST FAIL  {line}", file=sys.stderr)
    total = len(bad) + len(good)
    print(f"selftest: {total - len(failures)}/{total} cases passed "
          f"(pyyaml {'available' if yaml else 'not installed'})")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()

    out = Findings()
    seen: dict[str, Path] = {}

    for root_name in SKILL_ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        entries = sorted(p for p in root.iterdir()
                         if p.is_dir() or (p.is_symlink() and not p.exists()))
        for skill_dir in entries:
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
    sys.exit(main(sys.argv[1:]))
