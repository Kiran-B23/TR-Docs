# Diagram assets

## Long-Term Memory
Four diagrams used by
`../building-llm-applications--33-building-memory-agents-long-term-memory.md`.

| File | Used in section |
|------|-----------------|
| `memory-namespace-key-value.png` | How Long-Term Memory Works Under the Hood → The Storage Layer |
| `memory-write-path.png` | → The Write Path |
| `memory-read-path.png` | → The Read Path |
| `memory-agent-context-loop.png` | → Injection: Memory Only Matters if it Reaches the Model (the **pull** shape) |

## Build Your Own MCP Server
Four diagrams used by `../building-llm-applications--build-your-own-mcp-server.md`.

| File | Used in section |
|------|-----------------|
| `mcp-host-client-server.png` | The Three Server Primitives |
| `mcp-wire-messages.png` | Step 2 → what JSON-RPC messages actually travel |
| `mcp-transports.png` | Step 6 → Transports: stdio vs HTTP |
| `mcp-error-paths.png` | Step 8 → Structured Error Returns |

## Context Engineering (old doc, set aside)
Seven diagrams referenced by `../building-llm-applications--context-engineering.md`.

| File | Used in section | Source |
|------|-----------------|--------|
| `ce-prompt-vs-context-engineering.png` | Let's Understand the Problem | third-party — **confirm licensing** |
| `ce-everything-is-context-engineering.png` | Performance Comparison | third-party — **confirm licensing** |
| `ce-agent-loop.png` | The Context Engineering Process → Agents | third-party — **confirm licensing** |
| `ce-six-types-of-context.png` | Context for AI Agents | **ours** — `ce-six-types-of-context.svg`, redrawn to replace an image carrying a visible `productcompass.pm` credit |
| `ce-agent-context-strategies.png` | Strategies and Tasks for Agents | third-party — **confirm licensing** |
| `ce-context-failure-modes.png` | Context Hygiene | third-party — **confirm licensing** |
| `ce-classic-prompting-techniques.png` | Principle 2 | third-party — **confirm licensing** |

The six PNGs marked third-party were extracted from the original Google Docs export
(`Context Engineering .md`, kept as the source of record). Only the six-types diagram has
been replaced so far; the rest still need provenance confirmed before publish.

## Before publishing
The doc currently points at **relative paths** (`assets/*.png`). Upload each PNG to the
content-loading store and replace the path with the returned URL, matching the pattern
already used elsewhere in the courseware:

    ![alt text](https://s3.ap-south-1.amazonaws.com/.../memory-write-path.png)

## Editing a diagram
The `.svg` files are the editable sources. Change the SVG, then re-render at 2x:

    google-chrome --headless --disable-gpu --no-sandbox --hide-scrollbars \
      --force-device-scale-factor=2 --screenshot=NAME.png \
      --window-size=W,H file:///path/to/wrapper.html

The wrapper must **inline** the SVG markup - an `<img src="...">` pointing at a path
containing a space silently renders a broken-image icon in headless Chrome:

    <html><head><style>html,body{margin:0;padding:0;background:#fff}
    svg{display:block}</style></head><body>  ...paste the SVG here...  </body></html>

Sizes: namespace-key-value 740x152 · write-path 780x150 · read-path 780x150 ·
agent-context-loop 860x335 · mcp-wire-messages 800x372


## Context Engineering in Practice
Five diagrams used by `../building-llm-applications--context-engineering-in-practice.md`.
All authored here — no third-party images, no licensing to confirm.

| File | Used in section | Source | Render size |
|------|-----------------|--------|-------------|
| `ce-context-growth.png` | The Problem | **ours** — `ce-context-growth.svg` | 800x348 |
| `ce-six-types-of-context.png` | The Context Stack | **ours** — reused, `ce-six-types-of-context.svg` | 800x400 |
| `ce-failure-modes.png` | How Context Fails | **ours** — `ce-failure-modes.svg` | 800x340 |
| `ce-four-techniques.png` | The Four Techniques | **ours** — `ce-four-techniques.svg` | 800x360 |
| `ce-pruning-before-after.png` | Hands-On → Technique 1 | **ours** — `ce-pruning-before-after.svg` | 800x330 |

`ce-context-growth` and `ce-pruning-before-after` carry live figures from
`../ce_code/skillmap_context_lab.py` (696/1290/1897, 1535 = 80%, 1897 -> 677 = 64%). If that
script's numbers change, re-render both.
