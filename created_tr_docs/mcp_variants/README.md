# MCP TR Doc Variants

Each variant applies one change on top of the previous, so you can compare any pair to see the isolated effect of a single change.

| Variant | Change | Lines | Effect |
|---------|--------|-------|--------|
| [Original](../building-llm-applications--build-your-own-mcp-server.md) | — | 1569 | Baseline |
| [variant-1](variant-1-reorder-protocol.md) | Move protocol mechanics after Step 2 | 1567 | Students write code before reading about JSON-RPC |
| [variant-2](variant-2-cut-interview-assistant.md) | Cut Interview Assistant; open with `+` directly | 1551 | Problem section grounded in code they wrote, not a scenario they're told about |
| [variant-3](variant-3-continuous-build.md) | Continuous build (Steps 1→7), conceptual after | 1554 | Uninterrupted build-to-payoff arc; "Going Deeper" section after |
| [variant-4](variant-4-compress-colab-transition.md) | Compress Colab→local transition | 1536 | ~15 lines instead of ~35; keeps the key point without the venv lecture |
| [variant-5](variant-5-all-changes.md) | Move payoff table before Final Code | 1536 | "What Changed" section is the climax; closing quote lives there |

## Variant 5 = all changes combined

The section order in variant 5:

```
Introduction
The Problem: Our Tools Do Not Travel        ← tightened (change 2)
Which Primitive, and Why
What We Are Building
Heads Up: We Are Leaving Colab              ← compressed (change 4)
Step 1: Project Setup
Step 2: The Smallest Server That Runs
How MCP Actually Works                      ← moved here from before build (change 1)
Step 3: The Three Tools
Step 4: The Resource
Step 5: The Prompt
Step 6: Testing With the MCP Inspector      ← was Step 8 (change 3)
Step 7: Connecting It to Our Own Agent      ← was Step 11 (change 3)
What Changed                                ← new climax section (change 5)
<details> Final Code
Going Deeper                                ← transports, errors, versioning, elicitation (change 3)
Starting Your Own Server
What We Are Not Covering
When Things Go Wrong
When Should You Build an MCP Server?
Check Your Understanding
Summary
```

## Known issue in variants 3 and 4

Variants 3 and 4 did not correctly apply change 1 — "How MCP Actually Works" stayed before the build steps instead of moving to after Step 2. This is fixed in variant 5.
