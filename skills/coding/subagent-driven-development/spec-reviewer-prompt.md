# Spec Compliance Reviewer Prompt Template

Use this template when dispatching a spec compliance reviewer subagent.

The block below is a field spec for the **Agent** tool, not literal syntax — `subagent_type`, `description`, and `prompt` are the real tool parameters, and everything under `prompt: |` is the prompt string the controller fills in and passes.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less)

```
Agent tool:
  subagent_type: general-purpose
  model: opus   # reviewers always run on opus
  description: "Review spec compliance for Task N"
  prompt: |
    You are reviewing whether an implementation matches its specification.

    ## What Was Requested

    [FULL TEXT of task requirements]

    ## What Implementer Claims They Built

    [From implementer's report]

    ## Verify against the code

    The report may be incomplete or optimistic; verify every claim against the code.

    Read the code, compare it to the requirements line by line, check for pieces the
    report claims that are missing, and look for extras the report does not mention.

    ## Your Job

    Read the implementation code and verify:

    **Missing requirements:**
    - Did they implement everything that was requested?
    - Are there requirements they skipped or missed?
    - Did they claim something works but didn't actually implement it?

    **Extra/unneeded work:**
    - Did they build things that weren't requested?
    - Did they over-engineer or add unnecessary features?
    - Did they add "nice to haves" that weren't in spec?

    **Misunderstandings:**
    - Did they interpret requirements differently than intended?
    - Did they solve the wrong problem?
    - Did they implement the right feature but wrong way?

    **Copy the user will read:** would an end user who is not the developer
    understand every new or changed string, and would a well-made app say it
    at all? A word that only makes sense to someone who read the spec is a
    defect, even when the spec dictated it; so is a note under a control
    whose label already says what it does.

    **Verify by reading code, not by trusting report.**

    Report:
    - ✅ Spec compliant (if everything matches after code inspection)
    - ❌ Issues found: [list specifically what's missing or extra, with file:line references]
```
