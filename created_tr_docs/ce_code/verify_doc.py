"""Extract every runnable python block from
`../building-llm-applications--context-engineering-in-practice.md`, execute them
in document order, and assert the printed numbers match the outputs the doc claims.

If this fails, the doc and the library have drifted apart.

Run:  ./code/.venv/bin/python ce_code/verify_doc.py
"""
import io, os, re, sys, textwrap, contextlib

DOC = os.path.join(os.path.dirname(__file__), "..",
                   "building-llm-applications--context-engineering-in-practice.md")
src = io.open(DOC, encoding="utf-8").read()

# ---- every python block, and the ``` output block that follows it (if any) ----
blocks = re.findall(r"```python\n(.*?)```(?:\s*\n *```\n(.*?)```)?", src, re.S)
# fences nested in a list item arrive indented; dedent before compiling
blocks = [(textwrap.dedent(c), textwrap.dedent(o or "")) for c, o in blocks]
runnable = [(code, out) for code, out in blocks if not code.lstrip().startswith("!pip")]
print(f"{len(blocks)} python blocks, {len(runnable)} runnable\n")

# ---- names the doc says are carried over from the memory session ----
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langchain.tools import tool
from dataclasses import dataclass


@dataclass
class Context:
    user_id: str


@tool
def skill_demand_tool(query: str) -> str:
    """Research industry demand, salary insights and career trends."""
    return "stub"


@tool
def search_jobs(skill: str, location: str) -> list:
    """Find job listings requiring a specific skill."""
    return []


@tool
def save_learner_profile(name: str) -> str:
    """Save the learner's profile."""
    return "saved"


@tool
def get_learner_profile() -> str:
    """Look up the learner's saved profile."""
    return "none"


@tool
def save_interaction(summary: str) -> str:
    """Record what happened this session."""
    return "recorded"


env = {
    "model": GenericFakeChatModel(messages=iter([AIMessage("ok")] * 50)),
    "SYSTEM_PROMPT": "You are a Skill Mapping assistant.",
    "store": InMemoryStore(),
    "checkpointer": InMemorySaver(),
    "Context": Context,
    "skill_demand_tool": skill_demand_tool,
    "search_jobs": search_jobs,
    "save_learner_profile": save_learner_profile,
    "get_learner_profile": get_learner_profile,
    "save_interaction": save_interaction,
    "__name__": "__doc_verify__",
}
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

failures = []
LIVE_ONLY = "agent.invoke"      # needs a real tool-calling model, not a stub

for i, (code, expected) in enumerate(runnable, 1):
    label = code.strip().splitlines()[0][:58]
    if LIVE_ONLY in code:
        print(f"  {i}: SKIPPED - needs a live model   [{label}]")
        continue
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, f"<doc block {i}>", "exec"), env)
    except Exception as e:
        failures.append(f"block {i} ({label}) raised {type(e).__name__}: {e}")
        print(f"  {i}: RAISED {type(e).__name__}: {e}")
        continue

    got = buf.getvalue()
    if not expected:
        print(f"  {i}: ran, no output block to check   [{label}]")
        continue

    # the doc elides long outputs with "..."; compare only the lines it shows
    shown = [ln for ln in expected.strip().splitlines() if ln.strip() != "..."]
    missing = [ln for ln in shown if ln.strip() and ln.strip() not in got]
    if missing:
        failures.append(f"block {i} ({label}) output mismatch: {missing}")
        print(f"  {i}: MISMATCH   [{label}]")
        for ln in missing:
            print(f"       doc claims: {ln.strip()}")
        print(f"       actually got:\n{got.rstrip()}")
    else:
        print(f"  {i}: output matches doc ({len(shown)} lines)   [{label}]")

print()
if failures:
    print("FAILED:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("every runnable block in the doc executes and prints what the doc says it prints")
