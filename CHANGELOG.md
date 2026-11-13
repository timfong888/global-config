# Changelog

Notable changes to this repo. Newest first. Skill-selection rationale lives in
`SKILLS-INVENTORY.md`; this file records what changed and when.

## 2026-11-12 — Vendored design-build and interface-review skills

Added 9 skills under `.claude/skills/`, copied from the global `npx skills add` installs so they
load in every Blocks session.

| Skill | Upstream | Notes |
|---|---|---|
| `web-design-engineer` | [ConardLi/garden-skills](https://github.com/ConardLi/garden-skills) `skills/web-design-engineer` v1.3.0 (folder hash `d6b39956`) | Builder for HTML/CSS/JS/React visual artifacts. Dropped `README.md` and `README.zh-CN.md` (~55KB, unused at runtime). |
| `better-interface` | [jakubkrehel/skills](https://github.com/jakubkrehel/skills) @ `a72290d` | Full-page reviewer; orchestrates the six `better-*` skills below. |
| `better-accessibility`, `better-colors`, `better-layout`, `better-typography`, `better-ui`, `better-writing` | same, @ `a72290d` | Vendored because `better-interface` routes to them; without them its review degrades. |
| `interface-review` | same, @ `a72290d` | Change-scoped review (branch, PR, uncommitted). |

Not vendored from `jakubkrehel/skills`: `afk`, `break`, `build-design`, `explain-interface`,
`state-machine`, `variant`.

**Local edit:** removed `disable-model-invocation: true` from `interface-review/SKILL.md`. The
validator only allows `name`, `description`, `allowed-tools`, `license`. Side effect: the model can
now auto-select this skill instead of it being manual-only. Re-apply on any upstream re-sync.

**Validator:** no new errors. The 10 existing errors on `main` (`whenToUse` keys, `composio-personal`
reference, unquoted `coderabbit` description) are untouched.

**Re-sync:** copy from upstream at a newer commit, re-remove the key above, and bump the SHA here.
