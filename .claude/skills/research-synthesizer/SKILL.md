---
name: research-synthesizer
description: Synthesizes raw output from a deep-research tool (Perplexity, Exa, or web search) into structured, citation-rich content — patterns, principles, actionable insights — for prompt engineering, PRDs, or strategy docs. Use for "synthesize this research" or "extract principles from this research".
---

# Research Synthesizer

Transform scattered research findings (especially deep-research tool output) into structured, actionable content.

## Process

1. **Assess**: identify the research question, note source count/diversity/authority, spot gaps or bias.
2. **Extract patterns**: recurring themes, consensus points, contrarian views, how thinking evolved, real-world examples.
3. **Formulate principles**: one-sentence claim, supporting evidence with citation, a concrete example, exceptions/edge cases, links to related principles.
4. **Structure**: hierarchical headings, bullets for takeaways, numbered lists for sequences, tables for comparisons.

## Output structure

```markdown
# [Research Topic]

## Executive Summary
[2-3 paragraphs; core insights with citations]

## Detailed Findings
### [Theme]
**Key Principles:**
1. **[Principle]**: [description] [citation]
   - Example: ...
   - Application: ...

## Patterns Across Sources
## Contrarian Perspectives
## Practical Applications
## Gaps and Future Research
## References
```

## Citations

Inline: "Claude performs better with concrete examples [1]"; for quotes, "As Smith notes, '...' [4]".

Reference list format: `[1] Author, "Title", Publication, Date, URL`.

Every claim needs a citation; every source needs a reference entry.

## PM-research specifics

When synthesizing PM-related research: name reusable frameworks explicitly (JTBD, PR-FAQ, OKRs, etc.); call out proven techniques with evidence; highlight anti-patterns with examples; connect tactical advice back to strategic goals; include templates when the source provides them.

## Quality checks

All major themes covered; every claim cited; content is scannable (skim → get value); insights are actionable, not just descriptive; gaps/limitations noted.

## Not a fit for

Single-source analysis (use plain summarization), creative writing, purely quantitative/data analysis.
