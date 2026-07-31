---
name: vercel-comments-deployment
description: Reviews outstanding Vercel toolbar comments, confirms proposed changes with the user in a table, executes them, deploys to production, marks threads resolved, and posts a summary to the GitHub Issue. Activate on "review vercel comments" — no project name needed if CLAUDE.md declares a Vercel project.
---

# vercel-comments-deployment

Actions outstanding Vercel toolbar comments end-to-end: triage → confirm → implement → deploy → resolve → record. **The step order below is load-bearing — do not reorder or skip the confirmation gate.**

## Dependencies

- Bash (git, `gh` CLI), Read/Edit/Write, ToolSearch (to load Vercel MCP tool schemas before use)
- Vercel MCP: `mcp__claude_ai_Vercel__list_toolbar_threads`, `get_toolbar_thread`, `reply_to_toolbar_thread`, `change_toolbar_thread_resolve_status`, `get_project`, `list_deployments`
- `gh` CLI authenticated; project has a GitHub remote with Issues enabled; Vercel project name declared in CLAUDE.md (or supplied by the user)

## 0. Load Vercel MCP tools

```
ToolSearch: select:mcp__claude_ai_Vercel__list_toolbar_threads,mcp__claude_ai_Vercel__get_toolbar_thread,mcp__claude_ai_Vercel__reply_to_toolbar_thread,mcp__claude_ai_Vercel__change_toolbar_thread_resolve_status,mcp__claude_ai_Vercel__get_project,mcp__claude_ai_Vercel__list_deployments
```

## 1. Identify the Vercel project

Check CLAUDE.md for a declared project name/URL — use it without asking. Only prompt the user if none is resolvable from CLAUDE.md or the request. Validate with `get_project` and retrieve the project ID.

## 2. Retrieve outstanding threads

`list_toolbar_threads` for the project → filter to **not resolved** → `get_toolbar_thread` per thread for full message history.

## 3. Determine approval status

For threads with more than one message: scan for an explicit **"approved"** comment (case-insensitive). Found → note who approved and use it as authoritative. Not found → flag **"needs approval"**, do not execute. Single-message threads (original comment only) are approved by default.

## 4. Synthesize each change

Per actionable thread, produce: what exists now (current text/element/style/behavior), what it should become, and location (file path + line/selector if determinable). If the target is unclear, the change conflicts with existing logic, or scope is unspecified — ask a focused clarifying question. Do not guess.

## 5. Present the approval table — hard stop

```markdown
| # | Thread ID | Page / Element | Current State | Proposed Change | Status |
|---|-----------|---------------|---------------|-----------------|--------|
| 1 | abc123 | /about — Hero headline | "Welcome to X" | "Build with X" | Ready |
| 2 | def456 | /pricing — CTA button | "Get started" | "Start free trial" | Needs approval |
```

Ask: "Should I proceed with all Ready items? Flag any you want to skip or adjust." **Wait for explicit user confirmation before executing anything.**

## 6. Execute the changes

Per approved change: locate file(s) with Read/Grep/Glob, apply with Edit, verify the diff before moving to the next item.

## 7. Commit, push, open a PR

```bash
git add <changed files>
git commit -m "Apply Vercel toolbar feedback: <brief summary>"
git push origin HEAD
gh pr create --title "Vercel toolbar feedback: <summary>" --body "<table of changes>"
```

## 8. Deploy to production

Merge the PR (or confirm with the user if they prefer manual merge). Use `list_deployments` to confirm the production deployment completed and get the URL. If the project auto-deploys on merge to `main`, poll until status is `READY`.

## 9. Mark threads resolved

Per actioned thread: `reply_to_toolbar_thread` with "Change applied — [description]. Deployed in [PR link]." then `change_toolbar_thread_resolve_status` to resolved.

## 10. Post summary to the GitHub Issue

```bash
gh issue create --title "Vercel toolbar comments resolved — <date>" \
  --body "<summary table>\n\nProduction URL: <url>\nPR: <pr url>"
```

If a relevant open Issue already exists (e.g. a design-feedback tracker), comment instead: `gh issue comment <number> --body "<summary>"`. Report the Issue URL to the user.

## Notes

- The "approved" keyword check is intentionally simple — if the project uses a different convention (thumbs-up reaction, a named reviewer), note it in CLAUDE.md.
- If the project doesn't auto-deploy on merge, wait for the user to trigger the deploy manually before step 9.
- Scope: copy, UI element, and style changes in source files only — not database schema, API, or infrastructure-level comments.
- Related skills: `vercel:deploy`, `vercel:deployments-cicd`, `commit-commands:commit-push-pr`.
