---
name: frontend-performance-audit
description: Audits Next.js/React code for performance anti-patterns. Modes full (17-rule/8-category audit + GitHub issues), bundle (barrel imports, dynamic imports, tree-shaking), rerender (missing useMemo/useCallback, derived state). Activate on "audit performance", "nextjs audit", "check bundle", "check re-renders".
---

# frontend-performance-audit

Audits Next.js/React codebases for performance anti-patterns. Read-only except for GitHub issue creation in `full` mode — never edits source files.

## Modes

- `full` — audit against the 17 rules / 8 categories specified below; score each category; file one GitHub issue per finding.
- `bundle` — barrel imports, dynamic-import candidates, tree-shaking config (deeper pass on category 2 below).
- `rerender` — missing useMemo/useCallback, derived-state anti-patterns, over-subscribed components, React.memo candidates (deeper pass on category 5 below).

Invocation: `/frontend-performance-audit [full|bundle|rerender]` — default `full`.

## Dependencies

Bash, Read, Grep, Glob. `gh` CLI required only for `full` mode's issue creation.

## Setup (all modes)

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$PROJECT_ROOT"
EXCLUDE_DIRS='node_modules,.next,dist,build,out,coverage,.git'
```

Run every scan command below from `$PROJECT_ROOT` (not the invocation directory) so a subdirectory invocation still audits the whole project. Warn (don't block) if no `next.config.{js,ts,mjs}` is found. Every recursive `grep -r` in this skill must add `--exclude-dir=$EXCLUDE_DIRS` (or use `git grep`, which only scans tracked files) — without it, generated and dependency code dominates the scan and produces false findings.

`full` mode only, also resolve the repo before scanning:

```bash
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
```

If `REPO` can't be resolved, ask the user. Don't run this in `bundle` or `rerender` mode — they never call `gh`.

## Mode: full — 17-rule / 8-category taxonomy

This skill implements 17 rules across 8 categories, sourced from Vercel's performance-rules reference (linked below). That reference names a larger rule set, but only these 17 are individually specified here — the rest are not enumerated anywhere available to this skill and must not be invented. If asked for broader coverage, say so.

| # | Rule ID | Category | Priority | Check |
|---|---------|----------|----------|-------|
| 1.1 | async-parallel | 1. Eliminating Waterfalls | CRITICAL (2-10x) | Sequential `await`s that should be `Promise.all` |
| 1.2 | async-defer-await | 1. Eliminating Waterfalls | CRITICAL | `await` before a branch — move into the branch that uses it |
| 1.3 | async-suspense-boundaries | 1. Eliminating Waterfalls | CRITICAL | Data-fetching components without strategic `<Suspense>` |
| 2.1 | bundle-barrel-imports | 2. Bundle Optimization | CRITICAL (200-800ms) | Barrel imports from large libs — see Mode: bundle |
| 2.2 | bundle-dynamic-imports | 2. Bundle Optimization | CRITICAL | Heavy components not wrapped in `next/dynamic` |
| 2.3 | bundle-tree-shaking | 2. Bundle Optimization | CRITICAL | Missing `optimizePackageImports` in `next.config` |
| 3.1 | server-cache-react | 3. Server-Side Performance | HIGH | Missing `React.cache()` for per-request dedup |
| 3.2 | server-serialization | 3. Server-Side Performance | HIGH | Oversized objects/arrays passed to client components |
| 4.1 | client-swr-dedup | 4. Client-Side Data Fetching | MEDIUM-HIGH | Manual `useEffect` fetch instead of SWR/React Query dedup |
| 5.1 | rerender-memo | 5. Re-render Optimization | MEDIUM | Expensive `.map/.filter/.reduce` without `useMemo` — see Mode: rerender |
| 5.2 | rerender-derived-state | 5. Re-render Optimization | MEDIUM | State derived from other state via `useEffect`+`setState` |
| 6.1 | rendering-hoist-jsx | 6. Rendering Performance | MEDIUM | Static JSX defined inside a component body |
| 6.2 | rendering-virtual-list | 6. Rendering Performance | MEDIUM | Long list `.map()` without virtualization |
| 7.1 | js-spread-last | 7. JavaScript Performance | LOW-MEDIUM | Spread operator not last in object assignment |
| 7.2 | js-memo-expensive | 7. JavaScript Performance | LOW-MEDIUM | Expensive computation not memoized |
| 8.1 | advanced-use-transition | 8. Advanced Patterns | LOW | Non-urgent updates not wrapped in `startTransition` |
| 8.2 | advanced-optimistic-updates | 8. Advanced Patterns | LOW | Missing optimistic-UI pattern where applicable |

Run categories in priority order (1 → 8). For categories 2 and 5, reuse the `bundle`/`rerender` mode search commands below rather than duplicating them. Rule 2.3 requires Next.js ≥ 13.5 — check the project's `next` version (`package.json`) before flagging a missing `optimizePackageImports` as CRITICAL; on older versions mark it not-applicable instead.

### Priority mapping

Map each rule's taxonomy priority to a scorecard bucket:

| Rule priority | Scorecard bucket |
|---|---|
| CRITICAL | P0 |
| HIGH, MEDIUM-HIGH | P1 |
| MEDIUM | P2 |
| LOW-MEDIUM, LOW | P3 |

### Scoring

Per category, start at 100 and deduct once per finding by its bucket: P0 −25, P1 −15, P2 −8, P3 −4. Floor the category at 0. Round every score (category and overall) to the nearest integer, half up. Bands (post-deduction): 90-100 excellent · 70-89 good · 50-69 acceptable · 30-49 needs work · 0-29 critical. `{avg}` in the scorecard below = the mean of the 8 category scores, rounded the same way.

### Scorecard

```markdown
## Overall Score: {avg}/100
| Category | Score | Priority | Issues |
|----------|-------|----------|--------|
| 1. Eliminating Waterfalls | X/100 | CRITICAL | Y |
...
**Critical (P0):** n  **High (P1):** n  **Medium (P2):** n  **Low (P3):** n
```

### Approval gate — required before any GitHub write

Filing or editing issues is an outbound side effect, not a read. After scoring, show the user the scorecard and the full findings list (rule, file:line, category) and stop. Do not run `gh issue create` or `gh issue edit` until the user explicitly approves — either the whole batch or a named subset. If they approve a subset, file only those findings.

### GitHub issue per finding (idempotent)

Only after approval. Every issue carries a stable marker (`rule-id` + `file:line`) so re-running the audit updates instead of duplicating:

```bash
MARKER="<!-- perf-audit: {rule-id} @ {file}:{line} -->"
EXISTING=$(gh issue list --repo {REPO} --state all --search "\"$MARKER\" in:body" --json number -q '.[0].number')
```

If `$EXISTING` is non-empty, skip (or `gh issue edit $EXISTING --body ...` to refresh) — don't create. Otherwise, confirm the `performance` label exists first — `gh issue create --label` fails outright if it doesn't:

```bash
gh label list --repo {REPO} --json name -q '.[].name' | grep -qx performance
```

If that check fails, either create the label (`gh label create performance --repo {REPO} --color BFD4F2 --description "Performance audit finding"`) or drop `--label "performance"` from the command below — ask the user which they want rather than guessing. Then:

```bash
gh issue create --repo {REPO} \
  --title "[Performance] {rule-id}: {brief description}" \
  --label "performance" \
  --body "$(cat <<EOF
$MARKER
## Rule Violated
**Category:** {category}  **Rule:** {rule-id}  **Impact:** {CRITICAL|HIGH|MEDIUM|LOW}
## Location
\`{file}:{line}\`
## Current Code / Recommended Fix
{before snippet} / {after snippet}
## Why This Matters
{one-line explanation}
EOF
)"
```

Reference: https://github.com/vercel-labs/agent-skills. Don't suggest replacing UI libraries the project has already standardized on — flag the perf cost, not a swap.

## Mode: bundle

Rough, environment-dependent reference values only (bundler, package version, and build mode all shift them) — before using them to rank or prioritize findings, measure the project's actual impact (`next build` output or `@next/bundle-analyzer`) and report that measured figure instead.

| Library | Barrel cost (reference) | Fix |
|---|---|---|
| recharts | 200-400ms | direct: `recharts/es6/chart/LineChart` |
| lodash | 200-300ms | `lodash-es` or direct path |
| @mui/material | 300-500ms | `@mui/material/ComponentName` |
| date-fns | 100-200ms | `date-fns/function` |
| @heroicons/react, lucide-react | 100-200ms | `optimizePackageImports` |
| ethers | 150-250ms | consider `viem` |

```bash
grep -rn --exclude-dir=$EXCLUDE_DIRS "from 'recharts'\|from 'lodash'\|from '@mui/material'\|from 'date-fns'\|from '@heroicons/react'\|from 'lucide-react'" --include=*.{ts,tsx,js,jsx}
grep -rn --exclude-dir=$EXCLUDE_DIRS "import.*Chart\|import.*Editor\|import.*Map\|import.*PDF" --include=*.{tsx,jsx} | grep -v "next/dynamic"
grep -rn --exclude-dir=$EXCLUDE_DIRS "dynamic(" --include=*.{tsx,jsx} | wc -l
grep -rn "optimizePackageImports" next.config.*
```

Dynamic-import candidates: charts, rich-text editors, PDF viewers, maps, heavy modals.

`ssr: false` only works inside a Client Component — Next.js throws if the call is in a Server Component. Put it in a file (or wrapper) starting with `'use client'`:

```typescript
'use client';
const Dashboard = dynamic(() => import('@/components/Dashboard'), {
  loading: () => <DashboardSkeleton />,
  ssr: false, // client-only, requires 'use client'
});
```

Recommended `next.config.ts` — merge into the project's existing `experimental` block, don't replace it (other experimental flags may already be set):

```typescript
experimental: { optimizePackageImports: ['recharts', 'lodash', '@heroicons/react', 'date-fns'] }
```

Report: `Library | Files | Est. Impact | Priority` table, plus `Component | File | Reason` table for dynamic-import candidates.

## Mode: rerender

```bash
grep -rn --exclude-dir=$EXCLUDE_DIRS "\.map(\|\.filter(\|\.reduce(\|\.sort(" --include=*.{ts,tsx,js,jsx} | grep -v "useMemo"
grep -rn --exclude-dir=$EXCLUDE_DIRS "Object\.keys\|Object\.values\|Object\.entries" --include=*.{ts,tsx,js,jsx} | grep -v "useMemo"
grep -rn --exclude-dir=$EXCLUDE_DIRS "onClick={() =>\|onChange={() =>\|onSubmit={() =>" --include=*.{tsx,jsx}
grep -rn --exclude-dir=$EXCLUDE_DIRS "const \[.*\] = useState" --include=*.{ts,tsx,js,jsx} -A 2
grep -rn --exclude-dir=$EXCLUDE_DIRS "useEffect.*set" --include=*.{ts,tsx,js,jsx}
grep -rn --exclude-dir=$EXCLUDE_DIRS "useSelector\|useContext\|useStore" --include=*.{ts,tsx,js,jsx}
grep -rn --exclude-dir=$EXCLUDE_DIRS "useMemo(\|useCallback(\|React\.memo\|memo(" --include=*.{ts,tsx,js,jsx} | wc -l   # existing coverage
```

Flag:
- Expensive `.map/.filter/.reduce/.sort` or `Object.keys/values/entries` in render, unmemoized → wrap in `useMemo`.
- Inline arrow functions passed as props (`onClick={() => ...}`) to memoized children → `useCallback`.
- State derived from other state via `useEffect`+`setState` → compute inline or via `useMemo` instead of storing.
- `useSelector`/`useContext` subscribing to a whole object instead of the field actually used → narrow the selector.
- Pure presentational components with stable props still re-rendering → `React.memo` candidate.

`useCallback` only pays off when passed to a memoized child — don't flag it in isolation.

Report:

```markdown
| Category | Issues Found | Priority |
|----------|--------------|----------|
| Missing useMemo | X | P1 |
| Missing useCallback | X | P2 |
| Derived State Anti-patterns | X | P1 |
| Over-subscribed Components | X | P2 |
| React.memo Candidates | X | P3 |
```

Plus a `File | Line | Issue | Fix` detail table per category.
