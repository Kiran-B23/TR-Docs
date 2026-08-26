"""Run the doc's Hands-On snippets exactly as written."""
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain.agents.middleware import ClearToolUsesEdit

big = "Retrieved chunk. " * 200
messages = [HumanMessage("start")]
for i in range(3):
    messages.append(AIMessage(content="", tool_calls=[
        {"name": "search_docs", "args": {"query": f"q{i}"}, "id": f"c{i}"}]))
    messages.append(ToolMessage(content=big, tool_call_id=f"c{i}"))

before = count_tokens_approximately(messages)
print("doc claims 2649 ->", before, "MATCH" if before == 2649 else "MISMATCH")

edit = ClearToolUsesEdit(trigger=500, keep=1, placeholder="[cleared]")
edit.apply(messages, count_tokens=count_tokens_approximately)
after = count_tokens_approximately(messages)
print("doc claims  953 ->", after, "MATCH" if after == 953 else "MISMATCH")
print("doc claims  64% ->", f"{100*(before-after)//before}%")
for i, m in enumerate(messages):
    if type(m).__name__ == "ToolMessage":
        print(f"  msg[{i}] ToolMessage -> {m.content[:50]!r}")

# the exercises must have real answers
for keep in (1, 2):
    ms = [HumanMessage("start")]
    for i in range(3):
        ms.append(AIMessage(content="", tool_calls=[{"name":"search_docs","args":{},"id":f"c{i}"}]))
        ms.append(ToolMessage(content=big, tool_call_id=f"c{i}"))
    ClearToolUsesEdit(trigger=500, keep=keep).apply(ms, count_tokens=count_tokens_approximately)
    print(f"exercise 1: keep={keep} -> {count_tokens_approximately(ms)} tokens")

ms = [HumanMessage("start")]
for i in range(3):
    ms.append(AIMessage(content="", tool_calls=[{"name":"search_docs","args":{},"id":f"c{i}"}]))
    ms.append(ToolMessage(content=big, tool_call_id=f"c{i}"))
ClearToolUsesEdit(trigger=100000, keep=1).apply(ms, count_tokens=count_tokens_approximately)
print("exercise 2: trigger=100000 ->", count_tokens_approximately(ms), "(unchanged = correct)")

ms = [HumanMessage("start")]
for i in range(3):
    ms.append(AIMessage(content="", tool_calls=[{"name":"search_docs","args":{},"id":f"c{i}"}]))
    ms.append(ToolMessage(content=big, tool_call_id=f"c{i}", name="search_docs"))
ClearToolUsesEdit(trigger=500, keep=1, exclude_tools=["search_docs"]).apply(ms, count_tokens=count_tokens_approximately)
print("exercise 3: exclude_tools ->", count_tokens_approximately(ms), "(unchanged = correct)")
