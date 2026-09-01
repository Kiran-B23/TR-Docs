# Reference URLs

Sources behind `created_tr_docs/building-llm-applications--33-building-memory-agents-long-term-memory.md`.

---

## 1. Conceptual framing (provided)

Used for vocabulary and structure only. Vendor blogs — their benchmark numbers
(latency %, precision %, similarity thresholds) were deliberately **not** carried into the doc.

https://mem0.ai/blog/memory-in-agents-what-why-and-how
> Three pillars (state / persistence / selection); write-path → read-path → consolidation lifecycle; "Context window ≠ Memory".

https://mem0.ai/blog/rag-vs-ai-memory
> The RAG-vs-memory table: relevance as a property of content vs. of the user; read-only vs read-write; time awareness; conflict handling.

https://mem0.ai/blog/short-term-vs-long-term-memory-in-ai
> ST vs LT rows: scope, lifetime, size, latency, storage, cost; failure modes on both sides.

https://mem0.ai/blog/short-term-memory-for-ai-agents
> What short-term memory holds; context-window thresholds; truncation / summarization trade-offs (used for the Unit 31 recap).

https://mem0.ai/blog/long-term-memory-ai-agents
> Why large context windows don't replace memory; extraction → consolidation → retrieval; challenges.

https://mem0.ai/blog/semantic-vs-episodic-vs-procedural-memory-in-ai-agents-a-complete-comparison
> The three memory types plus the *characteristic failure* of each — the backbone of the "Types of Long-Term Memory" section.

---

## 2. Implementation — LangChain v1 / LangGraph docs (fetched, and independently verified in code)

**These are the source of truth for every API in the doc.**

https://docs.langchain.com/oss/python/langchain/long-term-memory
> PRIMARY. `InMemoryStore`, namespace/key/value model, `ToolRuntime` read & write tools,
> `create_agent(store=, context_schema=)`, `PostgresStore`.

https://docs.langchain.com/oss/python/langgraph/stores
> `store.put / get / search / list_namespaces` signatures; `index={"embed":..., "dims":..., "fields":[...]}`
> semantic-search config; the list of store implementations (InMemoryStore, PostgresStore,
> AsyncPostgresStore, MongoDBStore, RedisStore, UpstashStore — **no SqliteStore**).

https://docs.langchain.com/oss/python/langchain/short-term-memory
> Checkpointer + `thread_id` pattern, `SummarizationMiddleware`, `RemoveMessage`, `PostgresSaver`.
> Used for the Unit 31 recap and the production callout.

https://docs.langchain.com/oss/python/langgraph/memory
> LangGraph memory concepts; store vs checkpointer separation; namespace examples.

https://docs.langchain.com/oss/python/langgraph/persistence
> Persistence model behind checkpointers and stores. Thin — defers to the Stores guide above.

---

## 3. Claims cited in the doc but NOT fetched this session

Listed so the assertions in the doc are traceable. Worth reading before the doc is published.

https://arxiv.org/abs/2307.03172
> "Lost in the Middle: How Language Models Use Long Contexts" (Liu et al.) — the basis for the
> doc's claim that models under-attend to material in the middle of a long context.

https://research.trychroma.com/context-rot
> Context rot. Already cited in Unit 41 (Context Engineering); the doc calls back to it.

https://ai.google.dev/gemini-api/docs/rate-limits
> Gemini free tier = 20 requests/day for `gemini-2.5-flash`. Relevant when students run the final code.

---

## 4. Empirical source of truth (verified locally, not from docs)

Some claims were settled by **running code**, not by reading. See `created_tr_docs/code/`.

Verified against: `langchain 1.3.17` · `langchain-core 1.6.0` · `langgraph 1.2.11` ·
`langchain-google-genai 4.3.5` · Python 3.12.3

| Claim | How it was settled |
|---|---|
| `.text` (not `.content` or `.content[0]["text"]`) is the reliable way to read an agent reply | Live Gemini run: `content` came back as `str` on one turn and `list` of blocks on others. `.content[0]["text"]` raises `TypeError` on string turns; `.content` prints raw signature blobs. |
| `store.search(ns, query=...)` on a **non-indexed** store does not raise — it silently returns unranked results | `verify_doc_claims.py` check 2 |
| A blind `store.put()` with a partial profile destroys the other fields; `TypedDict` is not enforced at runtime | `verify_doc_claims.py` checks 3 and 4 |
| `runtime: ToolRuntime` is excluded from the tool schema the model sees | `verify_doc_claims.py` check 5 |
| `index={"embed": <Embeddings instance>}` is accepted (not only a provider string) | `verify_doc_claims.py` check 8 |
| Long-term memory survives a new `thread_id`; a different `user_id` sees nothing | `skillmap_memory_agent.py` sessions 1 → 2 → 3 |

Re-run any time with:

    cd created_tr_docs/code
    ./.venv/bin/python verify_doc_claims.py      # no API key needed
    ./.venv/bin/python skillmap_memory_agent.py  # needs ../../.env

---

## 5. Build Your Own MCP Server — official MCP documentation

Sources behind `created_tr_docs/building-llm-applications--build-your-own-mcp-server.md`.
All fetched; every API claim was then re-verified against the installed SDK (see §6).

https://modelcontextprotocol.io/docs/develop/build-server
> PRIMARY. Python quickstart: `from mcp.server import MCPServer`, `@mcp.tool()`,
> `mcp.run(transport="stdio")`, the uv setup, and the **never-print-to-stdout** rule.
>
> Re-fetched 26 Aug 2026 and confirmed line for line against the doc: the quickstart
> really does use `MCPServer` (not `FastMCP`), `uv add "mcp[cli]"`, and
> `mcp.run(transport="stdio")` — so the doc follows the current official approach, not a
> local variant.
>
> The stdout rule is quoted verbatim on this page under "Logging in MCP Servers":
> *"Never write to stdout. Writing to stdout will corrupt the JSON-RPC messages and break
> your server. The `print()` function writes to stdout by default, so keep it out of a
> STDIO server entirely."*
>
> **Docs-vs-implementation divergence — do not re-litigate this.** The rule as written is
> no longer literally true for SDK 2.x: `mcp/server/stdio.py` claims a private duplicate of
> fd 1 for the protocol and points fd 1 at stderr (`_open_stdout_diversion` -> `os.dup(2)`),
> so a stray `print()` does not break the connection. Tested both inside a tool and at
> import time. The page does not mention the guard. The doc keeps the quote *and* states
> what actually happens.

https://modelcontextprotocol.io/docs/learn/server-concepts
> Tools / Resources / Prompts and who controls each (Model / Application / User);
> direct resources vs resource templates.

https://modelcontextprotocol.io/docs/learn/architecture
> Host / client / server, one client per server, data layer vs transport layer.

https://modelcontextprotocol.io/specification/2025-06-18/server/tools
> The two error mechanisms (protocol error vs `isError: true`), `outputSchema`
> and `structuredContent`, with JSON examples.

https://modelcontextprotocol.io/specification/2025-06-18/server/resources
> `resources/list` / `resources/read`, URI schemes, `-32602` for a missing resource,
> and the rule that an empty `contents` array is never acceptable for one.

https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle
> Protocol version negotiation and `serverInfo` name/version.

https://modelcontextprotocol.io/specification/2026-07-28/basic/transports
> stdio and Streamable HTTP as *bindings*; identical JSON-RPC either way.
>
> Re-fetched 26 Aug 2026: this revision defines **exactly two** standard transports —
> stdio and Streamable HTTP. HTTP+SSE is not among them. The SDK still accepts
> `transport="sse"` for older clients, so the doc now flags it as legacy rather than
> listing three equal options. Note Streamable HTTP still uses SSE for streaming replies;
> what went away was SSE as a separate transport.

https://modelcontextprotocol.io/legacy/tools/inspector
> MCP Inspector web / CLI / TUI, exact `npx` commands, Node 22.19+ requirement.

https://code.claude.com/docs/en/mcp
> `claude mcp add`, the `--` separator, transports, and installation scopes.

https://pypi.org/pypi/mcp/json
> Current SDK version and dependencies (`httpx2`, `pydantic>=2.12`).

---

## 6. Empirical source of truth — MCP server doc

Verified by running code in `created_tr_docs/mcp_code/` on **26 Aug 2026**, against
`mcp 2.1.1` · `httpx2 2.12.0` · `pydantic 2.13.4` · Python 3.12.3 ·
MCP Inspector 2.3.0 (Node 24.14.0) · `langchain-mcp-adapters 0.3.2` ·
`langchain 1.3.17` · `langchain-google-genai 4.3.5` · `gemini-3.1-flash-lite`

`mcp_code/transcript.txt` is captured output from `test_server.py`, not written by hand.
Regenerate it after any change to `server.py`..

| Claim | How it was settled |
|---|---|
| `MCPServer` lives in `mcp.server`; `run()` accepts `stdio` / `sse` / `streamable-http` | Introspected the installed class signature |
| `@mcp.resource(uri, mime_type=...)` and resource templates expand `{user_id}` | `resources/templates/list` + a real `resources/read` |
| Input **and output** schemas are generated from type hints | Read `input_schema` / `output_schema` off `tools/list` |
| `ToolError` becomes `is_error=True` with the message as text content | Ran a deliberately failing tool call |
| `ResourceNotFoundError` surfaces as a protocol-level `MCPError` | Read a resource that does not exist |
| **The Python SDK returns unknown tools and validation failures as `isError` results, not JSON-RPC protocol errors** — contrary to a spec-only reading | Called a nonexistent tool and omitted a required argument |
| The negotiated protocol version is `2026-07-28` | Printed `client.protocol_version` |
| HTTP transport binds to `127.0.0.1:8000`, endpoint `/mcp` | Started it and connected a real client |
| The same `server.py` serves stdio and HTTP unchanged | Ran both against the same file |
| **A `ToolError` message reaches the model; any other exception is masked to `Error executing tool <name>`** | Raised both from the same tool and compared what the client received. With a live `gemini-3.1-flash-lite` agent the difference is stark: guarded → *"unable to retrieve the job listings because the necessary API key … is not configured on the server"*; unguarded → *"it failed with an error."* This is why the doc's three tools wrap their HTTP calls in `try/except → ToolError`. |
| **`langchain-mcp-adapters` requires `mcp<2.0.0`, so it cannot be installed in the server's own environment** | `pip install --dry-run langchain-mcp-adapters` into the mcp-2.x venv resolves `mcp-1.29.1`, which breaks `from mcp.server import MCPServer`. Step 10 now tells students to use a separate environment. |
| **Cross-major-version interop works across the process boundary** | Ran the full Step 10 agent with a **1.29.1** client consuming the **2.1.1** server over stdio, and again over HTTP. `get_tools()` returned all three tools and the agent called `save_learner_profile` both ways. |
| `get_resources()` and `get_prompt()` reach the resource and the prompt, not just tools | `res[0].data` is a `str` of the profile JSON; `get_prompt` returns a `HumanMessage` list |
| `print()` inside a stdio tool does **not** break the connection on SDK 2.x | Called the tool through the Inspector with a `print()` in it — `"isError": false`. Also tested a `print()` at import time. See the divergence note in §5. |
| A duplicate tool name silently keeps the **first** definition, with no warning | Registered `search_jobs` twice; `tools/list` showed one, and the first body ran |
| A resource-not-found error carries JSON-RPC code `-32602` | Read a missing resource and inspected `MCPError.code` |
| `gemini-3.1-flash-lite` exists and drives the Step 10 agent | Listed the Gemini models endpoint (exact id present), then ran the agent with it |

Re-run with:

    cd created_tr_docs/mcp_code
    ./.venv/bin/python test_server.py

**Not verified:** the `uv` flow in the doc's Step 1 — `uv` is not installed on this machine,
so `mcp_code/.venv` was built with `python3 -m venv` + `pip`. Everything downstream behaves
identically; `./.venv/bin/python server.py` substitutes for `uv run server.py`.

---

## 7. Claims tested and DISPROVEN

An external review of the MCP server session (26 Aug 2026) raised four defects that
testing did not support. Recorded here so they are not re-raised, and so the evidence
survives the conversation. Tested against `mcp 2.1.1`, `python-dotenv`, `requests`,
Python 3.12.3.

| Claim made | What testing showed |
|---|---|
| **`load_dotenv()` searches from the current working directory upward**, so a `.env` beside `server.py` is not found when a client launches it from elsewhere (raised as a blocking defect) | **False.** `find_dotenv(usecwd=False)` walks up from the *calling file's* directory. Ran a script with `.env` beside it, cwd at `/tmp` → key found. The doc's prose is correct. Caveat: it does switch to cwd in a REPL or a frozen binary — neither is the MCP case. |
| **`from mcp.server import MCPServer` may not exist**, so "every code block fails on line 1" | **False.** `from mcp.server import MCPServer` and `from mcp.server.mcpserver import MCPServer` both import and are the *same object*. `ToolError`, `ResourceNotFoundError` and `Context` all resolve at the paths the doc uses. |
| **Tavily's body-parameter auth (`json={"api_key": ...}`) is superseded**, so students would all get 401s | **False.** Live call with the doc's exact form returned **HTTP 200** with results. The `Authorization: Bearer` header also works — both forms are currently valid. |
| **The structured-output JSON in the errors step should be spot-checked** | Already verified. That JSON was captured from a live run, not reconstructed — see §6. |

Findings from the same review that testing **did** support, and which were applied:
`uv run` resolving the project from the working directory rather than the script path
(fixed with `uv --directory`), POSIX-only setup commands, the leftover author note,
broad `except Exception` without logging or chaining, the rename demo not actually
showing discovery, the missing `.gitignore`, and no mention of tool descriptions and
tool output as untrusted input.

---

## 8. Context Engineering in Practice — sources

For `created_tr_docs/building-llm-applications--context-engineering-in-practice.md`.
The doc itself carries a plain **Further Reading** list with no in-body attribution — this
section is where the mapping of source to content lives.

| Source | What came from it |
|---|---|
| https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | "Smallest set of high-signal tokens" goal; compaction, note-taking, sub-agents, just-in-time retrieval |
| https://research.trychroma.com/context-rot | The term **context rot** and the benchmarking behind it. Originates here; the Anthropic guide cites it rather than coining it |
| https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html | The four failure modes: poisoning, distraction, confusion, clash. Originates here |
| https://www.langchain.com/blog/context-engineering-for-agents | The **write / select / compress / isolate** framework; relays Breunig's four failure modes |
| https://www.promptingguide.ai/guides/context-engineering-guide | Component breakdown feeding the Context Stack table |
| https://aiengineeringfromscratch.com/lesson?path=phases%2F11-llm-engineering%2F05-context-engineering&learningPath=agentic-ai-engineer | Token budgeting across components; overflow strategies |
| https://docs.langchain.com/oss/python/langchain/middleware | `ContextEditingMiddleware`, `ClearToolUsesEdit`, `SummarizationMiddleware` signatures |

**Terminology note:** no source uses the phrase **"context stack"**. Each enumerates the parts of
the window under its own naming — LangChain: instructions / knowledge / tools; Prompting Guide:
system prompt, instructions, user input, structured I/O, tools, RAG & memory, state/history;
Anthropic: system prompts, tools, examples, message history, external data. The doc's table is a
synthesis, presented as the lesson rather than as a citation.

**Empirical source of truth:** every token count in the doc is produced and asserted by
`created_tr_docs/ce_code/skillmap_context_lab.py`.
Verified on `langchain 1.3.17`, `langchain-core 1.6.0`, `langgraph 1.2.11`,
`langchain-google-genai 4.3.5`, `langchain-tavily 0.2.18`, Python 3.12.3.

| Claim in doc | Verified |
|---|---|
| Context grows 696 → 1290 → 1897 tokens over three SkillMap turns | Yes |
| Tool output is 1535 tokens = 80% of the window at turn 3 | Yes |
| `ClearToolUsesEdit(trigger=500, keep=1)` gives 1897 → 677 | Yes |
| `ClearToolUsesEdit` defaults `trigger=100000`, `keep=3`, `exclude_tools=()` | Yes, from `inspect.signature` |
| `SummarizationMiddleware` default `keep=("messages", 20)` | Yes |
| `trigger` accepts both `("tokens", N)` and `("fraction", 0.8)` | Yes, both instantiate |
| `create_agent` accepts `middleware=` | Yes |
| Pruning edits messages to the model; stored history keeps full tool results | Yes — see `ce_code/README.md` |

**Middleware ordering**, checked by running an agent with both list orders and logging which hook
fired first: `SummarizationMiddleware` implements `before_model`, `ContextEditingMiddleware`
implements `wrap_model_call`, and the before-model hook runs first either way. Re-check if the
middleware base class changes. (Moved here from the doc — it is author provenance, not student
content.)
