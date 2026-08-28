# Build Your Own MCP Server

**Course:** Building LLM Applications  
**Topic:** Model Context Protocol — Authoring Servers  

---

**Key Takeaways:**

- **Why our tools work in only one agent**
- **Which primitive: tool, resource or prompt**
- **Building the `skillmap` server** — setup, three tools, a resource, a prompt
- **How MCP works on the wire**
- **Testing it with the MCP Inspector**
- **Connecting it to our agent and to a coding agent**
- **Transports, errors and versioning**
- **When to build an MCP server**

---

## Introduction

In the previous session we connected the SkillMap Agent to an MCP server. We pasted a URL, called `get_tools()`, and Tavily's search arrived — we never wrote a line of its code.

By the end of that session the agent had tools from three different places:

```python
# 1. A prebuilt component — we configured it, we did not write it
skill_demand_tool = TavilySearch(max_results=5, tavily_api_key=TAVILY_API_KEY)

# 2. Our own function
@tool
def search_jobs(skill: str, location: str) -> list:
    """Search for jobs requiring a specific skill using the JSearch API."""
    ...

# 3. Tools from someone else's MCP server
mcp_tools = await client.get_tools()

all_tools = mcp_tools + [search_jobs]
```

Tavily's search reached the agent through an address. Our `search_jobs` reached it by living inside the agent's own code — so it works in this project only. Want it in another agent? Write the whole function there as well. And in the next one after that.

So what if our own tools worked the way Tavily's does — reachable by a URL, usable from any application?

That is what we build in this session: an MCP server of our own, with the SkillMap tools behind it, connected back to the agent.

---

## The Problem: Our Tools Work in Only One Agent

That `+` in the last line joins two different kinds of tool. Both work in the agent. They are not the same kind of thing:

| | Tavily's search | Our `search_jobs` |
|---|---|---|
| Where it lives | Behind a server, at an address | Inside one program |
| A second agent uses it | Add a URL | Copy the function |
| A teammate uses it | Send a URL | Send the code, and the keys |
| When it changes | Owner redeploys once | Every copy goes stale |

`search_jobs` is not badly written. It is good code with no way in.

* Tavily's tool is a **service** — it has an address, so anything that can reach it can use it.
* Ours is a **function** — to use it, we have to run the program it lives inside.

> **A capability only one program can reach is not reusable. It is copyable.**

### Where This Session Sits

| | What we did | Who could use it |
|---|---|---|
| Building AI Agents with LangChain | Wrote `@tool` functions | That one agent |
| Integrating MCP | Used **someone else's** server | That one agent |
| **This session** | **Publish our own server** | **Anything that speaks MCP** |

Before we build: **what kind of thing** should each capability be?

---

## Which Primitive, and Why

A server can expose three kinds of thing. The **Integrating MCP** session named them — tools, resources, prompts. Here is what it did not say, and it is the thing that decides which one we reach for:

> **They differ by who chooses to use them.**

| Primitive | What it is | Who chooses to use it |
|-----------|-----------|----------------------|
| **Tools** | Functions that *do* something | **The model** — it decides a search is needed |
| **Resources** | Read-only data offered as context | **The application** — the host program (our agent script, Claude Code, an IDE) puts it in front of the model |
| **Prompts** | Templates someone deliberately picks | **The user** — from a menu or a slash-command |

The host opens one client per server it connects to:

![An MCP host creates one client per server; one client connects to our local SkillMap server over stdio, another to a remote server over HTTP](assets/mcp-host-client-server.png)

> **A tool is something the model decides to do. A resource is something the application decides to show it.**

Choosing the wrong primitive is the most common mistake in a first server. It is much cheaper to fix now than after other people's clients have connected.

---

## What We Are Building

A server called **`skillmap`** that exposes one of each:

| | | Why this primitive |
|---|---|---|
| **3 tools** | `skill_demand(skill)` · `search_jobs(skill, location)` · `save_learner_profile(user_id, name, skill, location)` | The model decides when a search or a save is needed |
| **1 resource** | `learner://profile/{user_id}` → the saved profile as JSON | The application supplies it as context; the model never "calls" it |
| **1 prompt** | `career_review(skill, location)` → a ready-made career question | The user picks it to start a workflow |

### What Happens to Each Capability

They do not all move across the same way:

| Capability | Came from | On our server |
|---|---|---|
| `search_jobs` | We wrote it | Moves across unchanged — only the decorator changes |
| `skill_demand` | Prebuilt `TavilySearch` | **We write it ourselves** — a server cannot re-export someone else's tool |
| `save_learner_profile` | Memory session, LangGraph store | **Changes shape** — a server has no store, so it writes to a JSON file |

### How We Get There

We build the server in seven continuous steps — from an empty folder to a working agent that consumes it. After the build is done, we circle back and deepen the ideas we used along the way.

| The question | Answered by |
|--------------|-------------|
| How does a function inside our agent become a program something else can start? | Steps 1–3 |
| How does it offer *data* and *workflows*, not just actions? | Steps 4–5 |
| How do we know it works before connecting an agent? | Step 6 |
| How does an agent actually consume it? | Step 7 — the payoff |

After Step 7 the server is live and connected. The sections that follow — **Transports, Errors and Versioning** — cover what turns it into something other people can rely on, without interrupting the build.

---

## Heads Up: We Are Leaving Colab

Every session so far has run in Google Colab. This one cannot. With the **stdio** transport — short for *standard input/output* — the client starts the server itself by running a command, then talks to it through the same input and output channels a terminal uses. A Colab notebook is not a command another program can start, so we work **locally**: a folder, a `server.py` file, and a terminal.

One new tool comes with that. **`uv`** is a Python package manager — think `pip`, except it also creates and manages the project's virtual environment. We use it because the client, not us, starts the server, and `uv run` guarantees it starts in the environment where its libraries live. It is also what the official MCP documentation uses.

| In Colab | Locally | Why |
|----------|---------|-----|
| A cell we run | A `.py` file a command runs | A client cannot "run a cell" |
| `!pip install X` | `uv add X` | The client must start our server where `X` exists |
| The runtime resets | A project folder that persists | The server has to still work tomorrow |


### What We Need

| Requirement | Why |
|-------------|-----|
| Python 3.10 or higher | Required by the MCP Python SDK |
| MCP Python SDK 2.0.0 or higher | The API changed significantly in 2.x |
| Node.js 22.19.0 or higher | Only for the MCP Inspector, our testing tool |

---

## Step 1: Project Setup

`search_jobs` is a function inside our agent's code, so only that program can call it. To be reachable by anything else it has to become a **program** something else can start: a folder, a file, and a command.

If `uv` is not on the machine yet:

**Terminal**

```bash
# Install uv (macOS / Linux)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Install uv (Windows PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Terminal**

```bash
uv init skillmap-mcp
cd skillmap-mcp
uv add "mcp[cli]" requests python-dotenv
```

Then create `server.py` in the editor, and delete the `main.py` that `uv init` generated — we will not use it.

<MultiLineNote>
Use plain `uv init` — not `--package` or `--lib`. Those add a build system, after which `uv run` tries to *build* the project and fails looking for `src/skillmap_mcp/__init__.py`. Our code is just `server.py`; nothing needs building.
</MultiLineNote>

Now stop those API keys ever reaching a repository:

**Terminal**

```bash
printf '.env\n.venv/\nprofiles.json\n__pycache__/\n' > .gitignore
```

Both files are introduced in this session, so the difference is worth stating explicitly: **`.env` is never committed. `.mcp.json` is** — it holds the address of a server, not the credentials to use it.

### Where Everything Lives

One file does almost all the work:

```
skillmap-mcp/            ← Steps 1–5
├── .env                 ← API keys. Never committed.
├── .gitignore
├── server.py            ← everything we write in Steps 2–5
└── profiles.json        ← created at runtime by save_learner_profile

skillmap-client/         ← Step 7. A separate folder, with its own venv.
└── agent.py
```

---

## Step 2: The Smallest Server That Runs

Get one tool answering before adding the rest.

**server.py — the whole file, for now**

```python
from mcp.server import MCPServer

mcp = MCPServer("skillmap", version="1.0.0")


@mcp.tool()
def skill_demand(skill: str) -> str:
    """Research industry demand, salary insights and career trends for a skill."""
    return f"Demand information for {skill}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

* **`MCPServer("skillmap", version="1.0.0")`** — names the server and declares its version. Clients see both.
* **`@mcp.tool()`** — registers the function as a tool.
* **`mcp.run(transport="stdio")`** — starts it, and waits for a client to connect over standard input/output.

### Check That It Answers

**Terminal**

```bash
npx @modelcontextprotocol/inspector --cli uv run server.py --method tools/list
```

```
skill_demand
```

If it fails, run `uv run server.py` on its own first. A server that crashes on startup tells the client nothing.

### The Schema We Never Wrote

The tool comes back with a full schema attached:

```json
{
  "type": "object",
  "properties": {
    "skill": {"title": "Skill", "type": "string"}
  },
  "required": ["skill"],
  "title": "skill_demandArguments"
}
```

It is inherited from the function itself — **the type hints become the schema, the docstring becomes the description**. Nothing else to write.

<MultiLineNote>
Every framework has its own way of describing a tool to a model — LangChain reads the `@tool` decorator, other SDKs use their own format. MCP publishes the schema over the protocol instead, so a client written by someone else can read it without knowing anything about our code.
</MultiLineNote>

That docstring is the only thing telling the model *when* to reach for this tool, so write it for the model rather than for ourselves:

```python
"""Search jobs."""                                   # what does it need? when?

"""Search for real job openings requiring a specific skill in a
location. Use when the learner asks what roles are available."""   # a model can act on this
```

---

## How MCP Actually Works

We have just run `tools/list` against our own server and got back a schema. Consider what actually happened on the wire — because it explains why that twelve-line file was enough.

### A Small, Fixed Vocabulary

MCP runs on **JSON-RPC**. The name is new, but the idea is one we have used all course: a request carrying JSON, and a JSON reply. The difference from the REST APIs we have called is that the set of messages is fixed and small — the client asks one of a handful of questions, and the server answers.

Four exchanges carry almost everything:

![Four JSON-RPC exchanges between client and server: initialize returns the protocol version and server info, tools/list returns the schemas, tools/call returns content and structuredContent and isError, and resources/read returns a contents envelope](assets/mcp-wire-messages.png)

**1. `initialize` — "which version do we both speak, and who are you?"**

Every connection opens with this. The server we just built answers:

```
protocol_version: 2026-07-28
server_info: name='skillmap' version='1.0.0'
```

<MultiLineWarning text="This handshake is on its way out">

`initialize` is what the SDK does today, and what appeared in the Inspector. The newer spec revision removes the handshake — each request will carry its own version instead — but the Python SDK has not caught up. Learn the four exchanges as they are; just do not build anything that assumes a long-lived session.

</MultiLineWarning>

**2. `tools/list` — "what can you do?"**

This is the exchange we just ran. The client asks what exists; the server answers with names *and machine-readable schemas*. Right now that is one tool — by the end of Step 3 it will be three:

```
['skill_demand', 'search_jobs', 'save_learner_profile']
```

```json
{
  "type": "object",
  "properties": {
    "skill":    {"title": "Skill",    "type": "string"},
    "location": {"title": "Location", "type": "string"}
  },
  "required": ["skill", "location"],
  "title": "search_jobsArguments"
}
```

**3. `tools/call` — "run this one, with these arguments"**

```
isError=False  content=[TextContent(type='text', text='Saved profile for Anil.')]
```

**4. `resources/read` — "give me the contents of this URI"**

```json
{"name": "Anil", "skill": "Generative AI", "location": "Hyderabad"}
```

`prompts/get` and `resources/templates/list` follow the same shape: ask, answer.

### What Each Decorator Answers

Building a server is writing the answers to those four questions:

| We write | It answers |
|-----------|-----------|
| `@mcp.tool()` | `tools/list` (the schema) and `tools/call` (the work) |
| `@mcp.resource(...)` | `resources/read` |
| `@mcp.prompt()` | `prompts/get` |
| `version="1.0.0"` | part of `initialize` |

The SDK handles the JSON. Our job is deciding what those answers should be.

---

## Step 3: The Three Tools

One tool answers, so the hard part is behind us. The other two follow the same pattern.

The placeholder `skill_demand` from Step 2 is replaced by the real one here. Keep only the `if __name__` block at the bottom; everything above it is rewritten across this step and the next two.

**server.py — replace everything above `if __name__`**

```python
import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError

logger = logging.getLogger(__name__)

load_dotenv()
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
RAPIDAPI_KEY = os.environ.get("RAPID_API_KEY")

PROFILES = Path(__file__).parent / "profiles.json"

mcp = MCPServer("skillmap", version="1.0.0")
```

* Put the `.env` file **next to `server.py`**, holding `TAVILY_API_KEY` and `RAPID_API_KEY`. `load_dotenv()` looks relative to the script, so it is still found when a client launches the server from elsewhere.

* `ToolError` reports a failure the **model** should see. For now, read it as "fail with a message the model can act on" — *Structured Error Returns* explains why that matters.

A missing `.env` never raises: `load_dotenv()` returns quietly, and the failure surfaces much later as `TAVILY_API_KEY is not configured on the server`. Keep the bare call, and keep the file beside `server.py`.

<MultiLineWarning text="Use logging, not print()">

A stdio server uses **stdout** for the protocol — which is also where `print()` writes. From the [official guide](https://modelcontextprotocol.io/docs/develop/build-server):

> "Never write to stdout. Writing to stdout will corrupt the JSON-RPC messages and break the server."

Use `logging` instead. It writes to **stderr**, which is safe:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("searching jobs")
```

</MultiLineWarning>

All three follow the same shape: **guard the key → call the API → check the result → return, or `ToolError` with a reason.**

### Tool 1 — `skill_demand`

**server.py — add below the imports**

```python
@mcp.tool()
def skill_demand(skill: str) -> str:
    """Research industry demand, salary insights and career trends for a skill."""
    logger.info("skill_demand(%s)", skill)
    if not TAVILY_API_KEY:
        raise ToolError("TAVILY_API_KEY is not configured on the server.")

    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY,
                  "query": f"{skill} skills demand and salary 2026",
                  "max_results": 3, "search_depth": "basic"},
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("Tavily API call failed")
        raise ToolError(f"Could not reach the Tavily API: {type(e).__name__}") from e
    if r.status_code != 200:
        raise ToolError(f"Tavily search failed with status {r.status_code}.")

    results = r.json().get("results", [])
    if not results:
        raise ToolError(f"No demand information found for '{skill}'.")
    return "\n\n".join(f"{x['title']}\n{x['content'][:300]}" for x in results)
```

### Tool 2 — `search_jobs`

**server.py — add below `skill_demand`**

```python
@mcp.tool()
def search_jobs(skill: str, location: str) -> list[dict]:
    """Search for real job openings requiring a specific skill in a location."""
    logger.info("search_jobs(%s, %s)", skill, location)
    if not RAPIDAPI_KEY:
        raise ToolError("RAPID_API_KEY is not configured on the server.")

    try:
        r = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={"x-rapidapi-key": RAPIDAPI_KEY,
                     "x-rapidapi-host": "jsearch.p.rapidapi.com"},
            params={"query": f"{skill} in {location}", "page": "1",
                    "num_pages": "1", "country": "in"},
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("jobs API call failed")
        raise ToolError(f"Could not reach the jobs API: {type(e).__name__}") from e
    if r.status_code != 200:
        raise ToolError(f"Job search failed with status {r.status_code}.")

    jobs = r.json().get("data", [])
    if not jobs:
        raise ToolError(f"No {skill} jobs found in {location}.")
    return [{"title": j.get("job_title"), "company": j.get("employer_name"),
             "location": j.get("job_city"), "apply_link": j.get("job_apply_link")}
            for j in jobs[:5]]
```

### Tool 3 — `save_learner_profile`

This tool and the resource in Step 4 read the same file, so a one-line helper saves repeating it.

**server.py — add below `search_jobs`**

```python
def _load() -> dict:
    return json.loads(PROFILES.read_text()) if PROFILES.exists() else {}


@mcp.tool()
def save_learner_profile(user_id: str, name: str, skill: str, location: str) -> str:
    """Save a learner's career profile so it can be read back in future sessions."""
    logger.info("save_learner_profile(%s)", user_id)
    data = _load()
    data[user_id] = {"name": name, "skill": skill, "location": location}
    PROFILES.write_text(json.dumps(data, indent=2))
    return f"Saved profile for {name}."
```

<MultiLineWarning text="Notice who supplies the user_id">

`user_id` is an ordinary tool argument, so the **model** fills it in. Any client can then write any learner's profile — and read any other one back by guessing an id.

That is a change from the memory session, where `user_id` came from `runtime.context` and the model could never see or set it.

It is acceptable here for one reason: on **stdio** the server is a subprocess launched by one user on one machine, so the operating system is the boundary. Put it on a public URL and that boundary disappears.

The rule: **a tool argument is something the model can choose. Identity is not.** When a server serves more than one person, identity must arrive from the transport as a verified token.

</MultiLineWarning>

### Tool Descriptions Are Instructions the Model Follows

Identity is one direction of trust. There is a second, running the other way.

A tool's **description is text the model reads and acts on**. Connecting someone's MCP server means letting them put instructions into our agent's context — a different decision from installing a library that only our code calls. Tool **output** lands in that context too: `search_jobs` returns strings from a third-party API, untrusted by the time the model sees them.

The defences are out of scope today. But a server author who has never heard that a description *is* an instruction will eventually trust one that should not be trusted.

---

## Step 4: The Resource

Our three tools let the agent *act*. The learner's profile is different: it is something the agent needs to *know*.

A fourth tool would work, and would be wrong — the model would have to decide to ask for facts it should simply have been handed. The profile is data the application reads, not an action the model takes, so it is a **resource**.

**server.py — add below the tools**

```python
@mcp.resource("learner://profile/{user_id}", mime_type="application/json")
def learner_profile(user_id: str) -> str:
    """The saved career profile for one learner."""
    data = _load()
    if user_id not in data:
        raise ResourceNotFoundError(f"No profile saved for '{user_id}'.")
    return json.dumps(data[user_id], indent=2)
```

### Direct Resources vs Resource Templates

| | Direct resource | Resource template |
|---|---|---|
| URI | Fixed — `config://settings` | Parameterised — `learner://profile/{user_id}` |
| Listed by | `resources/list` | `resources/templates/list` |
| Use for | One specific thing | A family of things addressed by parameter |

Ours is a **template**: `{user_id}` is filled in by the client at read time. A client asking for the templates gets back exactly this:

```
[('learner://profile/{user_id}', 'application/json')]
```

Notes on the URI: `learner://` is a **custom scheme**, which the spec explicitly allows. `mime_type` tells the client how to interpret what comes back.

<MultiLineNote>
When a resource does not exist, the spec requires an error — **not** an empty result. An empty `contents` array is ambiguous: it could mean "exists but is empty" or "does not exist". Raising `ResourceNotFoundError` produces the correct error response.
</MultiLineNote>

---

## Step 5: The Prompt

We have built the two primitives the model and the application control. The third belongs to the **user**.

A prompt is a named template with parameters, which the user picks on purpose. It shows up in a client as a slash-command or a menu entry — not as something the model decides to call.

**server.py — add below the resource**

```python
@mcp.prompt()
def career_review(skill: str, location: str) -> str:
    """Ask for a structured career review for one skill and city."""
    return (f"I am learning {skill} and job-hunting in {location}.\n"
            f"1. Check current demand for {skill}.\n"
            f"2. Find openings in {location}.\n"
            f"3. Tell me the two skills I am most likely missing.")
```

Same pattern as before: the function name becomes the prompt name, the docstring becomes its description, and the parameters become its arguments. A client listing prompts sees:

```
name: career_review
description: Ask for a structured career review for one skill and city.
arguments: [('skill', True), ('location', True)]
```

Filling it in returns a ready-made message:

```
role: user
text: I am learning Generative AI and job-hunting in Hyderabad.
      1. Check current demand for Generative AI.
      2. Find openings in Hyderabad.
      3. Tell me the two skills I am most likely missing.
```

A prompt runs no code and calls no API. It is packaged wording — a good question, written once, that a user fires without retyping. Ours happens to describe using two of our tools, and the model decides to call them once the text arrives.

> Tools do work. Resources supply data. **Prompts supply intent.**

### Start the Server

Three tools, a resource and a prompt are registered. Add the lines that run it:

**server.py — at the bottom**

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Without them the file defines everything and then exits, and a client trying to launch it reports only a closed connection.

---

## Step 6: Testing With the MCP Inspector

The **MCP Inspector** is the official test client. `npx` runs it without installing anything, which also keeps it outside the server's environment — a broken install here cannot hide a failure there.

<MultiLineWarning text="Run these from inside skillmap-mcp/">

`uv run` works out which environment to use from the directory it is run in. Run the Inspector from anywhere else and the server starts without its libraries, or not at all — the Inspector reports only `Failed to connect` or `Connection closed`.

`cd skillmap-mcp` first. Every command below assumes it.

</MultiLineWarning>

**Terminal — what can the server do?**

```bash
npx @modelcontextprotocol/inspector --cli uv run server.py --method tools/list
```

**Terminal — call a tool**

```bash
npx @modelcontextprotocol/inspector --cli uv run server.py \
  --method tools/call --tool-name search_jobs \
  --tool-arg skill="Generative AI" --tool-arg location="Hyderabad"
```

**Terminal — save a profile, then read it back as a resource**

```bash
npx @modelcontextprotocol/inspector --cli uv run server.py \
  --method tools/call --tool-name save_learner_profile \
  --tool-arg user_id=learner_001 --tool-arg name=Anil \
  --tool-arg skill="Generative AI" --tool-arg location=Hyderabad

npx @modelcontextprotocol/inspector --cli uv run server.py \
  --method resources/read --uri "learner://profile/learner_001"
```

The resource comes back as an **envelope**, not as the dictionary:

```json
{
  "contents": [
    {
      "uri": "learner://profile/learner_001",
      "mimeType": "application/json",
      "text": "{\n  \"name\": \"Anil\",\n  \"skill\": \"Generative AI\"\n}"
    }
  ]
}
```

* **`contents` is an array** — one URI may return several pieces of content.
* **`mimeType`** is the one we declared on the decorator.
* **The JSON arrived as a string** inside `text`. The protocol carries text; the client parses it.

Drop `--cli` for a browser UI, or use `--tui` for a terminal one. Both talk to the server the same way.

<MultiLineNote>
Test a **failing** call as well as a working one — ask for a skill with no jobs, or read a profile that does not exist. Confirming a failure comes back as `isError: true` with a readable message, rather than crashing the server, is the part most people skip.
</MultiLineNote>

---

## Step 7: Connecting It to Our Own Agent

Full circle: the same client code from the **Integrating MCP** session, pointed at our own server.

The SkillMap Agent lives in Colab, and a Colab notebook cannot launch a local subprocess — so the client has to run locally too. That is the only reason for a new project here.

### Set Up the Client Project

**Terminal**

```bash
cd ..
uv init skillmap-client
cd skillmap-client
uv add langchain-mcp-adapters langchain langchain-google-genai python-dotenv
```

Copy the `.env` file here as well — the agent needs `GOOGLE_API_KEY`. Plain `uv init` again, for the same reason as Step 1: the client is also a project we only run, so it needs no build system.

Note the `cd ..` — the client is a **separate project**. Two folders now sit side by side, each with its own environment:

```
skillmap-mcp/       ← the server.  mcp 2.x
skillmap-client/    ← the agent.   mcp 1.x, via langchain-mcp-adapters
```

They have to be separate: `langchain-mcp-adapters` still requires `mcp<2.0.0`, so installing it into the server's project would downgrade the SDK the server is built on. That version gap is the point rather than a problem, and the end of this step explains why.

### Point the Client at the Server

**skillmap-client/agent.py**

```python
import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

SYSTEM_PROMPT = """You are a Skill-to-Career Mapping assistant that helps students
understand skill demand and find matching job opportunities."""

client = MultiServerMCPClient({
    "skillmap": {
        "transport": "stdio",
        "command": "uv",
        "args": ["--directory", "/abs/path/to/skillmap-mcp", "run", "server.py"],
    }
})


async def main():
    tools = await client.get_tools()
    print("tools:", [t.name for t in tools])

    model = init_chat_model("google_genai:gemini-2.5-flash",
                            api_key=os.environ["GOOGLE_API_KEY"])
    agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)

    response = await agent.ainvoke({"messages": [{"role": "user", "content":
        "Save my profile: I am Anil, learning Generative AI in Hyderabad, user id learner_002."}]})
    print(response["messages"][-1].text)


asyncio.run(main())
```

Replace `/abs/path/to/skillmap-mcp` with the real path to the server folder.

**Terminal**

```bash
uv run agent.py
```

```
tools: ['skill_demand', 'search_jobs', 'save_learner_profile']
Hello Anil! I've saved your profile. You are learning Generative AI and are located in Hyderabad.
```

The client started the server, discovered its three tools, and the model chose `save_learner_profile` on its own. Over HTTP only the connection entry changes:

```python
"skillmap": {"transport": "http", "url": "http://127.0.0.1:8000/mcp"}
```

<MultiLineWarning text="Why --directory, and why it goes before run">

`uv run` picks the environment from **the directory it is run in**, not from the path of the file we give it. The client runs in its own folder, so `uv run /abs/path/server.py` finds the file but starts it in the *client's* environment — where `mcp` is the wrong major version. The server exits immediately and the client reports only a closed connection.

`--directory` points uv at the project. It is a **uv** flag, so it goes *before* `run`.

</MultiLineWarning>

### What Changes in the SkillMap Agent

That `agent.py` is a fresh file. Here is the same move applied to the SkillMap Agent we already have.

**Before — every tool defined inside the agent**

```python
skill_demand_tool = TavilySearch(max_results=5, tavily_api_key=TAVILY_API_KEY)

@tool
def search_jobs(skill: str, location: str) -> list:
    """Search for jobs requiring a specific skill using the JSearch API."""
    ...                                   # ~30 lines of request and parsing

mcp_tools = await client.get_tools()
all_tools = mcp_tools + [search_jobs]

agent = create_agent(model=model, tools=all_tools, system_prompt=system_prompt)
```

**After — every tool from the server**

```python
client = MultiServerMCPClient({
    "skillmap": {
        "transport": "stdio",
        "command": "uv",
        "args": ["--directory", "/abs/path/to/skillmap-mcp", "run", "server.py"],
    }
})

tools = await client.get_tools()

agent = create_agent(model=model, tools=tools, system_prompt=system_prompt)
```

| Delete from the agent | Keep |
|---|---|
| The `TavilySearch` setup | The model |
| The `@tool def search_jobs` body | The system prompt |
| `TAVILY_API_KEY` and `RAPID_API_KEY` — the **server** holds them now | The agent loop itself |

The agent file gets shorter, and the keys move out of it. That is the change worth noticing: the agent no longer needs credentials for services it never calls directly.

### The Resource and the Prompt Too

Steps 4 and 5 are reachable from the client as well, not just the tools:

**skillmap-client/agent.py**

```python
# the resource, as a langchain Blob
res = await client.get_resources("skillmap", uris=["learner://profile/learner_001"])
print(res[0].data)

# the prompt, as ready-made chat messages
msgs = await client.get_prompt(
    "skillmap", "career_review",
    arguments={"skill": "Generative AI", "location": "Pune"},
)
print(msgs[0].content)
```

### Connecting It to a Coding Agent

A coding agent is a third kind of client, and needs no new code from us:

**Terminal**

```bash
claude mcp add --transport stdio skillmap -- \
  uv --directory /abs/path/to/skillmap-mcp run server.py
claude mcp get skillmap      # confirm it connected
```

Everything after `--` is the command that launches the server, passed through untouched. Register it for one developer (`local`), for the team via a committed `.mcp.json` (`project`), or across all projects (`user`).

---

## What Changed

We opened on `all_tools = mcp_tools + [search_jobs]`. That `+` joined two different worlds. It is gone — one `get_tools()` now returns all of them.

Notice what that just proved. The **server** runs on SDK 2.x; the **client** consuming it runs on SDK 1.x — a different major version that cannot even import the server's code. It works because they never share a Python process: the client launches the server, and from then on the only thing they agree on is the **messages**.

Here is what changed about `search_jobs`. The code inside it never moved:

| | Before this session | Now |
|---|---|---|
| Where it lives | Inside one program | A program with an address |
| A teammate needs it | Send the code, the keys, and instructions | Send one line of config |
| A coding assistant needs it | Not possible | `claude mcp add ...` |
| A bug is fixed | Every copy is now stale | Fix once; every client gets it |
| It needs a new capability | Update every copy | Add a tool; clients discover it |

None of that came from better code. It came from putting the same code behind a protocol.

> A custom tool gives **one** agent a capability. An MCP server gives **every** agent that capability.

---

### Final Code (server.py)

```python
"""SkillMap MCP server — 3 tools + 1 resource + 1 prompt."""
import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError

logger = logging.getLogger(__name__)          # stderr — keep your own output off stdout

load_dotenv()
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
RAPIDAPI_KEY = os.environ.get("RAPID_API_KEY")

PROFILES = Path(__file__).parent / "profiles.json"

mcp = MCPServer("skillmap", version="1.0.0")


def _load() -> dict:
    return json.loads(PROFILES.read_text()) if PROFILES.exists() else {}


@mcp.tool()
def skill_demand(skill: str) -> str:
    """Research industry demand, salary insights and career trends for a skill."""
    logger.info("skill_demand(%s)", skill)
    if not TAVILY_API_KEY:
        raise ToolError("TAVILY_API_KEY is not configured on the server.")
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY,
                  "query": f"{skill} skills demand and salary 2026",
                  "max_results": 3, "search_depth": "basic"},
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("Tavily API call failed")
        raise ToolError(f"Could not reach the Tavily API: {type(e).__name__}") from e
    if r.status_code != 200:
        raise ToolError(f"Tavily search failed with status {r.status_code}.")
    results = r.json().get("results", [])
    if not results:
        raise ToolError(f"No demand information found for '{skill}'.")
    return "\n\n".join(f"{x['title']}\n{x['content'][:300]}" for x in results)


@mcp.tool()
def search_jobs(skill: str, location: str) -> list[dict]:
    """Search for real job openings requiring a specific skill in a location."""
    logger.info("search_jobs(%s, %s)", skill, location)
    if not RAPIDAPI_KEY:
        raise ToolError("RAPID_API_KEY is not configured on the server.")
    try:
        r = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={"x-rapidapi-key": RAPIDAPI_KEY,
                     "x-rapidapi-host": "jsearch.p.rapidapi.com"},
            params={"query": f"{skill} in {location}", "page": "1",
                    "num_pages": "1", "country": "in"},
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("jobs API call failed")
        raise ToolError(f"Could not reach the jobs API: {type(e).__name__}") from e
    if r.status_code != 200:
        raise ToolError(f"Job search failed with status {r.status_code}.")
    jobs = r.json().get("data", [])
    if not jobs:
        raise ToolError(f"No {skill} jobs found in {location}.")
    return [{"title": j.get("job_title"), "company": j.get("employer_name"),
             "location": j.get("job_city"), "apply_link": j.get("job_apply_link")}
            for j in jobs[:5]]


@mcp.tool()
def save_learner_profile(user_id: str, name: str, skill: str, location: str) -> str:
    """Save a learner's career profile so it can be read back in future sessions."""
    logger.info("save_learner_profile(%s)", user_id)
    data = _load()
    data[user_id] = {"name": name, "skill": skill, "location": location}
    PROFILES.write_text(json.dumps(data, indent=2))
    return f"Saved profile for {name}."


@mcp.resource("learner://profile/{user_id}", mime_type="application/json")
def learner_profile(user_id: str) -> str:
    """The saved career profile for one learner."""
    data = _load()
    if user_id not in data:
        raise ResourceNotFoundError(f"No profile saved for '{user_id}'.")
    return json.dumps(data[user_id], indent=2)


@mcp.prompt()
def career_review(skill: str, location: str) -> str:
    """Ask for a structured career review for one skill and city."""
    return (f"I am learning {skill} and job-hunting in {location}.\n"
            f"1. Check current demand for {skill}.\n"
            f"2. Find openings in {location}.\n"
            f"3. Tell me the two skills I am most likely missing.")


if __name__ == "__main__":
    mcp.run(transport="stdio")
```


---

## Transports, Errors and Versioning

The server works and the agent consumes it. Three things still stand between this and something other people can rely on: how it is reached, how it fails, and how it changes.

---

### Transports — stdio vs HTTP

Right now the server is reachable by anything **on this laptop**, and nothing beyond it. That is a transport choice, not a code one.

A transport is only a **binding**. The JSON-RPC messages and the tools are identical either way — only how bytes travel changes.

![stdio runs the server as a local subprocess over pipes; Streamable HTTP runs it independently and clients POST to a URL](assets/mcp-transports.png)

| | **stdio** | **Streamable HTTP** |
|---|---|---|
| How it runs | The client launches it as a subprocess | Runs independently; clients POST to a URL |
| Who can reach it | Only the local machine | Anything that can reach the URL |
| Typically serves | One client | Many clients |
| Authentication | The OS process boundary | Bearer tokens, OAuth, headers |
| Use it for | Local tools, development | Shared and remote servers |

Switching is one argument:

**server.py — the run line**

```python
mcp.run(transport="streamable-http")   # instead of "stdio"
```

**The same `server.py` serves both.** Nothing in the tools changes. Running with HTTP prints:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

* The endpoint is **`/mcp`** — the full URL is `http://127.0.0.1:8000/mcp`
* It binds to **`127.0.0.1`**, not `0.0.0.0`, so nothing outside the machine can reach it
* `mcp.run()` also accepts `"sse"` — the older HTTP transport, for clients that predate Streamable HTTP

<MultiLineWarning text="Before putting a server on a public address">

There is no login step in what we have built: anyone who can reach the URL can call every tool. Two things the SDK does not add for us.

* **Authentication** — so the server knows who is calling
* **An `Origin` header check** — so a web page open in someone's browser cannot make their machine call the server

Both are out of scope today. Until then, keep it on `127.0.0.1`.

</MultiLineWarning>

---

### Structured Error Returns

MCP has **two** ways to report a failure, and they reach different audiences.

![A failing tool call can return a result with isError true which the model sees, or a JSON-RPC protocol error which only the client sees](assets/mcp-error-paths.png)

| | Tool execution error (`isError: true`) | Protocol error (JSON-RPC `error`) |
|---|---|---|
| Means | The tool ran; the work failed | The call itself was invalid |
| Examples | API rate-limited, no results found | Resource not found, malformed request |
| **Who sees it** | **The model** | **Only the client** |

> An execution error goes back to the model as text, so it can retry, adjust or explain. A protocol error does not — the model never learns why anything failed.

That is why our tools raise `ToolError` with a *descriptive* message. "No Generative AI jobs found in Atlantis" is something a model can act on. A generic crash is not.

Comment out `RAPID_API_KEY` in the `.env` file and call `search_jobs`:

```
is_error=True
content=[TextContent(type='text',
         text='Error executing tool search_jobs: RAPID_API_KEY is not configured on the server.')]
```

**Put the key back before moving on.**

#### Never Return an Error as a Normal Result

**The SDK only forwards the message when we raise `ToolError`.** Every other exception is caught and replaced with the tool's name and nothing else. Let a network timeout escape and the model receives:

```
is_error=True
content=[TextContent(type='text', text='Error executing tool search_jobs')]
```

No cause, nothing to retry against, nothing to tell the learner. Which is why the `try`/`except` around each HTTP call is not padding:

```python
try:
    r = requests.get(...)
except requests.RequestException as e:
    logger.exception("jobs API call failed")                 # keeps the traceback
    raise ToolError(f"Could not reach the jobs API: {type(e).__name__}") from e
```

* **`requests.RequestException`, not `Exception`** — catch only what the network throws, or a typo in our own code gets reported as a network fault
* **`logger.exception(...)`** — the model gets a sentence; the stack stays with us on stderr
* **`from e`** — the traceback shows what actually failed, not just where it was re-raised

The model now receives a cause it can act on:

```
text='Error executing tool search_jobs: Could not reach the jobs API: ConnectError'
```

> **An unhandled exception in an MCP tool is a silent error.**

#### Structured Output

Because `search_jobs` is annotated `-> list[dict]`, the SDK also sends the result as machine-readable `structured_content`, so clients can use it without parsing prose. The return type hint was all it took — there is nothing to add.

---

### Versioning

Two different versions are in play.

Clients report a `protocol_version` when they connect. The SDK negotiates it; there is nothing to set. **The version that matters to us is our server's own:**

```python
mcp = MCPServer("skillmap", version="1.0.0")
```

Clients see it as `serverInfo`. Because they **discover our tool schemas**, those schemas are a public contract:

| Change | Version bump | Why |
|--------|--------------|-----|
| Add a new tool | Minor — `1.1.0` | Existing calls keep working |
| Add an optional argument | Minor — `1.1.0` | Old calls still valid |
| Rename or remove a tool | **Major — `2.0.0`** | Existing clients break |
| Make an argument required | **Major — `2.0.0`** | Existing calls become invalid |

#### See It Break

Worth doing once. Check the contract first:

**Terminal**

```bash
npx @modelcontextprotocol/inspector --cli uv run server.py --method tools/list
```

Rename `location` to `city` in `search_jobs`, then re-run the *same* tool call from Step 6:

```python
def search_jobs(skill: str, city: str) -> list[dict]:   # was: location
```

```
is_error=True
Error executing tool search_jobs: 1 validation error for search_jobsArguments
city
  Field required [type=missing, input_value={'skill': 'Generative AI', 'location': 'Hyderabad'}, ...]
```

Run `tools/list` again: the published schema now says `city`. We edited a parameter, and the contract changed underneath every client that had already read it.

That is why the rename is a `2.0.0` and not a tidy-up. **Rename it back before continuing.**

---

## Starting a Server From Scratch

A future server will not be SkillMap. Here is the shape to start from — everything below is the
minimum that already does the right thing:

```python
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer("your-server-name", version="0.1.0")


@mcp.tool()
def your_tool(argument: str) -> str:
    """Say what this does AND when the model should use it."""
    try:
        result = do_the_work(argument)
    except Exception as e:                     # narrow this once you know what can fail
        logger.exception("your_tool failed")
        raise ToolError(f"Could not complete the request: {type(e).__name__}") from e
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
```

Four things are deliberate in those fifteen lines:

* **The version starts at `0.1.0`.** Below `1.0.0`, clients are told the schema is not stable yet — which is honest, and leaves room to rename things.
* **The `try`/`except` is already there.** Not as polish, but because an unconverted exception reaches the model as nothing useful (see Structured Error Returns). Start with it and it never has to be remembered — then narrow `Exception` to whatever the work actually raises, as we did with `requests.RequestException`.
* **The docstring says *when*, not just what.** That is the only guidance the model gets.
* **`transport="stdio"`** so a client can launch it immediately. Switch to `"streamable-http"` the day something remote needs it.

Then work outward in the order this session used: get `tools/list` answering, add one real tool, test the failing path, then a resource or prompt if one is needed.

---

---

## When Should We Build an MCP Server?

There are now four ways to give an agent a capability. Choosing well matters more than the syntax.

| Option | Reach for it when | What it costs |
|--------|-------------------|---------------|
| **Built-in tool** | Someone already solved it — Tavily search | Least control |
| **Custom `@tool`** | The logic belongs to *this one agent* | Not reusable outside it |
| **Reusable skill** | The agent needs a *procedure*, not a new capability | Only helps agents that read skills |
| **MCP server** | The capability must be reused **across** agents, apps or teams | A process to run and a schema to keep stable |

1. **Does it already exist?** → Use it. Do not rebuild Tavily.
2. **Is it private logic for one agent?** → A custom `@tool`.
3. **Is it instructions rather than capability?** → A skill.
4. **Do two or more clients need it?** → An MCP server.

An MCP server is a **deployable artifact with a public contract** — it has to run somewhere, stay up, and keep its schemas stable for every client that has discovered them. Worth it when several things need the same capability; a poor trade for a function only one agent will ever call.

> Build the `@tool` first. Promote it to a server when something else actually needs to connect.
