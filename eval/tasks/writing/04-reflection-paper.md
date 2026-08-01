---
id: writing-04-reflection-paper
type: academic
weight: 1.0
---
## Task Prompt

Write a weekly reflection (450–550 words) for a graduate AI Studio course, based on the student's project notes below. First person, academic but natural register — this is a graded reflection, not a report. It must take an honest position on what the student got wrong, use at least four specific details from the notes, and end with what this changes about how they'll build next. Do not invent events, results, or readings not in the notes.

## Fixed Source Input

Student's raw notes on this week's project work (red-teaming the safety controls of Buddy AI, a mental-wellness chat app the team built — a single-file browser app calling a model API directly):

Going in, I assumed our safety story was decent because we had three layers: a crisis-keyword regex that intercepts messages before they reach the model, safety instructions in the system prompt (no diagnosis, no prescriptions, never claim licensure, crisis protocol), and a visible disclaimer in the UI. Wrote the test suite this week and found out only the regex is actually enforced in code — the other two are requests to the model and a label, not controls.

Then the regex turned out to be trivially evadable. All seven of our crisis-evasion test cases slipped past it: algospeak ("unalive"), leetspeak, spaced-out letters, misspellings, plain euphemism, non-English phrasing. So for exactly the users we most need to catch, the only enforced control does nothing and the unenforced prompt instructions are the real backstop.

Other findings: the model's replies render with no output-side check at all, and the web-search tool feeds retrieved page content to the model as trusted text — instructions hidden in a page would arrive through that channel unmarked.

Test design decisions I'm proud of: we included "true negative" cases that are near-twins of attacks (the idiom "this project is killing me," a grief conversation, an essay-brainstorm request) so we measure over-refusal, not just refusal. And the grading is cross-checked: a deterministic layer catches provable failures (a planted canary token appearing in output; a crisis reply with no 988 hotline string), and those override the AI judge when they fire.

Uncomfortable admission for the reflection: I had demoed the crisis regex to the class in week 2 as evidence we took safety seriously. Nobody on the team ever tried to get around it until this week — we tested that it fired, never that it could be missed.

Next steps we chose (cheapest first): rewrite the system prompt with an explicit instruction hierarchy and mark retrieved web content as untrusted; add an output check that grades the model's draft reply before rendering; a real guard model needs a server we don't have yet.
