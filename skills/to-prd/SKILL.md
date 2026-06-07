---
name: to-prd
description: Use when the user wants to create a PRD from the current conversation context, or capture requirements for asynchronous or parallel pickup. Synthesizes context into a PRD and publishes it to the issue tracker (GitHub Issues when available, local markdown under thoughts/ otherwise).
---

# To PRD

Take the current conversation context and codebase understanding and produce a PRD. Do NOT interview the user — just synthesize what you already know.

Tracker resolution and publishing mechanics: [tracker-conventions.md](../to-issues/tracker-conventions.md).

## Process

1. **Explore the repo** to understand the current state of the codebase, if you haven't already. Use the project's domain glossary (`CONTEXT.md`) vocabulary throughout the PRD, and respect any ADRs in the area you're touching.

2. **Sketch the test seams** at which the feature will be tested. Prefer existing seams to new ones; use the highest seam possible. If new seams are needed, propose them at the highest point you can.

   Check with the user that these seams match their expectations.

3. **Write the PRD** using the template below, then publish it per the tracker conventions (GitHub: an issue labeled `ready-for-agent`; local: `thoughts/shared/tickets/<feature-slug>/PRD.md` with `Status: ready-for-agent`). No additional triage needed.

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories covering all aspects of the feature, each in the format:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

## Implementation Decisions

A list of implementation decisions that were made: modules to build/modify, interfaces that change, technical clarifications, architectural decisions, schema changes, API contracts, specific interactions.

Do NOT include specific file paths or code snippets — they go stale quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts.

## Testing Decisions

- What makes a good test here (test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (similar tests in the codebase)

## Out of Scope

Things explicitly out of scope for this PRD.

## Further Notes

Any further notes about the feature.

</prd-template>
