# global-config

Global configuration for agents. Blocks loads this repo as the **global config repo**, so
everything here is merged into *every* Blocks session — the sandbox, Slack, GitHub, and Linear.

| Path | What it is |
|---|---|
| `.claude/skills/<name>/SKILL.md` | Skills. The folder name becomes the `/<name>` slash command. |
| `.blocks/post-clone` | Runs after Blocks clones the repo into a sandbox. |
| `mcp-servers/` | MCP servers published from this repo (currently `aurora`). |
| `scripts/validate_skills.py` | Pre-merge check that every skill is discoverable and unique. |
| `SKILLS-INVENTORY.md` | Decision record: what was kept, merged, and dropped, and why. |

## Skills

Blocks discovers skills from `.claude/skills/`, `.codex/skills/`, and `.agents/skills/` — the
folder prefix does not matter, and it merges dashboard skills, this global repo, and the active
per-repo skills into one set. Reference:
<https://docs.blocks.team/using-blocks/features/skills>

Because this repo loads everywhere, its skills are deliberately few and short. Two consequences
worth internalising before adding one:

- **Names must be globally unique.** On a collision Blocks silently renames one skill by
  appending a number (`review-security` → `review-security2`), and the losing skill becomes
  unreachable by the name people actually type.
- **Every line costs context in every session.** A skill earns its place by stating what the
  model *cannot* infer — exact IDs, endpoints, credential locations, file paths, API quirks,
  house rules — not by narrating procedure a current model already knows.

### Adding a skill

```
.claude/skills/<skill-name>/SKILL.md
```

```markdown
---
name: <skill-name>          # must equal the folder name
description: What it does, when to use it, and the literal phrases that should trigger it.
---

# <Title>

...
```

`description` is the only text the model sees when deciding whether to load the skill, so make it
discriminating and include real trigger phrases. Keep frontmatter to flat `key: value` scalars;
`name`, `description`, `allowed-tools`, and `license` are the only keys the validator accepts.

### Validating

```bash
python3 scripts/validate_skills.py
```

It checks that each skill has a `SKILL.md` with parseable frontmatter, that `name` matches its
folder, that no two skills across the three roots share a name, and that nothing references
infrastructure this workspace has retired (Rube MCP, Greptile, the pipedream MCP servers). Run it
before opening a PR; it exits non-zero on any failure.
