# Humanizer: remove AI writing patterns

Editor pass on text that already exists. The always-on version of the same rules is the **Human Writer** output style (`output-styles/human-writer.md`); the positive model, what good prose does, is [craft.md](craft.md). Load this file for a rewrite or an audit.

**Structure beats vocabulary.** The durable AI tells are structural: copula avoidance, participial tack-ons, rule of three, significance inflation, negative parallelism, false agency, manufactured punchiness, metacommentary. Word lists ("delve," "tapestry") date with each model generation, so treat them as illustrative. A draft with every banned word removed still reads as AI if the sentence skeletons are untouched. Fix the structure first.

## Task

1. **Identify** the structural tells below. Load [patterns.md](patterns.md) only when the piece is long, the text is for publication, or the first pass finds tells outside the eight.
2. **Rewrite** each problem surgically. Fix the phrase, not the paragraph; replacement patterns come from [craft.md](craft.md).
3. **Preserve meaning and requirements.** Keep whatever the brief, spec, or format explicitly requires, even when it resembles a pattern here. Requirements are content, not style.
4. **Preserve modality.** A deleted qualifier must not change what the sentence asserts. "Could shift" is not "likely moves"; an enabling condition is not the cause. Blind-eval evidence: styled rewrites lost calibration precisely by firming up claims their sources stated more carefully.
5. **Audit, targeted.** Ask: "What in this draft is still structural AI writing?" Name only tells actually present, fix those, and leave clean prose alone. A generic "make this better" pass on clean text invents problems and reintroduces tells.

## Voice

Match the voice the text already has, or the one the project's `WRITING.md` names. Do not import one. If the user supplies a writing sample, read it first and note sentence length, word level, paragraph openings, punctuation habits, and transitions, then replace tells with patterns from the sample rather than with defaults. Without a sample or a guide, the register-neutral rules in craft.md are the whole voice: plain, concrete, honest about what isn't known.

## The eight structural tells

### 1. Copula avoidance

"Serves as," "stands as," "boasts," "features" in place of is/are/has.

> **Before:** Gallery 825 serves as LAAA's exhibition space and boasts over 3,000 square feet.
> **After:** Gallery 825 is LAAA's exhibition space. It has four rooms totaling 3,000 square feet.

### 2. Participial tack-ons

A present-participle phrase hung on the end of a sentence to add fake depth: highlighting, underscoring, reflecting, ensuring, fostering, showcasing.

> **Before:** The temple uses blue, green, and gold, symbolizing the bluebonnets and the Gulf, reflecting the community's connection to the land.
> **After:** The temple uses blue, green, and gold. The architect said the colors reference local bluebonnets and the Gulf coast.

### 3. Rule of three

Ideas forced into triples to seem comprehensive.

> **Before:** Attendees can expect innovation, inspiration, and industry insights.
> **After:** The event includes talks and panels, with time for informal networking between sessions.

### 4. Significance inflation

Statements about how a thing marks, represents, or contributes to something broader: pivotal moment, testament to, vital role, evolving landscape, setting the stage.

> **Before:** The institute was established in 1989, marking a pivotal moment in the evolution of regional statistics.
> **After:** The institute was established in 1989 to publish regional statistics independently of the national office.

### 5. Negative parallelism and tailing negations

"Not just X, it's Y," and clipped fragments like "no guessing" tacked onto a sentence instead of written as a clause.

> **Before:** It's not merely a song, it's a statement. The options come from the selected item, no guessing.
> **After:** The song is a statement. The options come from the selected item, so the user never has to guess.

### 6. False agency

An abstraction performs a human verb while the actual actor disappears: the decision emerged, the data tells us, the culture shifted. Grammatically active, so it slips past a passive check. Name the actor; "you" or "we" usually fits.

> **Before:** The decision emerged after the data told a clear story, and the culture shifted toward smaller releases.
> **After:** The platform team read the incident reports, capped deploy size, and got the other teams shipping smaller releases.

### 7. Manufactured punchiness

Staccato fragments performing profundity, emphasis crutches ("Full stop," "Let that sink in"), setup/reveal openers ("Here's the thing:"), tagline antithesis, colon-spliced "claim: elaboration" chains. Models learned that punchy reads as human and overproduce it. Short sentences are fine; fragments deployed for drama are the tell.

> **Before:** Here's the thing: most migrations fail. Not because of the technology. Because of the people.
> **After:** Most migrations fail because teams underestimate the retraining, not the technology.

### 8. Metacommentary

Announcing the move instead of making it ("Let's dive in," "The takeaway is," "It's worth noting"), narrating the document's own structure ("This section covers"), remarking on how well something meets a requirement, or smuggling in the debate behind a decision ("not a straw man"). State the thing. Functional annotations that carry information the reader needs (a legend, a cross-reference) stay.

> **Before:** Let's dive into how caching works. The key insight is that Next.js caches at multiple layers.
> **After:** Next.js caches data at multiple layers: request memoization, the data cache, and the router cache.

## Output

1. Draft rewrite
2. Targeted audit: the structural tells still present, as brief bullets (omit if none)
3. Final rewrite
4. Summary of changes, only if it helps the reader

When generating prose rather than editing it, draft clean from the start with these patterns in mind.

## Example

**Before:**

> Great question! Here is an essay on this topic. I hope this helps!
>
> AI-assisted coding serves as an enduring testament to the transformative potential of large language models, marking a pivotal moment in the evolution of software development. It's not just about autocomplete; it's about unlocking creativity at scale. The tool serves as a catalyst. The assistant functions as a partner. The system stands as a foundation for innovation.
>
> Industry observers have noted that adoption has accelerated from hobbyist experiments to enterprise-wide rollouts. Additionally, the ability to generate documentation, tests, and refactors showcases how AI can contribute to better outcomes, highlighting the intricate interplay between automation and human judgment.
>
> In conclusion, the future looks bright. Let me know if you'd like me to expand on any section!

**Draft rewrite:**

> AI coding assistants speed up some tasks. A 2024 Google study found developers using an assistant completed simple functions 55% faster than a control group, with no improvement on debugging or architectural decisions.
>
> The tools are good at boilerplate: config files, test scaffolding, repetitive refactors. They are bad at knowing when they are wrong. I have accepted suggestions that compiled, passed lint, and still did the wrong thing because I stopped paying attention.
>
> The productivity claims are hard to verify. GitHub says users accept 30% of suggestions, but acceptance is not correctness, and correctness is not value. The 2024 Uplevel study found no significant difference in pull-request throughput between teams with and without assistants.
>
> None of this means the tools are useless. It means they are tools. They do not replace judgment, and they do not eliminate the need for tests.

**Targeted audit:**

- Rule of three in the boilerplate list and again in "compiled, passed lint, and still did the wrong thing."
- Negative parallelism in the last paragraph ("not X, it means Y"; "do not replace… do not eliminate").
- Every paragraph is the same length, which reads assembled.

**Final rewrite:**

> AI coding assistants speed up some tasks. A 2024 Google study found developers using an assistant completed simple functions 55% faster than a control group, with no improvement on debugging or architecture.
>
> The tools handle boilerplate well and are bad at knowing when they are wrong. I have accepted suggestions that compiled and still did the wrong thing because I stopped reading.
>
> The productivity claims are hard to verify. GitHub says users accept 30% of suggestions, but acceptance is not correctness. The 2024 Uplevel study found no significant difference in pull-request throughput between teams with and without assistants. The tools pay off on code that tests can check, because a wrong suggestion gets caught there.

**Changes:** removed chatbot artifacts, significance inflation, copula avoidance, negative parallelism, vague attribution, participial tack-ons, the generic conclusion; replaced the closing triple with one sentence that says when the tools pay off.

## Reference

The pattern catalogue derives from [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
