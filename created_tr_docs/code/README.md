# Runnable code for the Long-Term Memory TR Doc

Verifies every technical claim in
`../building-llm-applications--33-building-memory-agents-long-term-memory.md`.

## Setup (already done)
    python3 -m venv .venv
    ./.venv/bin/pip install -r requirements.txt

Keys are read from `../../.env` (GOOGLE_API_KEY, TAVILY_API_KEY, RAPID_API_KEY).

## Scripts

| File | Needs keys? | What it does |
|------|-------------|--------------|
| `verify_doc_claims.py` | No | 9 assertions on the Store API, merge logic, tool schemas, namespace isolation, embeddings index |
| `verify_doc_fixes.py` | No | 18 assertions on the claims added/corrected in review: `total=False` schema, tool rename, `save_memory`/`search_memory` pair, top-k has no threshold, `filter=`, `index=False`, `store.delete`, `forget_learner`, TTL capability + units, `created_at` for recency, `debug=`, `.text`, `SqliteStore`, `@dynamic_prompt` push injection, dedup-on-write, recency re-rank, provenance filter |
| `skillmap_memory_agent.py` | Yes | The doc's final code, end to end: session 1 saves, session 2 recalls across a new thread_id, session 3 proves per-user isolation |
| `test_content_extraction.py` | Yes (Gemini) | Shows why `.text` is required instead of `.content` |

## Run
    ./.venv/bin/python verify_doc_claims.py
    ./.venv/bin/python verify_doc_fixes.py
    ./.venv/bin/python skillmap_memory_agent.py

Verified against langchain 1.3.17 / langchain-core 1.6.0 / langgraph 1.2.11 /
langchain-google-genai 4.3.5.

## Note on quota
The Gemini free tier allows **20 requests/day** for `gemini-2.5-flash`. One full run of
`skillmap_memory_agent.py` uses roughly 6-10. On `RESOURCE_EXHAUSTED` the script skips
that session with a message instead of crashing.
