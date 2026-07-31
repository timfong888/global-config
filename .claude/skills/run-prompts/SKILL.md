---
name: run-prompts
description: Execute prompts in markdown. Inline mode runs "> prompt:" blockquotes embedded in a document, in place. File mode audits, refines (with approval), executes, and routes the output of a whole markdown prompt file. Use for "run this prompt", "execute this prompt", "process embedded prompts".
---

# Run Prompts

## Modes
- `inline <file>` — find and execute `> prompt:` blockquotes embedded in a document, in place.
- `file <path>` — audit, refine, execute, and route the output of a whole markdown file written as a prompt.

Both modes: git-backup the file first, and use a deep-research tool (Perplexity, Exa, or web search) for research-flavored prompts if one is available — otherwise execute directly.

---

## Mode: inline

1. **Backup**: `git add $FILE && git commit -m "Backup: $(basename $FILE) before prompt processing" --allow-empty`. Report the commit hash; continue if nothing to commit.
2. **Style**: `git diff $FILE` — note the user's recent terminology, tone, and sentence length, and match it.
3. **Scan**: `grep -in '^> prompt:' $FILE` (matches `> prompt:` or `> Prompt:`, case-insensitive). Report "Found N embedded prompts".
4. **Process each blockquote, top to bottom**:
   - Read the surrounding section for context.
   - Classify: "research"/"look up" → research (deep-research tool); "verify"/"check"/"make sure" → validation (search the doc for fulfillment); "improve"/"flow"/"repetitive"/"redundant" → flow/writing fix; else → generic, execute with document context.
   - Execute the instruction.
   - **Replace the blockquote entirely with the output — no audit markers, nothing of the marker left behind.**
5. **Show a unified `git diff` before applying.** Ask "Apply changes? (y/n)" — n reverts and exits.
6. **Commit**: `git add $FILE && git commit -m "docs: process embedded prompts\n\n- Processed N prompts\n- <summary>"`.
7. Multi-file input: repeat steps 1-6 per file, single summary at the end.
8. Report: "Prompts: N processed. Changes: <summary by type>."

---

## Mode: file

1. Validate the path exists; read the full contents. If it doesn't look like a prompt (no intent/instructions/goals), ask "This doesn't appear to be a prompt. Run anyway? (y/n)" before proceeding.
2. **Backup** as above.
3. **Context resolution**: if the file references other files (e.g. `[[wikilinks]]` or relative paths), resolve and read them; summarize each in 3-5 bullets held in memory for execution — do not write the summaries into the source file. Warn on any reference that can't be resolved.
4. **Audit** — score 1-5, present as a table, then wait for the user to acknowledge before continuing:

| Dimension | 5/5 looks like |
|---|---|
| Role Clarity | Specific, combines 2-3 relevant expertises |
| Objectives | Measurable, with success criteria |
| Instructions | Numbered steps, action verbs, clear sequence |
| Examples | Contrasting GOOD/BAD pairs |
| Context | Complete, references resolved |
| Output Format | Exact markdown structure specified |
| Quality Checks | Testable yes/no checks |

5. **Propose refinement** via the 6-part framework: strengthen Role, add GOOD/BAD Examples, structure Instructions with action verbs, clarify Context (resolved references + `{{ placeholders }}`), specify Output Format, add testable Quality Checks. Remove anti-patterns ("be helpful", "think step by step", vague objectives, walls of prose). Ask:
   - **approve** — apply to the source file (backup already exists)
   - **tweak** — adjust and re-propose
   - **skip** — execute as-is
6. **Execute**: scan for research keywords ("research", "find", "search", "latest", "current", "news", "compare", "what is", "how does") → route to a deep-research tool if one is available, else execute directly. Context = refined/original prompt + resolved-reference summaries.
7. **Route the output** — detect intent in order:
   1. Creation verbs ("write/create/generate/draft/produce/make") + a document noun ("blog/report/checklist/plan/guide/summary/spec") → new file in the same directory; filename derived from the ask; add frontmatter `source: "[[source filename]]"`, `created: YYYY-MM-DD`.
   2. Modification verbs ("improve/fix/rewrite/refine/update/edit/revise") + self-reference ("this/the above/this document") → edit the source file in place; append a `## Changelog` entry.
   3. Action verbs ("organize/move/create tickets/file/send/schedule/sort/categorize/migrate") → execute the actions; append a `## Execution Log` entry.
   4. Ambiguous → ask: "new file" / "in-place" / "just show me".
8. **Commit**, message including audit score, refinement status (applied/skipped), and output route.
9. Report: file, audit score, refinement status, execution route, output location.

No argument given: look for prompt-shaped files in the current directory and offer batch processing; process each through steps 1-9 and give a per-file report plus a batch summary.

---

For standalone prompt creation/refinement without execution, use `prompt-engineer`.
