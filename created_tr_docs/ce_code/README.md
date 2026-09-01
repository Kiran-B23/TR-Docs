# Context Engineering — runnable code

| File | Backs | Needs an API key? | What it does |
|------|-------|-------------------|--------------|
| `skillmap_context_lab.py` | `../building-llm-applications--context-engineering-in-practice.md` | No | Builds the three-turn SkillMap conversation the doc measures, then prints every number the doc claims: token growth per turn, the 80% tool-output share, pruning at four `keep` values with fact retention, the context-poisoning demo, and all four "Try It Yourself" answers. Asserts the key figures so the doc cannot drift. |
| `verify_doc.py` | same doc | No | Extracts every `python` block from the doc, executes them in document order, and asserts each one's printed output matches the output block the doc shows beneath it. This is the test that the lab is runnable **as printed**. Step 7's block is skipped — it needs a live tool-calling model. |
| `proof_run.py` | same doc, Step 7 | **Yes** — Gemini, Tavily, JSearch | Runs four real turns twice, with and without pruning, and prints `input_tokens` per turn plus both turn-4 answers. This is the source for Step 7's output block, which is still unfilled: the Gemini free tier allows 20 requests/day and the quota was spent. Do not paste illustrative numbers there — capture a real run. |
| `verify_lab.py` | `../building-llm-applications--context-engineering.md` (the earlier, superseded draft) | No | Kept only while that draft is still on disk. Its numbers (2649 → 953) belong to that draft's RAG-chunk fixture, not to the SkillMap fixture used by the current doc. |

## Run

    cd created_tr_docs
    ./code/.venv/bin/python ce_code/skillmap_context_lab.py
    ./code/.venv/bin/python ce_code/verify_doc.py

## Expected output

`skillmap_context_lab.py` ends with `all assertions passed`. Its headline figures:

    after turn 1:  696 tokens        turn 2: 1290        turn 3: 1897
    tool output   1535  (80% of the window)
    pruning keep=1:  1897 -> 677 tokens  (64% smaller)

    keep  tokens   facts still in the window
       1     677   2/5
       2     907   3/5
       3    1180   4/5
       6    1897   5/5

`verify_doc.py` ends with `every runnable block in the doc executes and prints what
the doc says it prints`.

## Relationship to the doc

The doc's Step 0 defines `SYSTEM`, `demand()`, `jobs()` and `history()` inline, so a student
can work through the whole lab in a Colab notebook with nothing to download. This module
holds the same definitions plus the reports and assertions, and is the file to run when you
want to confirm the doc's numbers in one shot.

Keep the two in sync: if `history()` changes here, the doc's Step 0 block and every number
downstream of it change too. `verify_doc.py` is what catches that.

## Verified against

`langchain 1.3.17` · `langchain-core 1.6.0` · `langgraph 1.2.11` ·
`langchain-google-genai 4.3.5` · `langchain-tavily 0.2.18` · Python 3.12.3,
on 1 Sep 2026.

Nothing here needs a model. The pruning path is pure message-list manipulation, which is
why the whole lab — including the evaluation and poisoning sections — runs offline. The
`SummarizationMiddleware` wiring shown in the doc does need a model, and was exercised
separately.

## Two behaviours the doc depends on

**Pruning is request-only.** `ContextEditingMiddleware` implements `wrap_model_call`, so it
edits messages on their way to the model. The agent's stored history keeps the full tool
results. That is why the doc tells students to measure on the message list handed to the
edit, not by inspecting saved history.

**Compaction runs first, whatever the list order.** `SummarizationMiddleware` implements
`before_model`; `ContextEditingMiddleware` implements `wrap_model_call`. The before-model
hook is a graph node that runs ahead of the model call, so compaction always precedes
pruning regardless of the order passed to `middleware=[...]`. Verified by running an agent
with both orders and logging which hook fired first. Re-check if the middleware base class
changes.
