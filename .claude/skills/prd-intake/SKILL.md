---
name: prd-intake
description: Turns raw PM input into PRD content. Mode "new" builds a structured PRD draft from a transcript, notes, or brainstorm. Mode "weave" integrates new strategic ideas into an EXISTING PRD with prerequisite and logical-flow validation. Activate for "create PRD from transcript", "structure this brainstorm", "weave intake into PRD".
---

# PRD Intake

## Modes

- `new` — raw transcript/notes/brainstorm → structured initial PRD draft (no existing PRD yet).
- `weave` — integrate new strategic ideas into an EXISTING PRD, preserving logical flow and prerequisites.

Both modes: apply prd-review's writing-mode rules (banned jargon list, structure) to any text you produce.

## Mode: new

### Extract

From the raw input, pull out (preserve original language where it's already clear):

- **Problem statement** — pain point, broken workflow, why it's worth solving, why now.
- **Goals & success metrics** — desired outcomes, any stated targets.
- **User needs (initial JTBD)** — who, plus "When [situation], I want to [motivation], so I can [outcome]."
- **Proposed solution** — features/approach discussed, explicit out-of-scope.
- **Constraints** — technical, business (timeline/budget/resources), compliance.
- **Open questions** — explicit questions asked, plus implied gaps.
- **Assumptions to validate** — beliefs stated without evidence; note risk if wrong and how to validate.
- **Contradictions** — conflicting statements that need resolution.

Tag each item inline: `[NEEDS CLARIFICATION]`, `[ASSUMPTION]`, `[CONTRADICTION]`, `[STRONG]` (well-articulated, no flag needed).

### Structure

Produce a draft in that section order (Problem Statement → Goals → User Needs → Proposed Solution → Constraints → Open Questions → Assumptions → Contradictions), preserve the raw input in a collapsed `<details>` block at the end, and close with 3-5 targeted clarifying questions — e.g. "Who is the primary user?", "What's the one metric that defines success?", "What's explicitly out of v1?".

Save to `prds/[product-name]-initial-draft-[date].md` unless told otherwise. Then offer to run `prd-review` for full multi-dimension scoring, or continue refining a specific section.

## Mode: weave

### 1. Identify the target PRD

```bash
find . -name "*-mrd-*.md" -o -name "*-prd-*.md" | sort
```

Confirm the version with the user before editing — never assume the latest file found is the right one. (`mrd` = market requirements doc; shares the same versioning convention as `prd`.)

### 2. Check recent edits first

Run `git diff path/to/prd-file.md` before touching it. Adopt whatever terminology, sentence rhythm, and formatting the user's last edits show — don't revert intentional changes you weren't asked to touch.

### 3. Gather the intake

Either a dated intake file or raw ideas pasted inline by the user. Locate the most recent intake file without relying on `ls -t <glob>` — it exits non-zero when nothing matches and word-splits filenames containing spaces:

```bash
find context/projects -path "*/prds/intake/*-intake-*.md" -print0 2>/dev/null \
  | xargs -0 ls -t 2>/dev/null | head -5
```

No result → no intake file exists yet. Say so and continue with whatever ideas the user pastes inline — don't stop the weave.

### 4. Reason through placement — this is the actual job

For each intake idea, before writing anything:

- **Does it already exist** in the PRD, or is it new content? What heading level does it belong at (H2/H3/H4)?
- **Prerequisites** — what context or definitions must exist before this idea makes sense? Does it reference an undefined term?
- **Connection** — does it extend, contradict, or sit disconnected from the surrounding sections? What bridging sentence links old to new?

If prerequisites are missing, say so and ask rather than inserting the idea anyway — e.g. "This references 'Filecoin Enterprise,' which isn't defined yet. Is that Akave? I'll define it before adding this claim." Never insert an idea that would read as disconnected to someone unfamiliar with the discussion that produced it.

### 5. Execute

Add prerequisite context first, then the idea, with explicit bridging language. Keep edits concise: short sentences, premise before conclusion, terms defined before their first use.

### 6. Validate

Re-read the surrounding section. Does the new content read as though it belongs, to someone who wasn't in the room? Are new terms defined before use?

### 7. Report

Summarize which sections were touched, what prerequisite context was added, and why — not just a diff.

## Both modes

Commit PRD file changes with a `feat:`/`docs:` prefix describing what was added or integrated, so later `git diff` checks (this skill's step 2, and prd-review) have a real baseline to learn the user's edit patterns from.
