---
name: github-ticket
description: Work with GitHub tickets. Fetches issue details, runs discovery, posts questions on the issue, handles sub-issues, and implements with PR. Activate with "/github-ticket 83", "/github-ticket 83 --dev", "/github-ticket 83 --linear SAT-328", or "work on ticket 83".
---

# github-ticket

GitHub is the work-product layer (plan, review, execution). A linked Linear ticket is the orchestration/guidance layer only — GitHub holds the finalized spec and PRs.

## Dependencies

- `gh` CLI (authenticated)
- Composio CLI (optional, for Linear guidance): `composio execute LINEAR_GET_LINEAR_ISSUE -d '{"issueId":"<ID>"}'` via the `satchel-linear` account (`linear_uhllo-extol`). Verified fallback: direct Linear GraphQL via the `$LINEAR_API_KEY` env var.
- Optional: `playwright-cli` skill for screenshot-based acceptance checks

## Invocation

```text
/github-ticket <number> [--dev] [--repo <owner/repo>] [--linear <TICKET-ID>]
```

Accepts `5`, `#5`, or a full issue URL (extract number + repo).

**Repo resolution** (priority order): `--repo` flag > primary repo declared in CLAUDE.md > git remote of cwd. If none resolve, ask the user for `--repo <owner/repo>`.

## Flags

| Flag | Behavior |
|------|----------|
| (none) | **Discover** — fetch ticket (+ Linear guidance, + sub-issues), explore codebase, post plan + questions on the issue |
| `--dev` | **Implement** — read finalized spec from the issue thread, branch, implement, open PR |

Flow spans sessions via the issue thread: discovery posts a comment → async discussion → user says "lock spec" → Claude posts a `## Finalized Spec` comment → `--dev` reads it and implements.

If `--linear <ID>` is passed, or the issue body links a Linear ticket (e.g. `linear.app/.../issue/SAT-328`), fetch it and fold its description into discovery as why/sequencing/acceptance guidance.

## Discover (default)

1. `gh issue view <number> --repo <repo> --json number,title,body,labels,milestone,comments,state,assignees`
2. Sub-issues are not returned by `gh issue view` — query GraphQL, and paginate: `first: 100` is not a guarantee, a parent can have more.

   ```bash
   gh api graphql -f query='
   query($owner:String!,$repo:String!,$num:Int!,$cursor:String){
     repository(owner:$owner,name:$repo){
       issue(number:$num){
         subIssues(first:100, after:$cursor){
           nodes { number title state }
           pageInfo { hasNextPage endCursor }
         }
       }
     }
   }' -F owner=<owner> -F repo=<repo> -F num=<number> -F cursor=null
   ```

   Repeat with `cursor=<endCursor>` while `hasNextPage` is true. `number`/`title`/`state` alone can't support per-sub-issue acceptance criteria — for each sub-issue in the full paginated set, fetch `gh issue view <sub-issue-number> --repo <repo> --json body,comments` before planning. If sub-issues exist, treat the parent as an orchestration index: list them, derive per-sub-issue acceptance criteria from each fetched body/comments, and plan one branch+PR per sub-issue in `--dev`. Empty result = single-issue flow, not an error.
3. Assess complexity: **Trivial** (single file, obvious fix) → ask "want me to just fix it and open a PR?"; **Standard** (2-5 files, clear requirements) → discovery + questions; **Complex** (multi-file, architectural, ambiguous, or has sub-issues) → full discovery, launching 2-3 parallel `Explore` agents (feature area / existing patterns / architecture-integration points for complex).
4. Post one structured comment on the issue: Understanding (cite Linear guidance if used), Sub-Issues checklist w/ acceptance criteria, Codebase Analysis (files to modify / patterns to follow / data sources), Questions, Estimated Complexity. If there are no open questions, say so and offer to post the finalized spec immediately.
5. Tell the user: discuss on the issue, say "lock spec" when settled, then run `--dev`.

## Locking the spec

On the user saying **"lock spec"** (a human decision — no CI gate), post a `## Finalized Spec` comment with the agreed requirements, acceptance criteria, and per-sub-issue checklist.

## Implement (--dev)

1. Re-fetch the ticket + comments, and re-run the sub-issue GraphQL query.
2. Scan comments for `## Finalized Spec`. None found, and no discovery comment with zero open questions → tell the user to say "lock spec" first (or run discovery if none has happened).
3. For a parent with sub-issues, repeat steps 4-7 per sub-issue; for a single issue, run once.
4. Branch:

   ```bash
   git checkout main && git pull origin main
   git checkout -b story-<number>-<slug>
   ```

   Slug: lowercase title, spaces→hyphens, max 40 chars, no special chars.
5. Complex tickets: launch 2-3 `general-purpose` agents as architects (minimal-changes / clean-architecture / pragmatic-balance), present options, get user approval before implementing. Standard tickets: implement directly.
6. Implement following codebase conventions; track progress with TodoWrite; auto-detect and run the build/test command (`package.json` scripts → `npm run build`/`npm test`; `Makefile` → `make`/`make test`; `Cargo.toml` → `cargo build`/`cargo test`; `pyproject.toml`/`setup.py` → project's documented command). Skip if none detected. Don't open the PR until the build is clean.
7. Push and open the PR:

   ```bash
   git push -u origin story-<number>-<slug>
   gh pr create --repo <repo> --title "<concise title>" --body "$(cat <<'EOF'
   ## Finalized Spec
   [paste the locked spec from the issue]
   ## Implementation
   - [what was built] / [key decisions] / [files modified]
   ## Test Plan
   - [ ] Build/tests pass
   - [ ] [feature-specific checks]
   - [ ] [if applicable] playwright-cli screenshot confirms the rendered result
   Closes #<number>
   Linear: <TICKET-ID> (if applicable)
   EOF
   )"
   ```

8. Comment `Implemented in PR #<pr-number>.` on the issue. Add the milestone to the PR if the ticket had one.

## Manual triggers (any session, after --dev)

| User says | Action |
|-----------|--------|
| "lock spec" | Post the `## Finalized Spec` comment on the issue |
| "update ticket" | Post a progress comment with completed/remaining todos |
| "close ticket" | Comment a final summary, then `gh issue close` |

## Error handling

| Error | Response |
|-------|----------|
| Issue not found | "Check the number or repo, or run `gh issue list --repo <repo>`." |
| Repo not resolved | "Pass `--repo <owner/repo>`." |
| No locked spec for `--dev` | "Say 'lock spec' on the issue first." |
| Sub-issue query empty | Treat as a single-issue ticket (not an error) |
| Build fails | Fix it — don't open the PR until it builds clean |
| Branch already exists | Ask: switch to it, or create a new one? |

## Complement: official @claude GitHub App

For PR-side `@claude` review/quick-fix mentions (separate from this skill's issue→plan→PR flow): run `/install-github-app`, or install https://github.com/apps/claude, add an `ANTHROPIC_API_KEY` repo secret, and add `.github/workflows/claude.yml` from `anthropics/claude-code-action`.
