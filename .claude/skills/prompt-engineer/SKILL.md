---
name: prompt-engineer
description: Transform research content into a production-ready prompt (Create mode), or refine an existing draft prompt (Refine mode), using a 6-part framework (role, examples, instructions, context, output format, quality checks). Use for "write a prompt for X", "improve/refine this prompt", or "turn this research into a prompt".
---

# Prompt Engineer

Two modes. A single input can carry signals for both (a research doc can define a role, give instructions, and include examples) — resolve mode in this order, stop at the first match:

1. **Explicit user intent** — "improve/refine this prompt" → Refine; "turn this into a prompt" → Create.
2. **Draft-prompt vs. research detection** — is the input already addressed to an agent in second person / imperative voice (a draft prompt) → **Refine**; is it findings/evidence about a topic, written for a human reader (research) → **Create**.
3. **Still ambiguous** (e.g. a research doc that also reads like instructions) → ask: "Draft prompt to refine, or research to turn into a prompt?" Do not guess when both signals are present and intent wasn't stated.

## Refine mode

1. **Audit** — score 1-5 on: Role Clarity, Objectives, Instructions, Examples, Context, Output Format, Quality Checks. Present as a table with the biggest 2-3 gaps. Wait for the user before rewriting.
2. **Refine** using the 6-part framework below.
3. **Determine output type**: reusable skill (frontmatter, `{{ placeholders }}`, generic) vs. one-time project brief (all context embedded, no placeholders, ready to execute).

## Create mode

1. Read the research; extract core insights, principles, examples, and anti-patterns; identify the target use case/persona.
2. Define architecture: primary role, 3-5 objectives, required inputs, output format, success criteria.
3. Draft using the 6-part framework.
4. Apply best practices: specificity over vagueness, concrete examples pulled from the research, no chain-of-thought instructions, action-verb steps, contrasting examples.

## The 6-part framework

1. **Role** — specific, combine 2-3 relevant expertises ("Web3 website designer specializing in DeFi protocols", not "web designer"). Focus on what to do, not personality traits.
2. **Examples** — GOOD vs. BAD pairs, domain-specific, with a 1-sentence "why" the difference matters.
3. **Instructions** — numbered steps, each starting with an action verb (Extract, Analyze, Generate, Validate), 2-3 sentences each, output-focused rather than reasoning-focused.
4. **Context placeholders** (reusable prompts only) — explicit `{{ paste X here }}` blocks.
5. **Output format** — exact markdown structure, section by section.
6. **Quality checks** — testable yes/no criteria, not vague aspirations.

## Anti-patterns to remove

| Anti-pattern | Fix |
|---|---|
| "Be helpful" / "be creative" | Delete — personality traits don't help |
| "Think step by step" | Delete — the model does this automatically |
| "Let's dive deep into" | Delete — filler preamble |
| Vague objectives ("assist the user") | Replace with specific, measurable goals |
| Walls of prose | Convert to numbered steps or tables |
| Missing examples | Add GOOD/BAD pairs |
| Implicit output format | Make explicit with markdown structure |

## Output shape

Reusable skill: frontmatter (`name`, `description`) → role → domain sections → `## Instructions` (numbered) → `## Context` (placeholders) → `## Output Format` → `## Quality Checks`.

One-time brief: `## Role` → `## Objectives` → `## Context` (embedded, no placeholders) → `## Instructions` → `## Output Format` → `## Quality Checks`.
