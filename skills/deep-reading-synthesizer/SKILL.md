---
name: deep-reading-synthesizer
description: Use when reading, summarizing, analyzing, or extracting insight from long-form prose such as essays, books, technical blogs, papers, transcripts, notes, or exported PDFs.
---

# Deep Reading Synthesizer

## Overview

Turn long-form text into source-grounded understanding. Do not summarize first: extract evidence, synthesize insights, then audit claims against the source.

## When to Use

Use for:

- Essays, books, chapters, long technical blogs, papers, transcripts, notes, and exported PDFs
- Requests to summarize, glean insight, produce reading notes, critique an argument, explain a technical article, or extract takeaways
- Source material large enough that a one-shot summary would lose structure, caveats, or evidence

Do not use for:

- Short text that can be answered directly
- Codebase analysis, unless the source is a prose document rather than source code
- PDF text extraction itself; use `pdf-extract` first when PDF text is unavailable

## Core Workflow

1. Clarify the reading goal if it changes the output:
   - overview, detailed notes, argument critique, technical understanding, study guide, decision support, implementation ideas
   - If unspecified, default to insight-oriented executive notes.
2. Preserve source structure:
   - Split large sources by semantic boundaries: headings, chapters, sections, timestamps, or natural topic changes.
   - Keep section titles, page numbers, URLs, timestamps, or other available source locations.
3. Build source cards before synthesis:
   - Section title or location
   - Core claim or thesis
   - Supporting points
   - Definitions, concepts, examples, named tools or people
   - Short important quotes with source location
   - Surprising or non-obvious insight
   - Caveats, contradictions, ambiguity, or open questions
   - Relevance to the user's goal
4. Synthesize across source cards:
   - Gist
   - Argument or concept map
   - Ranked insights
   - Practical implications
   - Tensions, weak points, or missing evidence
   - Questions worth asking next
5. Audit the answer:
   - Separate source-supported summary from interpretation.
   - Mark unsupported claims as inference.
   - Do not invent details not present in the source.
   - Cite sections, pages, timestamps, headings, or quote locations for major claims.

## Output Format

Use this structure unless the user asks for a different format:

```markdown
# Executive Summary

[5-10 sentences focused on the user's goal.]

# Argument / Concept Map

- Thesis:
- Supporting claims:
- Assumptions:
- Evidence:
- Conclusions:

# Key Insights

1. [Insight] - [why it matters] - Source: [section/page/timestamp]

# Notable Quotes

- "[short quote]" - [source location]

# Practical Implications

- [Actionable implication]

# Open Questions

- [Question]

# Confidence / Caveats

- Source-supported:
- Inferred:
- Unclear:
```

## Quality Bar

- Prefer insight, structure, and argument mapping over generic bullet summaries.
- Preserve important disagreement, nuance, and uncertainty.
- Keep quotes short and purposeful.
- If the source is too large for one pass, summarize chunks into source cards first, then merge.
- If the user asks for a brief answer, still do evidence-first reasoning internally and provide a compact synthesis.

## Prompt Template

```markdown
You are a deep-reading research assistant. Your job is to turn long-form text into source-grounded understanding.

Read the provided document according to this goal: [USER_GOAL].

First extract evidence from the source, then synthesize insights, then audit the output for unsupported claims.

Rules:
- Use only the provided source unless outside context is explicitly requested.
- Preserve section/page/chapter/timestamp references when available.
- Pull short relevant quotes before making major claims.
- Separate source-grounded summary from interpretation.
- Prefer insight, structure, and argument mapping over generic bullet summaries.
- If the document is too large, process it section by section and merge the resulting source cards.
- Mark uncertainty clearly: source-supported, inferred, or not established.
- Do not flatten disagreements, caveats, or contradictions.

Output:
1. Executive summary
2. Argument/concept map
3. Ranked key insights
4. Important quotes
5. Practical implications
6. Open questions
7. Confidence/caveats
```
