---
id: writing-05-slide-deck
type: slides
weight: 1.0
---
## Task Prompt

Build the content for a five-slide end-of-term presentation titled around the student's individual contributions to a team project. For each slide: a title that states a point (a claim, not a topic label), at most four short bullets, and a one-sentence speaker note. The audience is the professor and classmates who know the project but not who did what. The numbers in the notes must appear somewhere in the deck content — a bullet or a speaker note both count. No agenda slide, no filler.

## Fixed Source Input

Student's contribution notes, PolyPOI project (a campus map app answering questions about points of interest):

My lane was architecture, infrastructure, and the AI-assisted development workflow — the parts with no visible UI. Total time roughly 3 hours a week, 40–45 hours across the term, on a modest budget.

Database: chose Supabase because it bundles Postgres, pgvector, auth, and file storage in one service — one vendor to operate, and vector search built into the same database that holds everything else (no separate vector DB to run). It stores tenant configs, content records, admin accounts, and document embeddings.

Ingest pipeline: built the background worker that turns uploaded documents into searchable knowledge — extract, chunk, embed, index.

A design position I argued for and won: structured-data primacy over retrieval-everything. Hours and amenity lookups answer from structured records, not retrieval over documents — cheaper, faster, and still works when the AI provider is down. Retrieval is reserved for questions that actually need it.

Hosting: Vercel for the frontend, Railway for the backend. Railway over AWS because nobody on the team owns DevOps — managed deploys, near-zero ops overhead.

Workflow: AI-assisted development was the multiplier — one primary coding agent for planning, building, reviewing, and testing, and a second one for fresh-context second opinions on tricky decisions. The honest framing I want on the slide: I owned every plan, review, and merge; the AI absorbed the typing. That's how 40 hours covered this much ground.

One version-pin worth mentioning if asked: react-leaflet stayed on v4 because v5 requires React 19 and the app is on React 18.
