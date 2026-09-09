---
name: coderabbit-linear-handoff
description: Set up the CodeRabbit → Linear → Blocks handoff loop for a GitHub repository. Adds a GitHub Actions workflow that fires when CodeRabbit submits a PR review and posts an @blocks trigger comment on the linked Linear issue. TRIGGER on: "set up coderabbit linear handoff", "wire up coderabbit to linear", "automate coderabbit blocks loop", "add coderabbit handoff to [repo]".
---

# CodeRabbit → Linear → Blocks Handoff Loop

This skill wires a GitHub repository into the automated loop:

```
PR opened → CodeRabbit reviews → GitHub Action fires →
  Linear issue gets @blocks comment → Blocks implements fixes →
  pushes → CodeRabbit re-reviews → repeat
```

All handoff events are timestamped Linear comments, so the full lineage lives in Linear.

---

## How It Works

1. A PR is opened on a branch named `blocks/SAT-XXX-...` (the standard Blocks branch convention)
2. CodeRabbit reviews the PR and submits a review
3. The GitHub Action in the target repo fires — it extracts `SAT-XXX` from the branch name
4. It resolves the Linear issue UUID via the Linear GraphQL API
5. It posts a comment to the Linear issue: **"CodeRabbit review complete on PR #X — @blocks please implement"**
6. Blocks (this system) picks up the @blocks mention and acts on the PR

---

## Setup Steps for a New Repository

### Step 1 — Verify prerequisites

- The repo has CodeRabbit installed (reviews appear automatically on PRs)
- PRs use the branch naming convention `blocks/SAT-XXX-description` or `feature/SAT-XXX-description`
- `LINEAR_API_KEY` secret is set in the repo's GitHub Actions secrets (Settings → Secrets and variables → Actions → New repository secret). Value: a Linear personal API key from **linear.app → Account Settings → Security → Personal API Keys**.

### Step 2 — Create the caller workflow

Create `.github/workflows/coderabbit-to-linear.yml` in the target repo with the following content.

**Replace `GLOBAL_CONFIG_DEFAULT_BRANCH`** with the current default branch of `timfong888/global-config` (check `git ls-remote --symref https://github.com/timfong888/global-config HEAD`).

```yaml
name: CodeRabbit → Linear Handoff

on:
  pull_request_review:
    types: [submitted]

jobs:
  notify-linear:
    # Only fire for CodeRabbit reviews (skip human reviews)
    if: github.event.review.user.login == 'coderabbitai[bot]'
    uses: timfong888/global-config/.github/workflows/coderabbit-to-linear-reusable.yml@GLOBAL_CONFIG_DEFAULT_BRANCH
    with:
      branch_name: ${{ github.event.pull_request.head.ref }}
      pr_url: ${{ github.event.pull_request.html_url }}
      pr_number: ${{ github.event.pull_request.number }}
      repo_full_name: ${{ github.repository }}
      review_state: ${{ github.event.review.state }}
    secrets:
      LINEAR_API_KEY: ${{ secrets.LINEAR_API_KEY }}
```

### Step 3 — Commit and push

```bash
git add .github/workflows/coderabbit-to-linear.yml
git commit -m "SAT-XXX: Add CodeRabbit → Linear handoff workflow"
git push
```

### Step 4 — Test

Open or update a PR on a branch named `blocks/SAT-XXX-...`. Wait for CodeRabbit to post its review. The Linear issue `SAT-XXX` should receive a comment within ~30 seconds. Check the Actions tab of the repo to debug if it doesn't fire.

---

## Reusable Workflow Location

The canonical workflow logic lives in:

```
timfong888/global-config/.github/workflows/coderabbit-to-linear-reusable.yml
```

Callers reference it with `uses:` and pass four inputs + one secret. The logic is maintained in one place — updating the reusable workflow propagates to all repos on the next run.

---

## Linear Comment Format

When CodeRabbit requests changes or comments:
> **CodeRabbit review complete** on [PR #X](url) in `owner/repo`.
> @blocks Please review CodeRabbit's comments on the PR and implement the required changes, then push to the same branch.

When CodeRabbit approves:
> **CodeRabbit approved** [PR #X](url) in `owner/repo` — no blocking issues found.
> @blocks PR is ready. Please confirm the branch is clean and merge when appropriate.

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Action never fires | Confirm CodeRabbit is installed on the repo; check `github.event.review.user.login` in Actions logs |
| "Could not resolve Linear issue" | Branch name doesn't contain a Linear issue ID; confirm `blocks/SAT-XXX-...` convention |
| "Failed to post comment" | `LINEAR_API_KEY` secret is missing or invalid; verify under repo Settings → Secrets |
| Multiple comments per review | CodeRabbit submits reviews incrementally; Blocks handles duplicate triggers gracefully via context |
