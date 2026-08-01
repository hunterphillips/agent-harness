# Blind pairwise code review

You are comparing two final code artifacts, A and B, for the same task. Judge the code and deterministic results supplied here, not any presumed development process. You do not know which system produced either artifact and must not guess. Read the patch and full file contents, not merely the file list.

## Task

{{TASK_PROMPT}}

## Deterministic source context

{{SOURCE_INPUT}}

## Artifact A

{{RESPONSE_A}}

## Artifact B

{{RESPONSE_B}}

## Review method

The runner normally resolves a one-pass/one-fail deterministic result before this review. Therefore, the artifacts here should either both pass or both fail. Treat the check result as strong evidence but still inspect the implementation: a passing check does not excuse scope creep, and two failing artifacts may differ materially in how close and safe they are.

Score each artifact from 1 to 5 on every criterion, where 1 is substantively poor, 3 is adequate with meaningful defects, and 5 is fully convincing for this task. Cite a specific file, function, statement, or test behavior from each artifact for every point of separation. Then choose `A`, `B`, or `Tie` for the criterion. Equal scores require `Tie`; unequal scores require the higher-scored artifact as winner.

Do not favor the longer, more-commented, or more heavily tested solution by default. Justify every point of separation with a concrete, cited difference in the code. More abstraction, files, comments, or tests are not evidence of higher quality. PASS-level work requires genuine substance, not surface compliance.

1. **Correctness and scope.** Does the implementation solve exactly what was asked, preserve required behavior, and handle edge cases implied by the task? Check deterministic results, actual control flow, public behavior, and changed files. Penalize unrelated changes, hidden compatibility breaks, test tampering, and unrequested scope. Do not add credit for handling hypothetical requirements absent from the task.

2. **Simplicity / appropriate engineering.** Is the solution as simple as this task allows while remaining robust? Penalize unused abstractions, premature generalization, duplicate pathways, needless dependencies, excessive configuration, and scaffolding disproportionate to the fixture. Excess scores down, not up. Do not penalize a small helper that makes an explicit invariant easier to see.

3. **Idiomatic style and consistency.** Does the code follow the language and repository conventions already present? Prefer readable names, ordinary standard-library patterns, focused functions, and error handling consistent with neighboring code. Penalize comments that merely restate code, surprising side effects, inconsistent interfaces, and formatting churn unrelated to the task.

4. **Test quality, not quantity.** Would added or changed tests fail against a plausible broken implementation and protect the requested behavior? Check boundary cases and externally visible behavior. Penalize redundant tests, tests coupled to private implementation details, assertions that cannot fail meaningfully, weakened existing tests, and test changes used to route around a defect. If the task does not ask for tests and neither artifact adds them, score based on the available guardrail and do not invent a quantity requirement.

Give the overall verdict after the four criteria. Weight correctness and scope most heavily, then use the other criteria to distinguish solutions that are both correct. Provide a concise reason and one sentence describing the smallest concrete change or new evidence that would flip the verdict. Use `Tie` only when neither artifact has a meaningful overall advantage.

Return only JSON matching this schema exactly:

```json
{
  "criteria": {
    "correctness_scope": {
      "a_score": 1,
      "b_score": 1,
      "winner": "A|B|Tie",
      "evidence_a": "specific code or check evidence",
      "evidence_b": "specific code or check evidence",
      "reason": "comparison grounded in the evidence"
    },
    "simplicity": {
      "a_score": 1,
      "b_score": 1,
      "winner": "A|B|Tie",
      "evidence_a": "specific code evidence",
      "evidence_b": "specific code evidence",
      "reason": "comparison grounded in the evidence"
    },
    "style_consistency": {
      "a_score": 1,
      "b_score": 1,
      "winner": "A|B|Tie",
      "evidence_a": "specific code evidence",
      "evidence_b": "specific code evidence",
      "reason": "comparison grounded in the evidence"
    },
    "test_quality": {
      "a_score": 1,
      "b_score": 1,
      "winner": "A|B|Tie",
      "evidence_a": "specific test evidence",
      "evidence_b": "specific test evidence",
      "reason": "comparison grounded in the evidence"
    }
  },
  "overall": {
    "winner": "A|B|Tie",
    "reason": "concise overall comparison",
    "flip_condition": "one sentence naming the smallest change or evidence that would reverse the verdict"
  }
}
```
