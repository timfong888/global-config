---
name: frontend-performance-audit
description: Audits Next.js/React code for performance anti-patterns. Modes full (Vercel's 51-rule/8-category audit + GitHub issues), bundle (barrel imports, dynamic imports, tree-shaking), rerender (missing useMemo/useCallback, derived state). Activate on "audit performance", "nextjs audit", "check bundle", "check re-renders".
---

# frontend-performance-audit

Audits Next.js/React codebases for performance anti-patterns. Read-only except for GitHub issue creation in `full` mode — never edits source files.

## Modes

- `full` — audit against Vercel's 51 performance rules / 8 categories; score each category; file one GitHub issue per finding.
- `bundle` — barrel imports, dynamic-import candidates, tree-shaking config (deeper pass on category 2 below).
- `rerender` — missing useMemo/useCallback, derived-state anti-patterns, over-subscribed components, React.memo candidates (deeper pass on category 5 below).

Invocation: `/frontend-performance-audit [full|bundle|rerender]` — default `full`.

## Dependencies

Bash, Read, Grep, Glob. `gh` CLI required only for `full` mode's issue creation.

## Setup (all modes)

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
```

Warn (don't block) if no `next.config.{js,ts,mjs}` is found. If `full` mode can't resolve `REPO`, ask the user.

## Mode: full — 8-category rule taxonomy

Only these 17 rules are individually specified in the source material this skill was built from — the remainder of the claimed 51 are not enumerated anywhere and must not be invented. If asked for full 51-rule coverage, say so.

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

Run categories in priority order (1 → 8). For categories 2 and 5, reuse the `bundle`/`rerender` mode search commands below rather than duplicating them.

### Scoring

Per category, 0-100: 90-100 excellent · 70-89 good · 50-69 acceptable · 30-49 needs work · 0-29 critical.

### Scorecard

```markdown
## Overall Score: {avg}/100
| Category | Score | Priority | Issues |
|----------|-------|----------|--------|
| 1. Eliminating Waterfalls | X/100 | CRITICAL | Y |
...
**Critical (P0):** n  **High (P1):** n  **Medium (P2):** n  **Low (P3):** n
```

### GitHub issue per finding

```bash
gh issue create --repo {REPO} \
  --title "[Performance] {rule-id}: {brief description}" \
  --label "performance" \
  --body "$(cat <<'EOF'
## Rule Violated
**Category:** {category}  **Rule:** {rule-id}  **Impact:** {CRITICAL|HIGH|MEDIUM|LOW}
## Location
`{file}:{line}`
## Current Code / Recommended Fix
{before snippet} / {after snippet}
## Why This Matters
{one-line explanation}
EOF
)"
```

Reference: https://github.com/vercel-labs/agent-skills. Don't suggest replacing UI libraries the project has already standardized on — flag the perf cost, not a swap.

## Mode: bundle

| Library | Barrel cost | Fix |
|---|---|---|
| recharts | 200-400ms | direct: `recharts/es6/chart/LineChart` |
| lodash | 200-300ms | `lodash-es` or direct path |
| @mui/material | 300-500ms | `@mui/material/ComponentName` |
| date-fns | 100-200ms | `date-fns/function` |
| @heroicons/react, lucide-react | 100-200ms | `optimizePackageImports` |
| ethers | 150-250ms | consider `viem` |

```bash
grep -rn "from 'recharts'\|from 'lodash'\|from '@mui/material'\|from 'date-fns'\|from '@heroicons/react'\|from 'lucide-react'" --include="*.ts" --include="*.tsx"
grep -rn "import.*Chart\|import.*Editor\|import.*Map\|import.*PDF" --include="*.tsx" | grep -v "next/dynamic"
grep -rn "dynamic(" --include="*.tsx" | wc -l
grep -rn "optimizePackageImports" next.config.*
```

Dynamic-import candidates: charts, rich-text editors, PDF viewers, maps, heavy modals.

```typescript
const Dashboard = dynamic(() => import('@/components/Dashboard'), {
  loading: () => <DashboardSkeleton />,
  ssr: false, // client-only
});
```

Recommended `next.config.ts`:

```typescript
experimental: { optimizePackageImports: ['recharts', 'lodash', '@heroicons/react', 'date-fns'] }
```

Report: `Library | Files | Est. Impact | Priority` table, plus `Component | File | Reason` table for dynamic-import candidates.

## Mode: rerender

```bash
grep -rn "\.map(\|\.filter(\|\.reduce(\|\.sort(" --include="*.tsx" | grep -v "useMemo"
grep -rn "Object\.keys\|Object\.values\|Object\.entries" --include="*.tsx" | grep -v "useMemo"
grep -rn "onClick={() =>\|onChange={() =>\|onSubmit={() =>" --include="*.tsx"
grep -rn "const \[.*\] = useState" --include="*.tsx" -A 2
grep -rn "useEffect.*set" --include="*.tsx"
grep -rn "useSelector\|useContext\|useStore" --include="*.tsx"
grep -rn "useMemo(\|useCallback(\|React\.memo\|memo(" --include="*.tsx" | wc -l   # existing coverage
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
