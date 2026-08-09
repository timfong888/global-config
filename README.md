# global-config

Global configuration for agents. Blocks loads this repo as the **global config repo**, so
everything here is merged into *every* Blocks session — the sandbox, Slack, GitHub, and Linear.

| Path | What it is |
|---|---|
| `.claude/skills/<name>/SKILL.md` | Skills. The folder name becomes the `/<name>` slash command. |
| `.blocks/post-clone` | Runs after Blocks clones the repo into a sandbox. |
| `mcp-servers/` | MCP servers published from this repo (currently `aurora`). |
| `.github/workflows/coderabbit-to-linear.yml` | Reusable workflow: AI review bot → Linear `@blocks` mention. |
| `github-actions/examples/` | Templates to copy into project repos (caller workflow + bot configs). |
| `scripts/validate_skills.py` | Pre-merge check that every skill is discoverable and unique. |
| `scripts/notify-linear.py` | Posts `@blocks` Linear comment when a review bot finishes a PR review. |
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

```text
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
folder, that no two distinct skills across the three roots share a name (a skill symlinked into a
second root is deduplicated by resolved path, not flagged), and that nothing references
infrastructure this workspace has retired. Run it before opening a PR; it exits non-zero on any
failure. `--selftest` exercises the frontmatter parser against known-bad inputs.

Frontmatter is a strict subset of YAML: flat `key: value` scalars only. A value containing `": "`
must be quoted, so the file parses identically whether or not PyYAML is installed.

## CodeRabbit → Linear closed loop

When CodeRabbit or Sourcery reviews a PR, a GitHub Actions workflow fires, extracts the Linear
issue ID from the branch name, and posts an `@blocks` mention comment on that issue — activating
the Blocks agent to triage the review feedback.

The reusable workflow lives here in `global-config`; project repos call it via a 6-line caller.

### Wiring a new project repo into the loop

**Copy three files** from `github-actions/examples/` into the target repo:

```bash
# From the root of the project repo:
cp path/to/global-config/github-actions/examples/on-coderabbit-review.yml \
   .github/workflows/coderabbit-to-linear.yml
cp path/to/global-config/github-actions/examples/.coderabbit.yml .coderabbit.yml
cp path/to/global-config/github-actions/examples/.sourcery.yaml  .sourcery.yaml
```

**Add one secret** — `LINEAR_API` — to the repo's GitHub settings
(Settings → Secrets → Actions → New repository secret).
Generate a Linear personal API key at <https://linear.app/settings/api> (Personal API keys).

**Grant two app permissions:**

- CodeRabbit: <https://app.coderabbit.ai> → Repositories → enable this repo
- Sourcery: <https://sourcery.ai> → Repositories → enable this repo

**Verify:** Open a draft PR on a branch named `blocks/SAT-XXX-test`. Once CodeRabbit or Sourcery
reviews it, check the linked Linear issue for an `@blocks` comment within a few minutes.

> **Tip:** Use the `onboard-coderabbit` skill (`Skill: onboard-coderabbit`) to let a Blocks agent
> walk through these steps automatically for a target repo.

### Branch naming convention

The workflow extracts the first `[TEAM]-[NUMBER]` token from the PR branch name:

```
blocks/SAT-660-my-feature   →  SAT-660
feature/BLO-123-title       →  BLO-123
fix/SAT-99-bug              →  SAT-99
```

Branches with no recognisable identifier are silently skipped.

### Required GitHub repository variable

`BLOCKS_LINEAR_USER_ID` must be set as a repository variable on `global-config`
(Settings → Secrets and variables → Actions → Variables tab).
Current value: `86010372-1d6d-4dd1-90a7-98445e7a9805` (the Blocks agent's Linear user ID).
This drives the `mentionedUserIds` field that fires the Linear `AppUserMentioned` webhook.
