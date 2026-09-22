---
max_turns: 4
timeout_seconds: 180
allowed_tools: [Read, Glob, Grep, Skill]
---

ok so, random thought, but I keep coming back to it -- we're running our job queue on redis right now and it's fine, it works, but we've had like three incidents this quarter where redis fell over or lost jobs and everyone scrambled, and separately we already run postgres for everything else so it's one less piece of infra to babysit and page on at 2am. I don't know though, postgres as a queue feels a little bit like a hack, and I keep going back and forth on it in my head without actually writing any of it down. can you help me actually think this through instead of just going in circles about it
