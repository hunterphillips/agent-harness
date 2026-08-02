---
id: writing-06-linkedin-post
type: social
weight: 1.0
---
## Task Prompt

Write a LinkedIn post from the developer sharing this side project with their professional network, which includes many ServiceNow developers and platform engineers. The post should say what it is, why it exists, and invite people to try it or look at the code. Style matters more than coverage here: it must read like a person sharing something they built, not an AI-written engagement post — no hook-line openers, no emoji-bullet feature lists, no "thrilled to announce," no hashtag pile. A couple of hashtags at most, if any. Under 160 words. Plain text only (LinkedIn has no markdown).

## Fixed Source Input

Project facts, from the developer's notes:

ServiceNow Docs MCP Server — an MCP server that gives AI agents fast, reliable access to the full ServiceNow documentation catalog. The problem it solves: AI coding agents working on the ServiceNow platform routinely hallucinate API details or work from stale docs; pointing them at the real documentation makes them trustworthy for platform work.

Numbers: 287,271 documentation chunks indexed into ChromaDB with embeddings; 231 bundle filters so a search can be scoped to a specific product area or release; 4 MCP tools (semantic search, list bundles, reassemble a full doc page from its chunks, health stats).

Stack: Python, FastMCP, ChromaDB, HuggingFace embeddings. Runs locally over stdio for any MCP client, or hosted over HTTPS on Fly.io.

It's open source; the repo link goes in the post (use the placeholder [repo link]). The developer built it solo as a side project.
