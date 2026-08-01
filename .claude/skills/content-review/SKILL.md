---
name: content-review
description: Review launch/announcement content for structure, customer focus, and positioning alignment (mode review); or derive positioning, JTBD, content plans, and PAS/AIDA/BAB copy from a product description as structured JSON (mode position). Use for "review this announcement", "check positioning alignment", "build JTBD", "write homepage copy".
---

# Content Review & Positioning

## Modes

- `review` — audit a blog post/announcement for structure, the AWS five customer questions, positioning alignment, and best practices; flag items needing PM approval.
- `position` — derive positioning, JTBD, content plans, and copy assets from a product description, returned as structured JSON.

---

## Mode: review

Requires the product positioning doc (persona, JTBD, pillars, differentiation) as input — ask for it if not supplied.

### 1. Structural checklist

Headline states product + benefit; opening states what/why/who; value prop stated early; concrete use cases; visuals or placeholders; one clear CTA (not competing CTAs); docs/support links. Writing: ~5-7 word sentences, 3-7 sentence paragraphs, active voice, no adverbs, no undefined jargon.

### 2. AWS five customer questions

Mark each Addressed / Partial / Missing with a supporting quote:

1. Who is the customer? — flag generic "developers/users"
2. What's the problem/opportunity? — flag jumping straight to the solution
3. What's the #1 benefit? — must be a benefit (not a feature), in the headline and reinforced throughout
4. How do we know customers want this? — needs a quote, testimonial, or research reference
5. What does the customer experience look like? — needs a concrete journey/before-after, not abstraction

### 3. Positioning alignment

Cross-reference against the positioning doc: target persona match, JTBD mentioned in the first 3 paragraphs, all core pillars represented (none overweighted), feature accuracy (flag overpromising unbuilt capability), competitive differentiation implied without competitor-bashing. Mark each ✅ Aligned / ⚠️ Partial / ❌ Misaligned with a quote and a fix.

### 4. Best-practice + pitfall check

Benefit-first headline; Problem → Solution → Value flow; use-cases shown before feature lists; benefit:feature ratio ≥2:1; outcomes quantified where possible; customer quote/testimonial; before/after comparison; <5-step next action; feedback invitation. Pitfalls: jargon without definition, "revolutionary"/"best ever" superlatives, missing or multiple competing CTAs, generic messaging that could fit any product, announcing before GA.

### 5. PM-approval risk flags

- **High** (must review before publishing): roadmap commitments, pricing/packaging references, technical specs/performance claims, partner mentions, competitive comparisons, GA/timeline promises.
- **Medium** (should review): use-case validity, persona targeting, feature prioritization, pillar emphasis balance.
- **Clarification needed**: ambiguous or potentially misleading statements, claims lacking supporting evidence, terminology drift from established vocabulary.

### Output

`# Review: [title]` → Executive Summary (2-3 sentences) → per-section verdict (✅ Pass / ⚠️ Needs work / ❌ Major issues) with quotes and fixes → AWS-5 table → positioning-alignment findings → risk-flag list (🔴 High / 🟡 Medium / 🔵 Clarification) → Overall: publish status (Ready / Minor revisions / Major revisions) + ranked priority actions.

---

## Mode: position

Take a rough product description and produce positioning, JTBD, a content plan, or copy. Return structured JSON when the request says "structured JSON"/"objects"/"schema"; otherwise add brief prose around the JSON.

### Core concepts

| Concept | Definition |
|---|---|
| Audience | Who this is for (segment, role, context) |
| JTBD | The job they're hiring the product to do — functional + emotional |
| Outcome | Measurable change they care about (time, money, risk, status) |
| Obstacle | Pains/blockers/fears stopping them |
| Promise | What you commit to deliver (benefit + proof) |
| Mechanism | How your approach works differently/better |
| Offer | Concrete package, risk reversal, CTA |

### Frameworks — always state which one you used

- **PAS** — Problem, Agitate, Solution
- **AIDA** — Attention, Interest, Desire, Action
- **BAB** — Before, After, Bridge

### Output schemas

The shapes below are schema notation, not literal JSON — unquoted keys, `field[]` for an array, `a|b|c` for "one of these." When the request calls for structured JSON, emit real JSON: quoted keys, one concrete value per field. Example, content plan:

```json
{
  "content_items": [
    {
      "title": "3 fiat onramps now support FIL",
      "format": "blog",
      "funnel_stage": "consideration",
      "target_jtbd": "convert fiat to FIL without leaving the onramp",
      "key_message": "One flow, no separate wallet step"
    }
  ]
}
```

Positioning (Dunford-style): `{product_name, category, target_audience, key_differentiator, primary_benefit, proof_points[], competitive_alternatives[]}`

JTBD list: `{jtbd_items: [{situation, job, outcome}]}`

Content plan: `{content_items: [{title, format: blog|video|case_study|landing_page, funnel_stage: awareness|consideration|decision, target_jtbd, key_message}]}`

Copy asset: `{asset_type: homepage_hero|email|ad|landing_page, framework: PAS|AIDA|BAB, headline, subheadline, body_sections[], cta}`

Site structure: `{pages: [{path, purpose, key_sections[], target_jtbd}]}`

### Workflow

1. Build positioning — audience, differentiator, benefit, proof points.
2. Derive 2-4 JTBD statements before generating any content asset.
3. Map content items to JTBDs and funnel stages.
4. Draft copy in the stated framework; self-edit against Clear / Concise / Compelling / Credible.
