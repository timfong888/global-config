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

Produce a draft in that section order (Problem Statement → Goals → User Needs → Proposed Solution → Constraints → Open Questions → Assumptions → Contradictions), and close with 3-5 targeted clarifying questions — e.g. "Who is the primary user?", "What's the one metric that defines success?", "What's explicitly out of v1?".

Before appending the raw input as a collapsed `<details>` block at the end, scan it for anything sensitive — PII, credentials, API keys, confidential business detail. A collapsed block still commits the raw text to the repo (see "Both modes" below); it doesn't protect it. Flag anything sensitive to the user and confirm whether to keep it verbatim, redact the flagged parts, or drop the `<details>` block entirely — don't persist raw secrets or personal data by default.

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

Either a dated intake file or raw ideas pasted inline by the user. Locate the most recent intake file without relying on `ls -t <glob>` — it exits non-zero when nothing matches and word-splits filenames containing spaces. Guard the empty case explicitly too: `xargs -0 ls -t` with no input still runs `ls -t` on the current directory and returns a false match instead of nothing:

```bash
count=$(find context/projects -path "*/prds/intake/*-intake-*.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$count" -eq 0 ]; then
  echo "no intake file found"
else
  find context/projects -path "*/prds/intake/*-intake-*.md" -print0 2>/dev/null \
    | xargs -0 ls -t 2>/dev/null | head -5
fi
```

No result (`count` is 0) → no intake file exists yet. Say so and continue with whatever ideas the user pastes inline — don't stop the weave.

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

Committing keeps a real baseline for later `git diff` checks (this skill's step 2, and prd-review) to
learn the user's edit patterns from. Do it last, and **ask first**: show the user which PRD file(s)
this run touched and the proposed message, and wait for explicit approval — don't commit as a matter
of course.

Once approved, commit only the PRD file(s) this run modified, by path. A plain `git add -A`/`git
commit` sweeps in whatever else was already staged or dirty in the working tree:

```bash
git commit --only -- "$PRD_FILE" -m "docs: <what was added or integrated>"
```

`--only` commits the named paths from the working tree and ignores anything else in the index. Use a
`feat:` prefix instead when the change introduces new scope rather than documenting existing scope.
