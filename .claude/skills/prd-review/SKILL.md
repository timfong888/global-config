---
name: prd-review
description: Reviews a PRD across five dimensions — strategy, JTBD, research, validation, writing — with 0-100 scoring per domain and iterative re-review that skips domains already scoring 85+ except writing, which always reruns. Activate for "review this PRD", "score this PRD", "run full PM review", "multi-agent PRD analysis".
---

# PRD Review

No subagents to dispatch here — work through the modes below yourself, directly against the PRD text, in one pass per round.

## Modes

Run all five (`strategy`, `jtbd`, `research`, `validation`, `writing`) on round 1. Route with `/prd-review --strategy` etc. to run a single mode ad hoc. For a full iterative review, follow the Scoring loop below.

## Scoring

Each mode scores 0-100. Passing threshold: **85** (writing may terminate at ≥80).

| Mode | Point breakdown |
|---|---|
| strategy | vision alignment 20, market positioning 20, customer targeting 20, trade-offs 20, differentiation 20 |
| jtbd | JTBD clarity 30, user story completeness 30, persona definition 20, context/motivation 20 |
| research | competitive analysis 25, market validation 25, assumption testing 25, data/evidence 25 |
| validation | technical feasibility 30, resource assessment 25, timeline realism 20, risk identification 25 |
| writing | clarity/scannability 25, active voice/directness 20, no jargon/AI-speak 20, logical flow 20, professional tone 15 |

**Iteration rule (house convention — keep these numbers):**
- Round 1: run all 5 modes, score each 0-100.
- Round N: run only modes scoring <85 last round, **plus writing every time regardless of score**.
- Stop when: all scores ≥85 (writing ≥80 is acceptable) OR round 5 reached (max rounds) OR no score improved vs. the previous round (plateau).
- On stop, run one final pass of all 5 modes as a coherence check — isolated fixes in later rounds can regress earlier-passed domains.

Report a score table (Mode | R1 | R2 | … | Final) and the top 2-3 priorities pulled from the lowest-scoring domains. Before/after rewrites for writing issues; specific gaps (not a template) for the others.

## Strategy

Ask: why now, why us, why this problem, why these customers. Check:
- Vision alignment traceable to stated company goals, not just plausible.
- Differentiation stated as specific unique advantages, not generic claims.
- Customer targeting: primary segment named; willingness-to-pay and switching cost addressed.
- Trade-offs explicit: what we are NOT doing, and the opportunity cost.
- Timing: what must be true for this to succeed, named and testable — not asserted.

## JTBD

Distinguish JTBD (strategic "why," persona-agnostic) from user stories (tactical "what," persona-specific):
- JTBD format: "When [situation/trigger], I want to [motivation], so I can [outcome]."
- User story format: "As a [role], I want to [action], so that [benefit]."

Every JTBD should map to at least one user story. Flag JTBDs missing a concrete trigger or outcome ("Users want better storage" is not a JTBD — no situation, vague motivation, no outcome). Draft up to 3 clarifying questions about unclear user context/motivation/outcome, and 2-3 research queries to validate them.

## Research

Scan for unsupported claims ("users want X," "market is growing," pricing claims) lacking a citation. Check competitive coverage: top 3-5 direct competitors named with strengths/weaknesses and a differentiation response — not just a competitor list. For each gap: state priority (high/medium/low) and the specific query needed to close it. If research tools are available, use them to close gaps rather than only flagging them.

## Validation

Review from 5 stakeholder lenses and mark each Yes/Unclear/No with what's missing:
- Engineering — buildable? constraints and dependencies stated?
- Design — UX flows and interaction patterns defined?
- Sales/GTM — positioning and pricing rationale clear?
- Operations/Support — support burden and scale implications addressed?
- Leadership — business case and risk stated?

Catalog risks by category (technical/market/execution/external) with likelihood × impact and a mitigation. Verify every goal has an owned, measurable metric with a target, and check for stated kill criteria — flag if absent.

## Writing

Enforce (Amazon + Strunk & White style):
- Inverted pyramid: decision/conclusion first. One idea per paragraph, 2-3 sentences.
- Active voice; front-load cause before effect ("Because X, we're doing Y," not the reverse).
- Data over adjectives: "25% of users," not "many users."
- Vary sentence length deliberately — three consecutive sentences of the same length reads as robotic; mix short/medium/long for rhythm.
- Bullets sparingly, for MECE lists only. Bold sparingly, for short high-impact statements. Tables for structured trade-offs. No emoji.
- Approval tests: could an engineer build from this? Would a stakeholder get the trade-off? Is every success criterion measurable? Does it survive being read aloud? Does it sound like a press release (fail) or a colleague explaining over coffee (pass)?

**Banned AI/corporate phrasing** — flag and rewrite, don't just note:

| Instead of | Use |
|---|---|
| leverage, utilize | use |
| dive deep into | examine |
| it's worth noting that | delete — just state the fact |
| in today's fast-paced world | delete the preamble |
| cutting-edge, innovative | show the specific capability |
| synergies, paradigm, revolutionize, touchpoints | name the specific thing |
| upon analysis | we found |
| several deficiencies emerged | here's what went wrong |
| paragraph-opening Additionally/Furthermore/Moreover | stronger transition, or delete |
| many users / significant improvement / better experience | specific percentage or metric |

If asked to "review writing only, minimize changes": fix only jargon/AI-patterns, no structural edits.
