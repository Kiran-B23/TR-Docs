# Context Engineering in Practice — runnable code

Backs the **Hands-On: Pruning and Compaction on Your Own Agent** section of
`../building-llm-applications--context-engineering.md`.

| File | Needs an API key? | What it does |
|------|-------------------|--------------|
| `verify_lab.py` | No | Re-runs every snippet and number printed in the Hands-On section, plus the three "Try It Yourself" exercises, and asserts the token counts match the doc |

## Run

    ../code/.venv/bin/python verify_lab.py

## Expected output

    doc claims 2649 -> 2649 MATCH
    doc claims  953 ->  953 MATCH
    doc claims  64% -> 64%
      msg[2] ToolMessage -> '[cleared]'
      msg[4] ToolMessage -> '[cleared]'
      msg[6] ToolMessage -> 'Retrieved chunk. Retrieved chunk. ...'
    exercise 1: keep=1 ->  944 tokens
    exercise 1: keep=2 -> 1792 tokens
    exercise 2: trigger=100000 -> 2640 (unchanged = correct)
    exercise 3: exclude_tools    -> 2649 (unchanged = correct)

## Verified against

`langchain 1.3.17` · `langchain-core 1.6.0` · `langgraph 1.2.11` · Python 3.12.3,
on 26 Aug 2026. The pruning half needs no model; the `SummarizationMiddleware`
wiring shown in the doc does, and was exercised separately with
`gemini-3.1-flash-lite`.

## Note on behaviour

`ContextEditingMiddleware` edits messages on their way to the model. The agent's
stored history keeps the full tool results — confirmed by printing agent state after
a run. That is why the doc tells students to count tokens at the model call rather
than inspect saved history.
