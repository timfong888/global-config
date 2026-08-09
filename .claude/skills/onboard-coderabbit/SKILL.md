---
name: onboard-coderabbit
description: Wire a GitHub repository into the CodeRabbit+Sourcery → Linear closed review loop. Copies three template files, documents the one manual secret step, and verifies the chain end-to-end. Use when asked to "add CodeRabbit to a repo", "wire up the review loop", "set up code review notifications", or "onboard a repo to the review pipeline".
---

# onboard-coderabbit

Wire a target GitHub repo into the CodeRabbit → Sourcery → Linear `@blocks` notification
loop so every AI review automatically triggers a Blocks agent session.

**What the loop does:** when CodeRabbit or Sourcery reviews a PR, a GitHub Action fires,
extracts the Linear issue ID from the branch name, and posts an `@blocks` mention comment
on that issue — activating the Blocks agent to triage the review feedback.

---

## Prerequisites (check before starting)

```bash
# Confirm gh is authenticated
gh auth status

# Confirm the target repo exists and you have push access
gh repo view <owner>/<repo>
```

The two bot apps must have access to the repo:
- **CodeRabbit:** <https://app.coderabbit.ai> → Repositories → enable the repo
- **Sourcery:** <https://sourcery.ai> → Repositories → enable the repo

If either isn't enabled, note it in the handback and continue — the workflow will still
fire for whichever bot IS enabled.

---

## Step 1 — Clone the target repo

```bash
# Clone using the Blocks MCP tool (not git clone directly)
mcp__blocks-internal-mcp__clone_repository_into_folder
  url: <repo-url>
  folder_name: <repo-name>
```

---

## Step 2 — Copy the three template files

Templates live in `timfong888/global-config/github-actions/examples/`.
Clone global-config if not already present:

```bash
# Clone global-config to get the templates
mcp__blocks-internal-mcp__clone_repository_into_folder
  url: https://github.com/timfong888/global-config
  folder_name: global-config
  ref: main
```

Copy into the target repo:

```bash
TARGET=/home/user/workspace/<repo-name>

mkdir -p "$TARGET/.github/workflows"

cp workspace/global-config/github-actions/examples/on-coderabbit-review.yml \
   "$TARGET/.github/workflows/coderabbit-to-linear.yml"

cp workspace/global-config/github-actions/examples/.coderabbit.yml \
   "$TARGET/.coderabbit.yml"

cp workspace/global-config/github-actions/examples/.sourcery.yaml \
   "$TARGET/.sourcery.yaml"
```

Verify the three files exist before continuing.

---

## Step 3 — Check for the LINEAR_API secret

```bash
gh secret list --repo <owner>/<repo> | grep LINEAR_API
```

If the secret is missing, you **cannot set it programmatically** (GitHub secrets API
requires admin write access). Report this in the handback with exact instructions:

> Tim: please add `LINEAR_API` to `<owner>/<repo>` Settings → Secrets and variables →
> Actions → New repository secret. Value: a Linear personal API key from
> <https://linear.app/settings/api> (Personal API keys section).

Do not block the PR on this — open the PR, note the missing secret, and continue.

---

## Step 4 — Commit and open a PR

```bash
cd /home/user/workspace/<repo-name>

git checkout -b feature/onboard-coderabbit-review-loop

git add .github/workflows/coderabbit-to-linear.yml .coderabbit.yml .sourcery.yaml

git commit -m "Add CodeRabbit+Sourcery → Linear review loop

Wires the AI review bot notification chain:
- .github/workflows/coderabbit-to-linear.yml — calls reusable workflow in global-config
- .coderabbit.yml — enables CodeRabbit auto-reviews
- .sourcery.yaml — enables Sourcery auto-reviews

Requires LINEAR_API secret in repo settings (see PR description)."
```

Then create the PR using `mcp__blocks-internal-mcp__create_pull_request`.

---

## Step 5 — Verify end-to-end (optional but recommended)

After the PR merges and the secret is set:

1. Open a **draft PR** on a branch named `blocks/SAT-XXX-test` (any real Linear ID)
2. Wait for CodeRabbit or Sourcery to post a review (usually within 2–5 minutes)
3. Check the linked Linear issue — an `@blocks` comment should appear within ~30 seconds
   of the review posting

If no comment arrives after 5 minutes:
- Check Actions tab on GitHub for workflow run errors
- Verify `LINEAR_API` secret is set
- Verify CodeRabbit/Sourcery has access to the repo
- Confirm the branch name matches the `[TEAM]-[NUMBER]` pattern

---

## Branch naming convention (important)

The workflow only fires for branches that carry a recognisable Linear identifier:

```
blocks/SAT-660-my-feature   ✅  → SAT-660
feature/BLO-123-title       ✅  → BLO-123
my-fix-branch               ❌  silently skipped
```

---

## Handback template

```
✅ **CodeRabbit → Linear loop wired for `<owner>/<repo>`**

- **PR:** [PR #N: title](url)
- **Files added:** `.github/workflows/coderabbit-to-linear.yml`, `.coderabbit.yml`, `.sourcery.yaml`
- **Secret needed:** `LINEAR_API` — Tim must add it at repo Settings → Secrets → Actions
- **Bot access:** CodeRabbit [enabled/not enabled] · Sourcery [enabled/not enabled]
- **Verify:** open a draft PR on `blocks/SAT-XXX-test` after merging; an `@blocks` comment on the linked Linear issue confirms the chain is live

[model: <m>, effort: <e>] (by Claude)
```
