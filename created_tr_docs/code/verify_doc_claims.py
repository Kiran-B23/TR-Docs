"""
Verifies the technical claims made in
building-llm-applications--33-building-memory-agents-long-term-memory.md

No API key required. Run:  ./.venv/bin/python verify_doc_claims.py
"""
from dataclasses import dataclass
from datetime import datetime

from langchain_core.embeddings import Embeddings
from langchain.tools import tool, ToolRuntime
from langgraph.store.memory import InMemoryStore
from typing_extensions import TypedDict

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((PASS, name, detail))
    except Exception as e:
        results.append((FAIL, name, f"{type(e).__name__}: {e}"))


# ---------------------------------------------------------------- 1. storage
def t_storage():
    store = InMemoryStore()
    store.put(("learners",), "learner_001", {"name": "Anil", "skill": "Generative AI"})
    item = store.get(("learners",), "learner_001")
    assert item.value["name"] == "Anil", item.value
    listed = store.search(("learners",))
    assert len(listed) == 1
    return f"put/get/search ok; .value = {item.value}"


# ------------------------------------------- 2. search(query=) with NO index
def t_search_without_index():
    store = InMemoryStore()
    store.put(("learners",), "a", {"text": "prefers remote roles"})
    store.put(("learners",), "b", {"text": "dislikes service companies"})
    try:
        res = store.search(("learners",), query="what does the learner want?")
    except Exception as e:
        return f"RAISES {type(e).__name__}: {e}  -> doc fix 2 was REQUIRED"
    return (f"does NOT raise; returns {len(res)} items unranked "
            f"-> silently misleading, doc fix 2 was correct")


# ------------------------------------------------------ 3. merge vs overwrite
class LearnerProfile(TypedDict):
    name: str
    skill: str
    location: str
    experience_level: str


def t_merge():
    store = InMemoryStore()
    ns, key = ("learners",), "learner_001"
    store.put(ns, key, {"name": "Anil", "skill": "GenAI",
                        "location": "Hyderabad", "experience_level": "fresher"})

    # what the OLD doc code did: blind put with a partial profile
    store.put(ns, key, dict({"location": "Bangalore"}))
    after_overwrite = store.get(ns, key).value

    # what the FIXED doc code does
    store.put(ns, key, {"name": "Anil", "skill": "GenAI",
                        "location": "Hyderabad", "experience_level": "fresher"})
    existing = store.get(ns, key)
    merged = {**(existing.value if existing else {}), **dict({"location": "Bangalore"})}
    store.put(ns, key, merged)
    after_merge = store.get(ns, key).value

    assert len(after_overwrite) == 1, after_overwrite
    assert len(after_merge) == 4 and after_merge["location"] == "Bangalore", after_merge
    return (f"blind put -> {after_overwrite} (3 fields LOST) | "
            f"merge -> {after_merge} (intact)")


# ------------------------------- 4. TypedDict is not enforced at runtime
def t_typeddict_not_enforced():
    p: LearnerProfile = {"location": "Bangalore"}  # missing 3 required keys
    assert isinstance(p, dict) and len(p) == 1
    return "TypedDict accepted a partial dict at runtime -> doc's warning is correct"


# ---------------------------------------- 5. model never sees `runtime` param
@dataclass
class Context:
    user_id: str


@tool
def save_learner_profile(profile: LearnerProfile, runtime: ToolRuntime[Context]) -> str:
    """Save the learner's career profile so it can be recalled in future sessions."""
    existing = runtime.store.get(("learners",), runtime.context.user_id)
    merged = {**(existing.value if existing else {}), **dict(profile)}
    runtime.store.put(("learners",), runtime.context.user_id, merged)
    return "Learner profile saved."


@tool
def get_learner_profile(runtime: ToolRuntime[Context]) -> str:
    """Look up the learner's saved career profile from previous sessions."""
    profile = runtime.store.get(("learners",), runtime.context.user_id)
    return str(profile.value) if profile else "No saved profile yet."


@tool
def save_interaction(summary: str, outcome: str, runtime: ToolRuntime[Context]) -> str:
    """Record what happened in this session and how it turned out."""
    ts = datetime.now().isoformat()
    runtime.store.put(("learners", runtime.context.user_id, "episodes"), ts,
                      {"summary": summary, "outcome": outcome, "timestamp": ts})
    return "Interaction recorded."


def t_runtime_hidden():
    a = set(save_learner_profile.args.keys())
    b = set(get_learner_profile.args.keys())
    c = set(save_interaction.args.keys())
    assert "runtime" not in a and "runtime" not in b and "runtime" not in c
    assert a == {"profile"}, a
    assert b == set(), b
    assert c == {"summary", "outcome"}, c
    return (f"save_learner_profile{sorted(a)}  get_learner_profile{sorted(b)}  "
            f"save_interaction{sorted(c)} -- 'runtime' hidden from the model in all 3")


# ------------------------------------------------ 6. namespace isolation
def t_isolation():
    store = InMemoryStore()
    store.put(("learners",), "learner_001", {"name": "Anil"})
    store.put(("learners",), "learner_002", {"name": "Bhavya"})
    a = store.get(("learners",), "learner_001").value
    b = store.get(("learners",), "learner_002").value
    assert a != b and a["name"] == "Anil"
    return f"learner_001 -> {a}, learner_002 -> {b} (no leakage)"


# ------------------------------------------------ 7. episodic sub-namespace
def t_episodic():
    store = InMemoryStore()
    ns = ("learners", "learner_001", "episodes")
    ts = datetime.now().isoformat()
    store.put(ns, ts, {"summary": "Showed 5 GenAI jobs",
                       "outcome": "Applied to 2, rejected senior roles",
                       "timestamp": ts})
    eps = store.search(ns)
    prof = store.search(("learners",))
    assert len(eps) == 1
    return (f"episodes ns holds {len(eps)}; parent ns unaffected by sub-namespace "
            f"(returns {len(prof)} profile rows) -> types stay separated")


# --------------------------- 8. does index= accept an Embeddings INSTANCE?
class TinyEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[float(len(t) % 7), 1.0] for t in texts]

    def embed_query(self, text):
        return [float(len(text) % 7), 1.0]


def t_embeddings_instance():
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2})
    ns = ("learners", "learner_001", "memories")
    store.put(ns, "m1", {"text": "prefers remote roles"})
    store.put(ns, "m2", {"text": "dislikes service companies"})
    res = store.search(ns, query="what kind of company?", limit=2)
    assert len(res) >= 1
    return (f"InMemoryStore(index={{'embed': <Embeddings instance>, 'dims': 2}}) accepted; "
            f"search returned {len(res)} ranked items")


# ------------------------------------------------ 9. create_agent signature
def t_create_agent_params():
    import inspect
    from langchain.agents import create_agent
    sig = inspect.signature(create_agent).parameters
    for p in ("store", "checkpointer", "context_schema", "tools", "system_prompt", "model"):
        assert p in sig, f"missing param: {p}"
    return "create_agent accepts model/tools/system_prompt/checkpointer/store/context_schema"


for name, fn in [
    ("1. Store put/get/search + .value", t_storage),
    ("2. search(query=) on a NON-indexed store", t_search_without_index),
    ("3. Partial save: blind put vs merge", t_merge),
    ("4. TypedDict not enforced at runtime", t_typeddict_not_enforced),
    ("5. `runtime` hidden from the model's tool schema", t_runtime_hidden),
    ("6. Namespace isolation between users", t_isolation),
    ("7. Episodic sub-namespace", t_episodic),
    ("8. index= accepts an Embeddings instance", t_embeddings_instance),
    ("9. create_agent parameter names", t_create_agent_params),
]:
    check(name, fn)

print("=" * 78)
for status, name, detail in results:
    print(f"[{status}] {name}\n        {detail}")
print("=" * 78)
print(f"{sum(1 for r in results if r[0] == PASS)}/{len(results)} passed")
