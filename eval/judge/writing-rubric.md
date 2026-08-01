# Blind pairwise writing review

You are comparing two written responses, A and B, to the same task. Judge the final prose, not any presumed process. You do not know which system produced either response and must not guess. Evaluate only the material supplied below.

## Task

{{TASK_PROMPT}}

## Source material

{{SOURCE_INPUT}}

## Response A

{{RESPONSE_A}}

## Response B

{{RESPONSE_B}}

## What this review measures

This is a review of writing style and readability: which response reads more like a skilled person wrote it for the stated situation. Content accuracy has exactly one role here, described under dimension 5 — it is a floor, not a scoring axis. Do not let small wording-level differences in how faithfully each response mirrors the source decide anything.

## Review method

For each dimension, reason carefully from the task and source. Cite one short, specific phrase from each response as evidence; when a response omits required material, identify the omission instead of inventing a quotation. Then choose `A`, `B`, or `Tie`. Use `Tie` sparingly on dimensions 1–4, only when neither response has a meaningful advantage. On dimension 5, `Tie` is the expected verdict unless there is a material violation.

Ignore response length except when padding, repetition, or an instruction-specific length limit affects quality. Do not reward Markdown, headings, bullets, or visual polish for their own sake. Do not prefer a response because it sounds more formal.

1. **Naturalness / absence of AI tells.** Prefer prose that sounds like a person communicating for the stated situation. Penalize metacommentary, empty signposting, forced rule-of-three constructions, stacked hedges, throat-clearing openings, ritual summaries, inflated transitions, and repetitive sentence shapes. Do not penalize necessary qualifications or useful structure.

2. **Answer-first structure.** Prefer the response that leads with the substantive answer, decision, recommendation, or requested content before background. For creative work, interpret this as entering the scene or action promptly rather than announcing themes or setup. Do not reward bluntness that makes the response confusing.

3. **Voice and calibration of tone.** Prefer writing with a confident, proportionate voice. Penalize significance inflation ("pivotal", "a testament to", unsupported praise), manufactured punchiness, hollow certainty, and hedging deployed as filler. Judge each response's tone against its own content and the task's register — this dimension is about how claims are voiced, not whether every nuance matches the source exactly.

4. **Clarity and concision.** Prefer plain, precise sentences with useful flow. Penalize padding, duplication, vague abstractions, unnecessary jargon, confusing organization, and detail that does not serve the task. Concision must not come from dropping required information.

5. **Faithfulness floor.** This is a disqualifier, not a quality ranking. Award a winner here only when the other response commits a material violation: dropping a required fact, inventing a fact or commitment not in the source, contradicting the source, or breaking an explicit task constraint (audience, format, word limit, prohibited content). Wording-level shifts in emphasis or hedging strength ("could" rendered as "likely", a softened qualifier, a compressed detail) are NOT material — note them in the reason if you wish, but verdict `Tie`. If both responses commit material violations, the less severe one wins; if neither does, `Tie`.

## Overall verdict

Give the overall verdict last. It is decided by the style dimensions — naturalness, answer-first structure, voice, and clarity — with naturalness and clarity weighted most heavily. Dimension 5 overrides this only when it identified a material violation; in that case the violating response cannot win overall. State the deciding dimension or dimensions in one sentence.

Return only JSON matching this schema exactly:

```json
{
  "dims": {
    "naturalness": {
      "winner": "A|B|Tie",
      "evidence_a": "short quotation or concrete omission",
      "evidence_b": "short quotation or concrete omission",
      "reason": "comparison grounded in the evidence"
    },
    "answer_first": {
      "winner": "A|B|Tie",
      "evidence_a": "short quotation or concrete omission",
      "evidence_b": "short quotation or concrete omission",
      "reason": "comparison grounded in the evidence"
    },
    "calibration": {
      "winner": "A|B|Tie",
      "evidence_a": "short quotation or concrete omission",
      "evidence_b": "short quotation or concrete omission",
      "reason": "comparison grounded in the evidence"
    },
    "clarity_concision": {
      "winner": "A|B|Tie",
      "evidence_a": "short quotation or concrete omission",
      "evidence_b": "short quotation or concrete omission",
      "reason": "comparison grounded in the evidence"
    },
    "faithfulness": {
      "winner": "A|B|Tie",
      "evidence_a": "short quotation or concrete omission",
      "evidence_b": "short quotation or concrete omission",
      "reason": "comparison grounded in the evidence"
    }
  },
  "overall": {
    "winner": "A|B|Tie",
    "reason": "one sentence naming the deciding dimension or dimensions"
  }
}
```
