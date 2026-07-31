---
name: spec-review
description: Review dev/engineering specs across five lenses — clarity, completeness, DX, implementation readiness, technical accuracy. Triggers: review spec clarity, check spec coverage, review spec DX, implementation readiness review, engineering spec review, doc-to-dev-spec review. /spec-review runs all; --<lens> runs one.
---

# Spec Review

Merged from five ~500-line single-lens rubrics (dev-spec-clarity, dev-spec-completeness,
dev-spec-dx-review, dev-spec-implementation-readiness, dev-spec-technical-accuracy-v2), each
originally written for a weaker model that needed the criteria spelled out at length with
before/after prose examples. This file names the five lenses and keeps only the checks a
current model cannot infer on its own — exact thresholds, scoring bands, and checklist items
a reviewer would otherwise skip.

## Modes

- `/spec-review` — run all five lenses, report each separately, no averaged score.
- `/spec-review --clarity` — language precision and terminology only.
- `/spec-review --completeness` — coverage gaps only.
- `/spec-review --dx` — external-developer self-service usability only.
- `/spec-review --readiness` — internal implementation-readiness only.
- `/spec-review --accuracy` — internal engineering technical accuracy only.

## Clarity

- Replace "should/might/could/can be utilized" with "must/will/returns"; active voice; one idea
  per sentence, <20 words when possible.
- Same concept = same term everywhere (not "user" here, "account" there). Field names in prose
  must match field names in code examples exactly (`user_id` in text vs `userId` in JSON is a
  real bug, not a style nit).
- Required vs optional always stated explicitly. Numeric ranges state inclusive/exclusive
  bounds. All timestamps carry a timezone (UTC or explicit offset). "Or" statements disambiguated
  (either/both vs exclusive-or).
- Examples use realistic data (never foo/bar/test@test.com), are complete and runnable (not
  pseudocode), and include error handling.
- Score: EXCELLENT 90–100 / GOOD 75–89 / NEEDS IMPROVEMENT 60–74 / POOR <60, based on ambiguous
  statements found, terminology drift, and example completeness.

## Completeness

- Per-endpoint status-code checklist: flag docs that only show 200 and 500. Expect 400/401/403/
  404/409/422/429/503 wherever applicable, plus pagination, sorting, filtering, and idempotency
  behavior for list/write endpoints.
- Edge cases a first draft typically skips: empty-list response shape, null optional fields, max
  string/array size, Unicode/emoji input, numeric edges (0, negative, very large), concurrent or
  duplicate requests, partial batch failure, token expiring mid-operation.
- Each documented error needs: trigger condition, response body shape, retryable Y/N, and (for
  validation errors) which field failed.
- Workflows must be end-to-end (credential setup → auth → CRUD → error/retry handling →
  production checklist), not a 2-step summary.
- Versioning/migration: breaking changes enumerated, deprecated-feature sunset date, before/after
  code, and an explicit support-end date for the old version.
- Auth mechanics (external API references only, and easy to miss because no other lens asks):
  exact header format, OAuth/refresh-token flow, per-endpoint scope requirements, token lifetime,
  webhook signature verification, and whether HTTPS/CORS are enforced.
- Score: same 90/75/60 bands as Clarity, judged as % of the coverage matrix actually checked.

## Developer Experience (DX)

Audience: external customer-developer integrating self-service.

- Time-to-Hello-World target: under 15 minutes — one copy-paste request that returns a
  verifiable success signal, with expected-response and common-first-error both shown inline.
- Any "contact support" instruction in the doc body is itself a finding — it means self-service
  failed at that point.
- Examples must be multi-language (cURL + at least 2 SDKs) and include error handling, not toy
  calls.
- Structure test: can a reader reach a working call before the full reference? Flag quick-starts
  that require reading 10+ pages first, or common tasks buried under "advanced."
- Friction-point table: rate each by severity × frequency × has-documented-workaround; anything
  High/Often/No is a must-fix.
- Production-readiness checklist must cover all four of: security, reliability/retry,
  monitoring/alerting, performance (caching, pagination, batch endpoints).
- Score: overall Excellent/Good/Fair/Poor + Self-Service Score X/10 + measured
  Time-to-Hello-World in minutes.

## Implementation Readiness

Audience: the engineer about to build this, not PM or external dev.

- Acceptance criteria must be testable and phrased with must/can/shows/returns — a goal like
  "system should be user-friendly" is an automatic fail.
- Every technical decision is either made or logged as an explicit open question: question,
  what it blocks, decision owner (PM/Design/Eng), decision-by date. An undocumented default
  choice ("store it in the database") fails even if no one flagged it as unclear.
- Data model needs a full constraint table per field: type, required, length/range/regex,
  default, FK cardinality. Enums must be fully enumerated — no "etc."
- State machines must state which transitions are valid and which are explicitly invalid, not
  leave it implied by the happy path.
- Test strategy must map 1:1 to acceptance criteria (every AC → at least one test scenario),
  plus dedicated concurrency/race-condition and edge-case tests.
- Score: READY TO IMPLEMENT / NEEDS CLARIFICATION / MAJOR REVISION NEEDED, plus per-section
  X/10. Blockers tagged Critical (stops work) / High (workaround exists but will resurface) /
  Medium (clarify, not blocking).

## Technical Accuracy

Audience: internal engineers evaluating spec correctness and feasibility of an engineering
spec (not an external API reference — that's a DX/Completeness concern, above).

- User story = As a/I want/So that, with every acceptance criterion independently testable.
- Data model: explicit types + constraints + indexes on any field used in a WHERE/JOIN, plus a
  state-transition diagram whenever a status/enum field exists.
- Functional requirements numbered (FR-N), each written as preconditions → numbered
  step-by-step system behavior → validation → error handling → perf target — never a one-line
  goal statement.
- Architecture section must give each component's interface as a callable signature (e.g.
  `resetPassword(email) → ResetToken | RateLimitError`), mark every cross-component call
  sync or async, state transaction boundaries, and define retry/circuit-breaker/fallback
  behavior for every external dependency.
- Business rules must be numeric and enforceable ("max 3/hour, enforced via count query +
  row lock"), never fuzzy ("a reasonable number of attempts").
- NFRs need real numbers: p50/p95/p99 latency, concurrent-user targets, named compliance
  regimes (GDPR/SOC2) where relevant — "should be fast and secure" is an automatic fail.
- Score: /100 overall + /10 per subsection (stories, data model, requirements, architecture,
  business logic, NFRs, testing).

## Output

Report per lens run:
- **Score** in that lens's native scale (see above) plus its verdict word.
- **Issues**, grouped Critical (blocks integration/implementation) / High (causes confusion or
  support burden) / Medium (polish) — never averaged across lenses, they measure different
  things. Each issue: location (quote the spec's own heading/field name, not a paraphrase),
  current text, problem, suggested fix.
- **Aggregated run** (`/spec-review` with no flag): one findings list per lens under its own
  heading, then a single closing line listing all five verdict words side by side — do not
  collapse them into one number.
