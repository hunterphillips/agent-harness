---
id: coding-01-bug-fix
type: bug-fix
weight: 1.0
---
## Task Prompt

Fix the slug generator so runs of punctuation, whitespace, and underscores between words become one `-`. Preserve the existing behavior for case folding, Unicode letters, digits, empty input, and leading or trailing separators. A regression test already demonstrates the reported failure. Do not edit the tests.
