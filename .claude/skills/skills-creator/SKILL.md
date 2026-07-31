---
name: skills-creator
description: Creates a new Claude Code skill with correct frontmatter, location, and content density for the Blocks platform. Activate when user says "create a new skill", "make a skill for X", or "help me build a skill".
---

# Skills Creator

## Where skills live

`.claude/skills/<skill-name>/SKILL.md` (Claude Code / Blocks). Other agent runtimes sharing the same repo use the parallel paths `.codex/skills/<name>/SKILL.md` and `.agents/skills/<name>/SKILL.md`.

The folder name **is** the slash command the platform exposes (`/<skill-name>`). Blocks resolves a duplicate folder name across merged skill sources by appending a number (`review-security2`) rather than erroring — so pick a name that's unique across the repo's skill roots; don't rely on that collision-handling.

`<skill-name>` must be lowercase, hyphen-separated: `^[a-z0-9][a-z0-9-]*$`.

## Frontmatter

```yaml
---
name: skill-name-here
description: One line. What it does + when to use it + literal trigger phrases the user might type.
---
```

Only `name` and `description` are required. Don't add `tags`, `version`, `author`, `dependencies: []`, `scope`, or `metadata` — nothing reads them.

**The description is the entire signal the model uses to decide whether to load the skill.** It never sees the body until it loads it. Write it to discriminate against neighboring skills, not to summarize nicely — include the exact phrases a user would say ("check skills health", "diagnose skills") and the concrete situation, not just a category label.

## The authoring rule

Write for a model that already knows how to code, use git, call APIs, and write YAML. State only what it **cannot infer**:
- Exact IDs, URLs, endpoints, project/team/spreadsheet IDs, CLI flags.
- Where credentials live (env var name / file path — never the secret).
- File paths and directory conventions specific to this repo.
- API quirks and gotchas ("returns X not Y", known-broken versions, rate limits).
- House rules ("never push to main", "always sign X").
- Domain taxonomies the model wouldn't otherwise produce.

Do not narrate obvious agent behavior ("Step 1: read the file. Step 2: understand it."), explain what well-known tools are, or paste giant output templates — describe the shape in a few lines instead.

Target 40-120 lines. If a skill has distinct modes, expose them as a `## Modes` list near the top so the agent can route on them.

## Process

1. Ask (if not given): skill name, purpose, trigger phrases, and the non-inferable facts (IDs/paths/quirks/rules) it must carry.
2. Check for a name collision in this repo's skill root(s) before creating — rename if one exists rather than relying on Blocks' auto-suffix.
3. Write `.claude/skills/<name>/SKILL.md` with the frontmatter above plus body sections only for what's genuinely non-inferable.
4. Confirm the file location and the resulting slash command back to the user.
