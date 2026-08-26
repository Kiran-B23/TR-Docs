# Review Inputs — "Build Your Own MCP Server"

**Material reviewed:** Building LLM Applications → Model Context Protocol, Authoring Servers
**Reviewed as:** experienced developer, reviewing for classroom delivery
**Audience assumption:** 1st / 2nd year undergraduates, first exposure to authoring a protocol server, prior sessions covered LangChain `@tool`, agent memory, and consuming a hosted MCP server
**Review date:** 26 August 2026

---

## 1. Summary verdict

**Ship it, but not as-is.** The instructional design is genuinely above average — better than most published MCP tutorials — and the core narrative should be preserved intact. However there are four defects that will break in a live classroom, and two of them are in the final step, which means students hit them after investing an hour and with no time left to recover.

| Dimension | Assessment |
|---|---|
| Narrative and motivation | Strong. Keep as written. |
| Conceptual model (ownership: model / app / user) | Strong. Correct organising idea. |
| Correctness of runnable code | **Four blocking defects.** See §3. |
| Correctness of prose claims | Two factually wrong statements. See §4. |
| Cognitive load for stated audience | **Too high for one session.** See §5. |
| Coverage / gaps | Minor gaps, one security gap worth closing. See §6. |
| Spec currency | Good — better than most material in circulation. |

**Recommended action:** fix §3 before the next delivery; treat §5 as a restructure for the following term.

**Severity legend used below**

| Level | Meaning |
|---|---|
| **P0** | Will break during class. Fix before delivery. |
| **P1** | Wrong or misleading. Students will learn something false. |
| **P2** | Correct but costly — load, ordering, or framing problems. |
| **P3** | Gap or improvement. Safe to defer. |

---

## 2. What to preserve

Listing this first, deliberately: the fixes below touch a lot of surface area, and the strengths are easy to lose in a rewrite.

1. **The `+` as the thesis.** Opening on `all_tools = mcp_tools + [search_jobs]` and treating that operator as the thing requiring explanation is the best decision in the document. It gives students a concrete grievance before any protocol vocabulary arrives. Most MCP material opens with "USB-C for AI" and never earns the analogy. Do not replace this with a definition.

2. **The ownership table.** Model chooses tools / application chooses resources / user chooses prompts. This is the right axis, it is the axis students actually get wrong, and repeating it in the Check Your Understanding answers is correct reinforcement.

3. **Step 9 in its entirety.** "An unhandled exception in an MCP tool is a silent error" is the single most useful sentence in the session. It is not in the official docs and it costs practitioners days. The before/after contrast with one line of difference is exactly the right way to show it.

4. **The debugging exercise.** Three planted faults where none produces a useful error, and the instruction to decide *what you would run first* before looking. The duplicate-registration fault (silent overwrite, no warning) is a particularly good choice.

5. **"Run `--method tools/list` before debugging anything else."** Professional habit-forming. Keep it, and consider repeating it in the slide deck.

6. **Step 6 marked read-only.** Correctly identifying elicitation as worth understanding but not worth building at this level is good scope discipline.

7. **The "When should you build an MCP server?" decision path.** Teaching students *not* to reach for the tool they just learned is rare and valuable.

---

## 3. P0 — Blocking defects

### P0-1 — Both client launch commands defeat the `uv run` guarantee

**Location:** Step 11, `MultiServerMCPClient` config and the `claude mcp add` command.

**The defect.** `uv run` resolves the project — and therefore the virtual environment — from the **current working directory**, not from the path of the script it is given. Neither invocation controls the working directory.

```python
# Step 11, as written
"skillmap": {"transport": "stdio", "command": "uv", "args": ["run", "server.py"]}
```

The client process runs in the client folder — which Step 11 has just instructed students to create as a *separate* directory with a *separate* virtual environment pinned to `mcp<2.0.0`. So `server.py` is not on that path; and if a student flattens the folders to make it resolve, uv then starts the server against the client's 1.x environment, where `MCPServer` does not import.

```bash
# Step 11, as written
claude mcp add --transport stdio skillmap -- uv run /absolute/path/to/server.py
```

The absolute path locates the file but not the project. Claude Code launches with the cwd of whatever project the student is working in, so uv resolves *that* project's environment and runs `server.py` inside it. Missing `mcp`, missing `requests`, immediate exit, connection closed, no error text.

**Why this is the worst defect in the document.** Step 1 spends three paragraphs establishing that `uv run` exists precisely to guarantee the server starts in the environment you installed into, and the troubleshooting table names "the client launches your server with a different working directory" as a symptom. The document diagnoses this failure and then commits it — twice, in the final step, as the payoff.

**Fix.**

```python
"skillmap": {
    "transport": "stdio",
    "command": "uv",
    "args": ["--directory", "/abs/path/to/skillmap-mcp", "run", "server.py"],
}
```

```bash
claude mcp add --transport stdio skillmap -- \
  uv --directory /abs/path/to/skillmap-mcp run server.py
```

Note `--directory` is a **uv** flag, so it goes before `run`, not after. Worth calling that out explicitly — students will put it in the wrong place.

**Teaching opportunity.** This is not merely a typo to correct silently. `--directory` is the mechanism that makes the Step 1 promise true, and explaining it converts an accident into the session's cleanest illustration of why "installed" has to mean "installed in an environment a specific command can start."

---

### P0-2 — `load_dotenv()` does not do what the text claims

**Location:** Step 3, prose immediately following the import block.

**The claim in the document:**

> Put your `.env` file next to `server.py` [...] `load_dotenv()` looks for it relative to the script, so it is still found when a client launches your server from some other directory.

**Reality.** Bare `load_dotenv()` searches from the **current working directory** upward. It has no knowledge of the script's location. So it fails in exactly the scenario the sentence promises it survives.

**Why it matters more than a normal doc error.** The failure surfaces as:

```
ToolError: TAVILY_API_KEY is not configured on the server.
```

A student reads that message and goes looking for a missing or misspelled key — while the `.env` file sits correctly next to `server.py`. The error is truthful about the symptom and completely misleading about the cause. Combined with P0-1, a student following Step 11 exactly can hit two independent path-resolution failures in the same minute.

**Fix.** The correct pattern is already used one line below for `PROFILES`:

```python
load_dotenv(Path(__file__).parent / ".env")
```

Move the `PROFILES` definition above `load_dotenv` and reuse the parent, or just repeat the expression. Then the prose claim becomes true and the two lines teach the same lesson together: *a server launched by someone else cannot assume anything about its working directory.*

---

### P0-3 — Windows students cannot complete Step 1

**Location:** Step 1, setup block.

```bash
uv venv
source .venv/bin/activate
touch server.py
```

`source .venv/bin/activate` and `touch` are both POSIX-only. The document supplies a PowerShell installer line immediately above, so Windows students are expected in the room.

**Fix — and a simplification worth taking.** Do not add a PowerShell variant. Remove the activation entirely:

```bash
uv init skillmap-mcp
cd skillmap-mcp
uv add "mcp[cli]" requests python-dotenv
```

Then have students create `server.py` in their editor. `uv add` creates the virtual environment on its own, and `uv run` uses it without activation. This removes the platform fork *and* removes a mixed message — the current text activates a venv and then explains at length that `uv run` is what actually matters. Cutting activation makes the lesson cleaner, not just shorter.

`uv init` also generates a starter `main.py`; either tell students to delete it or have them use it instead of creating a new file, otherwise the folder contents won't match the text.

---

### P0-4 — An unresolved author note is in student-facing material

**Location:** Step 6, inside the elicitation warning box.

> **UNVERIFIED — author to confirm:** the shape above is correct against SDK 2.1.1 and the `Context` injection is verified, but a full round-trip needs a client that supports elicitation.

This is internal reviewer scaffolding. Students reading it either lose confidence in the rest of the document or, worse, spend time trying to make an unverified snippet work.

**Fix.** Pick one: (a) verify the round-trip against a supporting client and delete the note; (b) keep the code, delete the note, and state plainly in prose that few clients implement elicitation yet so it may not round-trip in their setup; (c) cut the code and describe elicitation in prose only. Given Step 6 is already marked read-only, (c) is the cheapest and loses almost nothing.

---

## 4. P1 — Correctness and consistency

### P1-1 — Import path is inconsistent, and possibly wrong throughout

Every code block uses:

```python
from mcp.server import MCPServer
```

but Step 6 uses:

```python
from mcp.server.mcpserver import Context
```

The rename itself is real: SDK 2.0 renamed `FastMCP` to `MCPServer` and moved `mcp.server.fastmcp.*` to `mcp.server.mcpserver.*`. But published migration guidance consistently gives the class as `from mcp.server.mcpserver import MCPServer`. If the top-level re-export does not exist, **every code block in the document fails on line 1** — including the twelve-line server in Step 2, which is the first thing a student runs.

**Action required.** Fresh `uv add "mcp[cli]"` in a clean directory, then confirm all four of these against the installed package:

- `MCPServer` import path — and use one form consistently
- `ToolError` and `ResourceNotFoundError` — the document places them at `mcp.server.mcpserver.exceptions`
- `Context` import path
- whether the `[cli]` extra still exists in 2.x

Also: protocol types moved to a standalone `mcp-types` package in 2.x. Nothing in the session imports them directly, but it will surface in any error message or stack trace students see, and a one-line mention prevents confusion.

### P1-2 — Pin the version in Step 1, not just in the closing note

The document's own closing note advises pinning so *you* choose when to move. The setup step does not pin. Given that this session exists in the middle of a 1.x→2.x migration with an incompatible client library at Step 11, an unpinned `uv add mcp` is a live hazard: a student setting up a week later can land on a different minor version. State the exact version in Step 1 and show it in `pyproject.toml`.

### P1-3 — `except Exception` mislabels the student's own bugs

```python
except Exception as e:
    raise ToolError(f"Could not reach the jobs API: {type(e).__name__}")
```

Three problems, in increasing order of importance:

1. **Too broad.** A `KeyError` in the list comprehension below becomes "Could not reach the jobs API: KeyError". The student's own bug is reported as a network fault. Narrow to `requests.RequestException`.
2. **Traceback destroyed.** The exception is swallowed with no logging. A student debugging their own tool body has one line of text and nothing else — and the Step 9 lesson (detail-free errors mean an unconverted exception) now works against them, because *this* error has detail and is still uninformative about location. Add `logger.exception("jobs API call failed")` before raising.
3. **Chain not preserved.** `raise ToolError(...) from e` costs three characters and is the correct idiom.

Recommended shape for the teaching example:

```python
try:
    r = requests.get(..., timeout=30)
    r.raise_for_status()
except requests.RequestException as e:
    logger.exception("jobs API call failed")
    raise ToolError(f"Could not reach the jobs API: {type(e).__name__}") from e
```

`raise_for_status()` also collapses the separate status-code check, which shortens the block — worth it, since this pattern is repeated across three tools and students will copy it.

### P1-4 — Tavily authentication may be stale

Step 3 passes the key in the request body:

```python
json={"api_key": TAVILY_API_KEY, "query": ...}
```

Verify against current Tavily documentation; the body-parameter form has been superseded by an `Authorization: Bearer tvly-...` header. If it has been removed, every student receives a 401 in Step 3, the `ToolError` reports a status code, and they will assume their own key is wrong. Same check applies to the RapidAPI/JSearch host and path.

### P1-5 — The stdout guard is presented as verified behaviour

> On startup, SDK 2.x takes a private copy of stdout for the protocol and redirects your program's stdout to **stderr** — so a stray `print()` no longer breaks the connection. Try it if you like; it works.

Two objections.

**Factual risk.** This is an internal implementation detail of one SDK minor version, asserted without a source. If it changes, or differs across transports, students carry a habit that silently corrupts JSON-RPC.

**Pedagogical.** The box states the rule absolutely, then demonstrates that breaking it is harmless, then asks students to follow it anyway on the strength of four secondary arguments. A first-year student reads "try it if you like; it works" as permission. The rule does not survive that framing.

**Fix.** Reduce to two sentences: a stdio server uses stdout for the protocol, so keep your own output off it and use `logging`, which writes to stderr. Delete the guard discussion. If you want to keep it for accuracy, move it to an instructor's note rather than student-facing text.

### P1-6 — The "See It Break" demonstration doesn't quite show what the text claims

The text concludes:

> every caller that had already discovered your old schema now fails

What is actually demonstrated is a hand-written Inspector call with literal `--tool-arg` values being rejected by validation. The mechanism is the same and the conclusion is right, but no discovery occurred, so an attentive student can object. Either adjust the wording ("a call built against your old schema now fails"), or — better — have them run `--method tools/list` before and after the rename so they see the published contract change. That costs one command and makes the point properly.

---

## 5. P2 — Load and structure

### P2-1 — This is two sessions, not one

Eleven steps, eight callout boxes, a final-code appendix, a "not covering" section, a troubleshooting table, a debugging exercise, and seven comprehension questions. For students whose prior experience is Colab cells, this is a lot of new machinery arriving at once: a terminal, a project manager, virtual environments, a subprocess model, JSON-RPC, three primitives, two transports, two error channels, and semantic versioning.

**Suggested split.**

| Session | Steps | Closing state |
|---|---|---|
| A — *Make it exist* | 1–5 | A server with three tools, one resource, one prompt, verified with the Inspector CLI |
| B — *Make it reachable* | 7–11 | Same server consumed by Claude Code and by an agent, with errors, versioning, and transports |

Step 6 (elicitation) becomes optional reading between the two. Step 8 (Inspector) has to appear in both — introduce the CLI smoke test in A, and the full three-client tour in B.

This split also has a clean conceptual boundary: session A is "a program", session B is "a service", which is the same distinction the introduction uses to motivate the whole session.

### P2-2 — The handshake warning arrives far too early

**Location:** "How MCP Actually Works", the box after exchange 1.

At that point a student has written zero lines of code and is asked to hold four facts simultaneously: here are four exchanges; exchange 1 doesn't exist in the current spec; your SDK does it anyway; probing over HTTP gives session-ID errors. This is a hard idea even for someone who has written a server.

It is also **redundant** — Step 10 covers the same ground properly, in context, where protocol version is already the topic.

**Fix.** Delete the early box. Replace with one sentence: *how the two sides agree on a version is changing, and we come back to it in Step 10.* Let students build one coherent mental model before complicating it. The "direction of travel" point lands far better once they have something running.

### P2-3 — Two API keys before the first working server

Step 3 requires Tavily and RapidAPI signups. At cohort scale this means: signup friction, per-account rate limits, free-tier expiries, and at least one student blocked on email verification while the class moves on. The failures are all indistinguishable from code errors at the student's end.

**Fix.** Make the Step 2 tool keyless — read a local file, compute something, return the current time. Students then get `tools/list` answering, and their first Inspector success, with zero external dependencies. Keys arrive in Step 3 where the real APIs do, and a student blocked on a signup has still learned the protocol shape.

This also improves Step 2's own argument. The text says to get *one* tool answering before adding others so that failures are easy to localise; a tool that depends on a third-party key and a network call is not the smallest possible first tool.

### P2-4 — The finale rests on a version conflict

Step 11's primary client is `langchain-mcp-adapters`, which requires `mcp<2.0.0` — so the session's payoff needs a second folder, a second virtual environment, and a warning box explaining what not to install. That warning is the last substantive thing students read before the summary.

The material handles the conflict correctly. The problem is placement: the climax is the most fragile part of the session, and it is fragile for reasons that have nothing to do with MCP.

**Fix — reorder within Step 11.** Lead with Claude Code:

```bash
claude mcp add --transport stdio skillmap -- \
  uv --directory /abs/path/to/skillmap-mcp run server.py
claude mcp get skillmap
```

No second environment, no version conflict, no new Python. It also demonstrates the session's central claim — *any* client can reach it — more forcefully than a LangChain adapter does, because it is visibly not the framework they've been using all term.

Then show `MultiServerMCPClient` second, as the "inside your own agent" variant, with the version warning attached. Same content, but the failure-prone path is no longer the finish line. The existing "The Payoff" paragraph about a 1.x client consuming a 2.x server is excellent and should stay — it just works better as the *second* demonstration than the only one.

### P2-5 — Callout density

Eight `MultiLineWarning` / `MultiLineNote` boxes, several running longer than the step they interrupt. The signal-to-interruption ratio matters more for this audience than for practitioners: a student cannot yet tell which asides are load-bearing and which are context.

Suggested triage:

| Box | Action |
|---|---|
| Handshake is going away | Delete (see P2-2) |
| `print()` / stdout | Cut to two lines in body text (P1-5) |
| Who supplies the `user_id` | **Keep as-is.** Best box in the document. |
| Elicitation needs a supporting client | Keep, minus the UNVERIFIED note |
| Install the client library elsewhere | Keep — it prevents real damage |
| What the Python SDK actually does (errors) | Keep, shorten |
| Async / one-process-per-client note | Demote to instructor note or B-session appendix |
| Spec-ahead-of-SDK pattern | Keep — good closing thought |

---

## 6. P3 — Gaps

### P3-1 — No `.gitignore`, and a step that encourages committing config

Students hold two API keys in a `.env`, and Step 11 mentions `project` scope writing a committed `.mcp.json`. Somebody will push a key. One line in Step 1:

```bash
printf '.env\n.venv/\nprofiles.json\n__pycache__/\n' > .gitignore
```

Worth saying out loud that `.mcp.json` is committed and `.env` is not, since the session introduces both in the same breath.

### P3-2 — Nothing on untrusted tool descriptions or tool output

The session ends with students publishing servers and connecting other people's servers to their agents. The security content present is good but covers only one axis — identity and the transport boundary, in the `user_id` box.

Missing, and worth one short paragraph near that box:

- A tool **description** is text the model reads and acts on. Installing someone's server means letting them add instructions to your agent's context.
- Tool **output** goes into the context too. `search_jobs` returns strings from a third-party API; those strings are untrusted input.

This is not a lecture on prompt injection — two sentences and a "we are not covering the defences today" is enough. But a student who publishes a server without ever hearing that a tool description is an instruction has a real gap.

### P3-3 — Tool annotations not mentioned

`save_learner_profile` writes to disk. `readOnlyHint` and `destructiveHint` are how a server tells a client which tools need confirmation, and clients use them. One sentence beside the `title` discussion in Step 2 would cover it, and it reinforces the "your schema is a public contract" idea from Step 10.

### P3-4 — Concurrency of `profiles.json` is glossed

Read-modify-write with no locking. On stdio, one process per client, single user — genuinely fine, and the document is right not to complicate it. But the "one process serving many clients" note in Step 7 is exactly where a student might connect the two. Consider one clause: *and shared files need locking once several clients write at once.*

### P3-5 — Structured output claim should be spot-checked

Step 9 shows the SDK wrapping a `list[dict]` return into `{"result": [...]}` with a generated `search_jobsOutput` schema. Plausible, but it is a 2.x behaviour presented with exact JSON. Verify the wrapper key and title format against the installed version — students will compare their output character by character.

---

## 7. Verification checklist before next delivery

Run in a clean directory on both macOS/Linux and Windows.

- [ ] `uv init` + `uv add "mcp[cli]" requests python-dotenv` — record the exact resolved `mcp` version and pin it in the text
- [ ] `from mcp.server import MCPServer` — does it import? If not, correct every code block
- [ ] `ToolError`, `ResourceNotFoundError`, `Context` — confirm import paths
- [ ] Step 2 twelve-line server: `uv run server.py` starts, `--method tools/list` returns the tool
- [ ] Generated `inputSchema` matches the JSON printed in Step 2
- [ ] Generated `structured_content` and output schema match the JSON printed in Step 9
- [ ] Tavily call succeeds with a current free-tier key, using the auth form shown
- [ ] JSearch call succeeds with a current RapidAPI key
- [ ] `.env` is found when the server is launched from a **different** directory (this is the P0-2 regression test)
- [ ] `resources/read` envelope matches the JSON printed in Step 8
- [ ] `claude mcp add ... uv --directory ... run server.py` connects, and `claude mcp get skillmap` confirms
- [ ] `MultiServerMCPClient` with `--directory` returns three tools from a separate client folder and venv
- [ ] All three planted debugging faults produce the errors the answers claim
- [ ] Windows: full Step 1 → Step 2 path with no POSIX commands

---

## 8. Priority summary

| ID | Severity | Location | One-line fix |
|---|---|---|---|
| P0-1 | P0 | Step 11 | Add `uv --directory /abs/path` to both launch commands |
| P0-2 | P0 | Step 3 | `load_dotenv(Path(__file__).parent / ".env")`; correct the prose |
| P0-3 | P0 | Step 1 | Drop `uv venv` + `activate` + `touch`; cross-platform path |
| P0-4 | P0 | Step 6 | Remove the UNVERIFIED author note |
| P1-1 | P1 | throughout | Verify and unify the `MCPServer` import path |
| P1-2 | P1 | Step 1 | Pin the exact `mcp` version at setup |
| P1-3 | P1 | Step 3 | Narrow the except, log, chain with `from e` |
| P1-4 | P1 | Step 3 | Verify Tavily auth form |
| P1-5 | P1 | Step 2 | Cut the stdout-guard discussion to two lines |
| P1-6 | P1 | Step 10 | Show `tools/list` before and after the rename |
| P2-1 | P2 | whole | Split into two sessions at Step 5/7 |
| P2-2 | P2 | §How MCP works | Delete the early handshake box; forward-reference Step 10 |
| P2-3 | P2 | Step 2 | Make the first tool keyless |
| P2-4 | P2 | Step 11 | Lead with Claude Code, LangChain second |
| P2-5 | P2 | whole | Triage the eight callouts per table in §5 |
| P3-1 | P3 | Step 1 | Add `.gitignore` |
| P3-2 | P3 | Step 3 | Two sentences on tool descriptions and output as untrusted input |
| P3-3 | P3 | Step 2 | Mention `readOnlyHint` / `destructiveHint` |
| P3-4 | P3 | Step 7 | One clause on file locking under HTTP |
| P3-5 | P3 | Step 9 | Spot-check the structured-output JSON |

**Minimum viable fix set for the next delivery:** P0-1 through P0-4, plus P1-1 and P1-2. Everything else can wait a term without a student getting stuck.
