# SkillMap MCP server

Runnable code for `../building-llm-applications--build-your-own-mcp-server.md`.
`server.py` here is **AST-identical** to the Final Code block in the doc.

## Setup (already done)
    python3 -m venv .venv
    ./.venv/bin/pip install -r requirements.txt

Keys are read from `../../.env` (TAVILY_API_KEY, RAPID_API_KEY).

| File | What it does |
|------|--------------|
| `server.py` | 3 tools + 1 resource + 1 prompt, stdio transport |
| `http_server.py` | Same server over Streamable HTTP (127.0.0.1:8000/mcp) |
| `test_server.py` | In-process client: lists tools and prompts, calls them, reads the resource, and exercises every failure path — including the difference between a `ToolError` (message preserved) and an unguarded exception (message masked) |
| `http_client_test.py` | Connects a real MCP client over HTTP |

## Run
    ./.venv/bin/python test_server.py          # full behaviour transcript
    ./.venv/bin/python server.py               # stdio (waits for a client)
    ./.venv/bin/python http_server.py          # HTTP on 127.0.0.1:8000/mcp

## Connecting an agent to this server (doc Step 10)

`langchain-mcp-adapters` requires `mcp<2.0.0`, so it **cannot** live in this environment —
installing it here downgrades `mcp` to 1.x and breaks `from mcp.server import MCPServer`.

Use a second venv for the client, and point it at this one's interpreter:

    python3 -m venv /tmp/mcp-client && \
      /tmp/mcp-client/bin/pip install "langchain>=1.0,<2" langchain-google-genai \
        langchain-mcp-adapters python-dotenv

    # in the client script:
    #   command = "<abs path>/mcp_code/.venv/bin/python"
    #   args    = ["<abs path>/mcp_code/server.py"]

A 1.x client consuming this 2.x server is the protocol working as intended — they share no
Python process, only messages.

## Verified against
mcp 2.1.1 · httpx2 2.12.0 · pydantic 2.13.4 · Python 3.12.3 · protocol 2026-07-28
MCP Inspector 2.3.0 (Node 24.14.0) · langchain-mcp-adapters 0.3.2

`transcript.txt` is **captured output**, not written by hand — regenerate it with
`./.venv/bin/python test_server.py` after any change to `server.py`.

Checked end to end: stdio via the Inspector (`--cli`, `tools/list`, `tools/call`,
`resources/read`), Streamable HTTP (`POST /mcp` → 200, `POST /` → 404), the tool and
output schemas, and every failure path in the doc's Step 8.

Not verified here: the `uv` flow in the doc's Step 1 — `uv` is not installed on this
machine, so this venv was built with `python3 -m venv` + `pip`. Everything downstream
behaves identically; `./.venv/bin/python server.py` substitutes for `uv run server.py`.
