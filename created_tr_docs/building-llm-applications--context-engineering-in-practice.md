# Context Engineering in Practice

**Course:** Building LLM Applications  
**Topic:** Introduction to Context Engineering and MCP  

---

**Key Takeaways:**

- **The Problem: A Long Conversation Makes the Agent Worse**
- **How the Context Window Actually Works**
    - **The Window Has Two Limits**
    - **What Follows From This**
- **What Context Engineering Is**
- **Context Engineering vs Prompt Engineering**
- **The Context Stack**
- **Memory Is Not Context**
- **How Context Fails**
    - **Context Poisoning**
    - **Context Distraction**
    - **Context Confusion**
    - **Context Clash**
- **The Four Techniques**
- **Four Principles for Managing Context**
    - **Principle 1: Minimal High-Quality Information**
    - **Principle 2: Smart System Prompts**
    - **Principle 3: Efficient Tool Design**
    - **Principle 4: Smart Information Retrieval**
- **How to Tell If It Worked**
- **Choosing the Right Approach**

---

# Introduction

In the previous units we built the **SkillMap Agent** with LangChain and Google Gemini. We gave it
tools for researching skill demand and finding jobs, then added memory so it recognises a learner
across sessions. Each addition put more information in front of the model.

Now in this unit, we will look at what all that information does to the model. We will watch a
working agent get worse as its context fills, see why that happens, and then meet **context
engineering** — the discipline of managing what the model reads. We will cover the four ways
context fails, and the four techniques and four principles for handling it.

---

# The Problem: A Long Conversation Makes the Agent Worse

Let's give the SkillMap Agent a harder test than usual. Not one question — four, in the same
conversation, the way a real learner would use it.

**Turn 1**

* **User**: "Find me Generative AI jobs in Hyderabad"
* **Agent**: *Researches demand, lists 5 openings with companies and apply links.*

**Turn 2**

* **User**: "Now AI Engineer roles in Bangalore"
* **Agent**: *Lists 5 more.*

**Turn 3**

* **User**: "And Machine Learning in Pune"
* **Agent**: *Lists 5 more.*

Perfect. The agent is doing exactly its job.

**Turn 4** — and this is the one that matters:

* **User**: "Of the Pune roles you just listed, which need less than 2 years experience?"
* **Agent**: *Runs the Pune search again from scratch. Or answers about Bangalore. Or drops the
  formatting rule it has followed for three turns.*

Everything the agent needs is already in its window. It just listed those roles. And yet.

## Why This Happens

Nothing broke. The tools work, the prompt is unchanged, the model is the same. What changed is how
much the model has to read to answer:

| | Turn 1 | Turn 4 |
|---|---|---|
| The question | One line | One line |
| The system prompt | Unchanged | Unchanged |
| **Tool results in the window** | **One search** | **Three searches, all re-sent** |

Every tool result from every earlier turn is still in the conversation, and all of it goes to the
model again on every new turn. By turn 3, **four fifths of what the model reads is search results
the learner has already moved past.**

> The agent did not get worse at its job. Its context got noisier.

<MultiLineNote>

**This is measured, not anecdotal.** Give a model a task all at once, then give it the same task
revealed turn by turn, and performance falls **39% on average** across six generation tasks — a
result that held for all 15 models tested, over 200,000 simulated conversations.

The interesting part is *how* it falls. Best-case ability drops only 15% — the model is barely
less capable. What rises is **unreliability, by 112%**. The same question can go well or badly
depending on what the conversation has accumulated. As the study puts it: when models take a wrong
turn, *they get lost and do not recover*.

</MultiLineNote>

---

# How the Context Window Actually Works

Behind that failure is one fact about how models work, and everything in this session follows
from it.

**An LLM remembers nothing between calls.** Each request is a blank slate. When the agent answers
turn 4, it is not recalling turn 1 — it is being *shown* turn 1 again, as text, along with
everything else that happened.

That is why the conversation grows. Nothing is being remembered. Everything is being re-sent.

> The window is not the model's short-term memory. It is the model's entire world for one call.

## The Window Has Two Limits

Everything sent to the model is counted in **tokens** — the pieces text is split into, which we
met in the **Understanding How LLMs Work** session. The window is measured in them, and it has two
different ceilings.

**The hard limit** is the model's maximum. Go past it and nothing degrades gracefully: the request
is rejected, or the client silently drops the oldest messages to make it fit. Either way the agent
stops behaving predictably, and the second case is worse because nothing tells us it happened.

**The soft limit** arrives much earlier, and it is the one that matters day to day. Accuracy
declines steadily as the window fills — attention is finite and spread across whatever we hand the
model. One page and it reads every line; fifty pages and everything gets skimmed. This decline has
a name: **context rot**.

It also has a shape. In the memory session we met **Lost in the Middle**: as input grows, models
reliably pay *less* attention to what sits in the middle of it. The beginning and the end are read
carefully; the middle is skimmed. A fact does not just compete for space — it competes for
position.

<MultiLineNote>

There is no safe token limit to design against. The drop-off depends on the model and the task. A
focused 300-token context can outperform an unfocused 100,000-token one.

</MultiLineNote>

## What Follows From This

Two consequences, and together they are the whole subject:

* **If it is not in the window, the model cannot use it.** No amount of clever prompting recovers
  a fact we left out.
* **If it is in the window, it takes space and attention from everything else** — including three
  turns of stale search results nobody asked about.

So the window is a budget with a failure at each end. Leave things out and the model cannot
answer. Put everything in and it answers badly, long before it runs out of room. Landing between
the two is not something the model does for us — it is a system we have to build.

Building that system has a name, and it is the subject of this session: **context engineering**.

---

# What Context Engineering Is

**Context engineering is filling the model's window with just the right information, in the right
format, at the right time to accomplish the task.**

It is not prompt writing done more carefully. A prompt is written once, by a person. Context is
assembled fresh on every single call, by the system — and on turn 40 nobody is choosing what goes
into it unless we built something that chooses.

Three things are packed into that sentence, and each is a separate decision:

* **The right information** — what goes in, and what stays out.
* **The right format** — how it is laid out, so the model can find what it needs inside it.
* **The right time** — when it enters the window, and when it leaves.

In plain terms: **it is deciding what the model gets to read, every time it reads.**

> Not the most context. Not the least. The most useful context per token spent.

## Why It Is Called Engineering

The term is new; the problem is old. An operating system has faced it for decades:

| Computer | AI agent |
|----------|----------|
| CPU | The LLM |
| RAM — limited | The context window — limited |
| The OS, deciding what is loaded into RAM | **Context engineering** |

A computer with the wrong things in RAM still runs. It just spends its time swapping instead of
working. Our agent on turn 4 was doing the same thing — still answering, but reading three
searches' worth of stale results to do it.

The analogy also sets the expectation. No operating system solves memory once and stops. It
decides continuously, as programs load and close. This is the same kind of job.

## But Windows Are Huge Now

A fair question at this point:

> "Models take a million tokens now. Why manage the window at all — why not put everything in?"

Three reasons:

* **Accuracy falls long before the window is full.** That is context rot, and it starts early.
* **Everything in the window competes.** A stale search result does not sit quietly beside the
  system prompt — it takes attention away from it.
* **A bigger window raises the ceiling, not the quality.** It changes how much noise the agent can
  carry, not how well it reasons through it.

---

# Context Engineering vs Prompt Engineering

Prompt engineering sits inside context engineering, not against it. The system prompt is one part
of the window; context engineering is about the whole window.

| | Prompt Engineering | Context Engineering |
|---|---|---|
| What it shapes | The wording of an instruction | Everything the model sees |
| When it happens | Once, when we write it | On every model call |
| Who does it | A person, editing text | The system, at runtime |
| The question it asks | "How do I phrase this?" | "What does the model need right now?" |
| It fails when | The instruction is unclear | The window is full of the wrong things |

Reach for **prompt engineering** on one-shot work: summarise this paragraph, classify this review,
translate this page. The prompt is the whole input, so better wording gives a better answer.

Reach for **context engineering** when the model is called repeatedly and each call inherits what
the last one left behind — agents, memory across sessions, tool use, multi-step workflows.

> Prompt engineering asks what we say to the model. Context engineering asks what the model is
> looking at when we say it.

---

# The Context Stack

Everything in the window competes for the same space. It helps to see it as layers:

| Layer | What it holds | Grows over time? |
|-------|---------------|------------------|
| **System prompt** | Role, rules, output format | No — fixed size |
| **Tool definitions** | Names, descriptions and schemas of every bound tool | No, but every tool added is permanent |
| **Retrieved knowledge** | RAG chunks, documents, search results | Yes |
| **Memory** | Facts carried across sessions | Yes |
| **Conversation history** | Every question, answer and tool result so far | **Yes — fastest** |
| **Current input** | The question just asked | No |

Two things follow.

**Only some layers grow.** The system prompt is the same size on turn 30 as on turn 1. Tool
descriptions are fixed too — but they are sent every turn whether used or not, so twenty tools is
a standing tax. Conversation history, and inside it tool output, is what runs away.

**The layers are not equally valuable per token.** The system prompt is small and shapes every
answer. A stale search result is large and shapes nothing.

> When the window gets tight, that ratio decides what to cut.

---

# Memory Is Not Context

Memory is a layer in that stack, and it is the one most easily confused with the window itself.
The memory session made half the point already: a new `thread_id` starts empty, so anything that
must survive has to live outside the conversation.

**Memory is what the agent stores. Context is what the model reads.**

| | Memory | Context |
|---|---|---|
| Where it lives | A store, outside the model | The window, inside one call |
| Lifespan | Across sessions | One call |
| Size | Effectively unlimited | Fixed and small |
| When the model sees it | Only when something retrieves it and puts it in the window | Always — all of it, every call |

The relationship runs one way. **A fact in the store changes nothing until something selects it
and places it in the window.** A store full of perfect facts about the learner has no effect on an
answer that never retrieves them.

That is what this session adds to the memory session. Memory is not an alternative to managing the
window — it is one of the tools for managing it. Writing a fact to the store is how we get it
*out* of the window while keeping it reachable.

> A bigger window lets an agent read more. Memory lets an agent know more. Only what is read
> changes the answer.

---

# How Context Fails

Context fails in two ways: because of **what is in it**, and because of **how much of it there
is**. Four named modes cover the first. None of them raises an error, which is why they are found
by reading transcripts, not logs.

## Context Poisoning

A wrong fact enters the window and is then treated as true by every later turn. Because the model
reads its own history, one early error becomes the premise for everything after it.

*In SkillMap:* one listing comes back with the wrong city, gets summarised into an answer, and the
agent keeps recommending it.

## Context Distraction

So much history accumulates that the model leans on the pattern of what it already did instead of
reasoning about the new question.

*In SkillMap:* turn 4 re-runs a search whose results are already sitting in the window.

## Context Confusion

Irrelevant content pulls the answer off target. The information is not wrong — it is just not what
this question is about.

*In SkillMap:* the learner asks about Pune and the answer includes Hyderabad roles, because those
results are still there.

## Context Clash

Two parts of the window disagree and nothing marks which is current.

*In SkillMap:* the learner said "internships" on turn 2 and "full-time roles" on turn 6. Both are
in the history. Both look equally true.

| Failure | How to fix it |
|---------|---------------|
| **Poisoning** | Check accuracy before saving · let only trusted sources write to memory |
| **Distraction** | **Compress** — prune old tool results, summarise old turns |
| **Confusion** | **Select** — retrieve only what fits the question · give tools clear, non-overlapping descriptions |
| **Clash** | **Write** — one value under one key, so the newer write replaces the older |

<MultiLineWarning text="These failures return confident answers">

None of the four produces an exception or a stack trace. The agent returns a well-formatted answer
that is simply worse than it should be. That is what makes them easy to ship.

</MultiLineWarning>

---

# The Four Techniques

Every fix is one of four moves. The useful way to hold them: **select** is the only one that puts
information *in*. The other three take it *out* — to a store, to a summary, or to another agent.

| Technique | What it does | Where we have met it |
|-----------|--------------|----------------------|
| **Write** | Save information outside the window, to read back later | The memory session — `save_learner_profile` writing to `InMemoryStore` |
| **Select** | Pull in only what this question needs | The RAG session — retrieve matching chunks, then answer |
| **Compress** | Shrink what is already in the window | This session's hands-on |
| **Isolate** | Split work so no single window holds all of it | Sub-agents, each with its own context |

**Compress has two forms**, and the difference decides which to reach for:

| | Pruning | Compaction |
|---|---|---|
| What it does | Removes content outright | Replaces content with a summary |
| Keeps meaning? | No | Yes |
| Costs a model call? | No | Yes |
| Best for | Stale tool output | Long conversations that still matter |

**Isolate** is the one we have not used yet. A sub-agent gets one focused task and its own window,
does the heavy reading, and returns only its conclusion. For SkillMap the natural split is
research: a sub-agent reads twenty listings and hands back a shortlist, so the raw listings never
enter the main conversation. The cost is that each sub-agent is its own set of model calls, and
sub-agents cannot see each other's work.

<MultiLineNote>

**Write** is also what settles a context clash. If "internships only" and "full-time roles" are
both in the history, the model has two equally current statements and no rule for choosing. Write
each preference to the store instead and there is one value under one key. The window stops being
where the argument happens.

</MultiLineNote>

---

# Four Principles for Managing Context

The four techniques are a **cure** — they act on a window that has already filled. These four
principles are the **prevention**.

## Principle 1: Minimal High-Quality Information

**Goal:** the minimum amount of high-quality information needed to finish the task.

Think of packing a suitcase. Do not pack the whole wardrobe. Pack what will actually be used, and
prefer versatile items.

| Instead of | Do this |
|---|---|
| Including an entire document | Highlight the key points |
| Keeping every old message | Summarise the ones that still matter |
| Providing 20 examples | Offer 3–5 diverse, clear ones |

## Principle 2: Smart System Prompts

Everything from the **Effective Prompting Techniques** session still applies. What changes in an
agent is that the system prompt is re-sent on **every turn**, and that has two consequences:

* **Its tokens are permanent.** A 500-token prompt occupies 500 tokens of every single turn,
  before anything useful is added. Tighten it once and the space comes back on every turn.
* **Its instructions compete.** Every rule added makes the others slightly less salient. A prompt
  with thirty rules is followed less reliably than one with six.

The goal is not the most complete system prompt. It is the smallest one that still produces the
behaviour we need.

| Tip | Why |
|-----|-----|
| Put must-never-break rules at the top | Instructions in the middle of a long context get the least attention |
| Say what to do, not only what to avoid | "Answer in one paragraph" beats "don't be verbose" |
| Cut anything the tools already say | A tool description that explains when to use it is paying twice |
| Re-read it periodically | Prompts accumulate rules added for one-off failures, and those rules never get removed |

### Pitch It at the Right Level

There are two ways to get a system prompt wrong, and they are opposites.

| Too rigid | Too vague |
|---|---|
| Hardcoded if-else logic for every case the agent might meet | "Be helpful and use good judgement" |
| Breaks on the first situation nobody anticipated | Gives the model nothing concrete to act on |

The target sits between them: **specific enough to guide behaviour, general enough to survive a
situation we did not predict.** Write heuristics, not branches.

### Give the Context a Shape

This is the *format* half of the definition. A wall of undifferentiated text is harder for a model
to use than the same text with its parts marked out.

* **Delineate the sections** — markdown headings or XML tags around background, instructions, tool
  guidance and output rules. The model can then tell an instruction from an example.
* **Prefer a few canonical examples to many edge cases.** Three to five diverse, clear examples
  teach the shape of a good answer better than twenty near-duplicates — and cost far fewer tokens.
  This is Principle 1 applied to examples.

The same applies to what tools return. A tool that hands back tidy, labelled fields is easier to
use than one that returns a raw dump, even when both contain the same facts.

## Principle 3: Efficient Tool Design

A tool's description and schema sit in the window every turn, used or not. Overlapping tools are
both a standing token cost and the direct cause of context confusion.

| Confusing | Clear |
|---|---|
| `search_documents` — searches everything | `search_document_by_keyword` — full-text search |
| `find_files` — also searches documents | `get_document_by_id` — fetch one known document |
| `query_database` — can also search documents | `list_recent_documents` — browse recent items |

A good tool has one clear purpose, a descriptive name, no overlap with its neighbours, and returns
focused results rather than a data dump. That last point is the one that bit us: `skill_demand`
and `search_jobs` return everything the API gives them.

## Principle 4: Smart Information Retrieval

This is **select**, stated as a design rule. The choice is *when* data enters the window.

| | Pre-load everything | Just-in-time retrieval |
|---|---|---|
| **Step 1** | User asks a question | User asks a question |
| **Step 2** | Search every source at once | The model works out what it actually needs |
| **Step 3** | Load it all into context | A tool fetches only that |
| **Step 4** | The model sifts through it | The model works on focused data |
| **Step 5** | — | If more is needed, repeat from step 2 |

A concrete case — *"What were our sales in Q3 2024 for Product X?"*

* **Pre-loading:** fetch all of 2024's sales, 10,000 rows, and let the model find the answer.
* **Just-in-time:** the model recognises what it needs, and a tool runs
  `SELECT * FROM sales WHERE quarter='Q3' AND year=2024 AND product='X'` — 50 rows come back.

Same answer. A fraction of the window, and nothing stale left behind for the next turn.

---

# How to Tell If It Worked

Every technique in this session removes something from the window. That makes them easy to
over-apply, because the token count improves either way — whether we cut noise or cut the answer.

So measure two numbers, never one:

| Measure | The question it answers |
|---|---|
| **Tokens in the window** | Did the change make room? |
| **Task success** | Can the agent still do the job? |

Task success needs to be concrete before the change, not judged after it. Fix a short list of
facts the agent must still be able to reach: the city the learner asked about, the most recent
search results, the preference stated on turn 2. Then check each one afterwards.

That list is what turns a setting into a decision. Keeping one recent tool result is cheaper than
keeping three, and which is right depends entirely on what the next question needs.

> A context change that reports only tokens saved is reporting half a result.

---

# Choosing the Right Approach

| Situation | Reach for | Why |
|-----------|-----------|-----|
| Tool results dominate the window | **Pruning** | Needs no model call, and they are usually stale |
| The conversation is long and still matters | **Compaction** | Keeps meaning that deleting would lose |
| A fact must survive across sessions | **Write** to a store | The window is not storage |
| The agent loads data it does not always need | **Select** — retrieve on demand | Nothing unused takes up space |
| One sub-task produces a lot and concludes briefly | **Isolate** in a sub-agent | Keeps the bulk out of the main window |

A short decision path:

1. **Measure first.** Find which layer of the stack is actually large. Optimising the wrong layer
   changes nothing.
2. **Try the fixes that need no model call.** Pruning and better tool design are the easiest to
   try and the easiest to undo.
3. **Then reach for compaction**, once there is meaning worth preserving.
4. **Reach for isolation last** — it is the largest change to the shape of the system.

<MultiLineNote>

The cheapest context fix is often not a technique at all. A tool that returns 5 fields instead of
50 keeps tokens out of the window in the first place. So does a system prompt that says what to
leave out. Nothing beats not adding them.

</MultiLineNote>

---

# Summary

| Idea | What to remember |
|------|------------------|
| Context engineering | Deciding what the model reads, on every call — not wording one prompt |
| The goal | The smallest set of high-signal tokens that gets the job done |
| The context stack | System prompt, tools, retrieved knowledge, memory, history, current input |
| What grows | Conversation history, and inside it tool output |
| Why it is needed | An LLM remembers nothing between calls. The window is its entire world for one call |
| Memory vs context | Memory is what the agent stores; context is what the model reads. A stored fact does nothing until something puts it in the window |
| The window's two limits | A hard maximum that truncates or rejects, and a soft decline (context rot) that starts long before it |
| Four failure modes | Poisoning, distraction, confusion, clash — none of which raise an error |
| Four techniques | Write, select, compress, isolate — only select adds |
| Four principles | Minimal information, smart system prompts, efficient tools, just-in-time retrieval |

The line worth carrying forward:

> A bigger context window is not a fix. It just raises the ceiling on how much noise the agent can
> carry.

---

# Further Reading

* <a href="https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents" target="_blank">Effective context engineering for AI agents</a>
* <a href="https://research.trychroma.com/context-rot" target="_blank">Context Rot: how increasing input tokens impacts LLM performance</a>
* <a href="https://arxiv.org/abs/2505.06120" target="_blank">LLMs Get Lost in Multi-Turn Conversation</a>
* <a href="https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html" target="_blank">How long contexts fail, and how to fix them</a>
* <a href="https://www.langchain.com/blog/context-engineering-for-agents" target="_blank">Context Engineering for Agents</a>
* <a href="https://www.elastic.co/search-labs/blog/context-engineering-overview" target="_blank">What is Context Engineering?</a>
* <a href="https://www.datacamp.com/blog/context-engineering" target="_blank">Context Engineering: A Guide With Examples</a>
* <a href="https://sourcegraph.com/blog/context-engineering" target="_blank">Context Engineering</a>
* <a href="https://www.promptingguide.ai/guides/context-engineering-guide" target="_blank">Context Engineering Guide</a>
* <a href="https://aiengineeringfromscratch.com/lesson?path=phases%2F11-llm-engineering%2F05-context-engineering&amp;learningPath=agentic-ai-engineer" target="_blank">Context Engineering — AI Engineering From Scratch</a>
