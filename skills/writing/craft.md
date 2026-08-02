# Craft: the positive model

Distilled from two battle-tested project guides (a research paper's style guide and a finance publication's) — the portable principles, with project voices removed. The underlying idea is Pinker's "classic style" (*The Sense of Style*): prose is a clear window — the writer has noticed something and points the reader's gaze at it.

## Show the thing

Write to show the reader the world, not to describe your own writing. Never narrate a document's own structure, announce what a part contains, or remark on how well it satisfies a requirement. If the structure is good, it is visible. This applies to working documents (outlines, notes, briefs) too, not just polished prose. Don't smuggle in the discussion that produced a decision ("not a straw man," "decided, not deferred") — state the decision, drop the contrast with the rejected alternative.

## Beware the curse of knowledge

The single biggest cause of unclear writing: once you understand something, you can't remember what not-understanding was like, so you omit the step, example, or plain restatement the reader needs. Fix: write for a specific intelligent reader outside the subfield. Define a loaded term the first time it appears. Say it once in the technical register, once plainly — "in other words" is a teacher's move, not a hedger's.

## Hunt nominalizations

A nominalization freezes a verb into a noun: *evaluate* → *evaluation*, *impose* → *imposition*. Stack them and the sentence goes static — the real action trapped in an abstract noun while a limp verb (*is*, *performs*, *provides*) holds the grammar. The buried verb is usually the actual sentence: "the system performs a construction of a model of the user" → "the system builds a model of the user." Prefer a concrete subject doing a concrete thing.

## Plain and precise, not punchy and not vague

The billboard test: a clause that would work as a tagline is usually wrong. Tagline antithesis ("Recall is cheap; synthesis is the open question") reads like ad copy — spell out both halves in plain clauses. Adjectives and labels state, they don't sell: "a demanding baseline" → "a baseline"; "the loudest conviction call" → "the strongest theme." Don't coin label-like noun phrases ("the experiment platform", "the stored thing") — use plain description or the term the source already uses.

## Read, not decoded

The test for any line is whether it's understood on first read. Compressed notation fails it: "condition × persona × scenario" → "run every design against every persona and every scenario." Telegraphic noun strings ("config capture for repeatability") fail it. Jargon gets defined at first use or replaced with a plain word. When two phrasings are equally accurate, the shorter one wins.

## Concede, then commit

Open with the honest limit, then commit to the claim at the strength the evidence sets — the concession buys the claim its credibility. Committing means dropping filler qualifiers, not upgrading the claim: "could" stays "could," a contributing factor doesn't become the cause. One plain "this isn't known" beats stacked qualifiers. What's banned: hedging toward multiple possible futures, prose written to survive a pending answer, qualifiers layered on the writer's own method. Genuinely open questions go in a to-do list, not woven into prose as caveats.

## Voice anchors

Anchor on one or two writers who explain hard material in the project's domain plainly, and borrow their *principles* — fewest words, concrete over abstract, no throat-clearing, honest unknowns — never their tics. (The source guides used Melanie Mitchell for research prose; Benedict Evans and Morgan Housel for finance.) Pick anchors per project in `WRITING.md`; see [writing-md-bootstrap.md](writing-md-bootstrap.md).

## Process

1. Draft clean with these patterns from the start — don't draft dirty and clean later.
2. Audit: "What makes this read as AI-generated?" — fix what surfaces ([humanizer.md](humanizer.md)).
3. When editing existing prose, make surgical, precision-preserving edits. Fix the phrase, not the paragraph.
4. When unsure whether a sentence works, read it aloud.
