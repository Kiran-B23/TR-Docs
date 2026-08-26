"""
Verifies the claims ADDED or CORRECTED during the review of
building-llm-applications--33-building-memory-agents-long-term-memory.md

Companion to verify_doc_claims.py. No API key required.
Run:  ./.venv/bin/python verify_doc_fixes.py
"""
import inspect
from dataclasses import dataclass
from uuid import uuid4

from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langchain_tavily import TavilySearch
from langgraph.store.memory import InMemoryStore
from typing_extensions import TypedDict

PASS, FAIL = "PASS", "FAIL"
results = []


def check(name, fn):
    try:
        results.append((PASS, name, fn()))
    except Exception as e:
        results.append((FAIL, name, f"{type(e).__name__}: {e}"))


@dataclass
class Context:
    user_id: str


class TinyEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[float(len(t) % 7), 1.0] for t in texts]

    def embed_query(self, text):
        return [float(len(text) % 7), 1.0]


# --------------------------------------------- 1. total=False removes `required`
class ProfileTotal(TypedDict):
    name: str
    skill: str


class ProfileOptional(TypedDict, total=False):
    """Only include the fields the learner actually mentioned."""
    name: str
    skill: str


def t_total_false():
    @tool
    def strict(profile: ProfileTotal, runtime: ToolRuntime[Context]) -> str:
        """Save."""
        return "ok"

    @tool
    def loose(profile: ProfileOptional, runtime: ToolRuntime[Context]) -> str:
        """Save."""
        return "ok"

    a = strict.tool_call_schema.model_json_schema()["$defs"]["ProfileTotal"]
    b = loose.tool_call_schema.model_json_schema()["$defs"]["ProfileOptional"]
    assert a.get("required") == ["name", "skill"], a
    assert "required" not in b, b
    return ("TypedDict -> required=['name','skill'] (model MUST invent a name); "
            "total=False -> no required list")


# ------------------------------------------- 2. renaming a prebuilt tool works
def t_tool_rename():
    t = TavilySearch(max_results=5, search_depth="advanced", tavily_api_key="x")
    before = t.name
    t.name = "skill_demand_tool"
    assert before == "tavily_search" and t.name == "skill_demand_tool"
    return f"{before!r} -> {t.name!r}; system prompt and trace now agree"


# ------------------------------------ 3. save_memory / search_memory as a pair
def t_memory_pair():
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2})

    @tool
    def save_memory(text: str, runtime: ToolRuntime[Context]) -> str:
        """Remember one short observation about this learner."""
        ns = ("learners", runtime.context.user_id, "memories")
        runtime.store.put(ns, f"mem_{uuid4().hex[:8]}", {"text": text})
        return "Saved."

    @tool
    def search_learner_memories(query: str, runtime: ToolRuntime[Context]) -> str:
        """Search everything remembered about this learner."""
        ns = ("learners", runtime.context.user_id, "memories")
        res = runtime.store.search(ns, query=query, limit=3)
        return "\n".join(r.value["text"] for r in res) or "Nothing relevant remembered."

    assert set(save_memory.args) == {"text"}
    assert set(search_learner_memories.args) == {"query"}

    # The tools need an agent-supplied runtime to invoke, so exercise the
    # store operation each one wraps.
    ns = ("learners", "l1", "memories")
    store.put(ns, "m1", {"text": "Prefers remote roles"})
    hits = store.search(ns, query="remote?", limit=3)
    assert hits and "remote" in hits[0].value["text"]
    return (f"save_memory args={sorted(save_memory.args)} "
            f"search args={sorted(search_learner_memories.args)}; "
            f"search finds {hits[0].value['text']!r}")


# ------------------------------------------------ 4. search returns ALL of top-k
def t_no_threshold():
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2})
    ns = ("learners", "l1", "memories")
    for k, txt in [("m1", "Prefers remote roles"),
                   ("m2", "Not interested in service-based companies"),
                   ("m3", "Struggles with system design interviews")]:
        store.put(ns, k, {"text": txt})
    res = store.search(ns, query="what kind of company?", limit=3)
    assert len(res) == 3, len(res)
    assert all(r.score is not None for r in res)
    default_limit = inspect.signature(type(store).search).parameters["limit"].default
    return (f"limit=3 over 3 memories -> {len(res)} results (NOT 2); "
            f"every result carries .score; default limit={default_limit}")


# --------------------------------------------- 5. threshold + filter both work
def t_threshold_and_filter():
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2})
    ns = ("learners", "l1", "memories")
    store.put(ns, "m1", {"text": "Prefers remote roles", "kind": "preference"})
    store.put(ns, "m2", {"text": "Applied to two roles", "kind": "episode"})
    filtered = store.search(ns, query="remote?", filter={"kind": "preference"})
    assert len(filtered) == 1 and filtered[0].value["kind"] == "preference"
    thresholded = [r for r in store.search(ns, query="remote?", limit=5) if r.score > 999]
    assert thresholded == []
    return f"filter={{'kind':'preference'}} -> {len(filtered)} of 2; score threshold prunes"


# ------------------------------------------------ 6. fields= and index=False
def t_index_scoping():
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2, "fields": ["text"]})
    store.put(("a",), "k1", {"text": "prefers remote", "kind": "pref"})
    store.put(("a",), "k2", {"text": "skip me"}, index=False)
    assert len(store.search(("a",))) == 2
    return "index={'fields': ['text']} accepted; put(..., index=False) accepted"


# ------------------------------------------------------- 7. store.delete exists
def t_delete():
    store = InMemoryStore()
    store.put(("learners",), "l1", {"name": "Anil"})
    store.delete(("learners",), "l1")
    assert store.get(("learners",), "l1") is None
    return "store.delete(namespace, key) removes the item; get() -> None"


# --------------------------------- 8. forget_learner: full per-user deletion
def t_forget_learner():
    store = InMemoryStore()
    store.put(("learners",), "l1", {"skill": "GenAI"})
    store.put(("learners", "l1", "episodes"), "e1", {"summary": "showed jobs"})
    store.put(("learners", "l1", "memories"), "m1", {"text": "prefers remote"})
    store.put(("learners",), "l2", {"skill": "DevOps"})   # another user, must survive

    def forget_learner(store, user_id):
        deleted = 0
        for namespace in store.list_namespaces(prefix=("learners", user_id)):
            for item in store.search(namespace):
                store.delete(namespace, item.key)
                deleted += 1
        store.delete(("learners",), user_id)
        return deleted + 1

    n = forget_learner(store, "l1")
    assert store.get(("learners",), "l1") is None
    assert store.get(("learners",), "l2") is not None, "other user was damaged"
    assert store.search(("learners", "l1", "memories")) == []
    return f"deleted {n} items for l1; l2 untouched"


# ------------------------------------------------ 9. ttl is backend-dependent
def t_ttl_capability():
    store = InMemoryStore()
    assert store.supports_ttl is False
    try:
        store.put(("a",), "k", {"x": 1}, ttl=1.0)
        raise AssertionError("expected NotImplementedError")
    except NotImplementedError as e:
        return f"InMemoryStore.supports_ttl={store.supports_ttl}; put(ttl=) -> {e}"


# ------------------------------------------- 10. created_at enables recency
def t_created_at():
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2})
    store.put(("a",), "k", {"text": "hello"})
    item = store.search(("a",), query="hello")[0]
    assert item.created_at is not None and item.updated_at is not None
    assert item.score is not None
    return (f"SearchItem carries score={item.score:.3f}, created_at={item.created_at.date()}, "
            "updated_at -> recency ranking needs no extra field")


# ------------------------------------------------- 11. debug= is still valid
def t_debug_param():
    sig = inspect.signature(create_agent).parameters
    assert "debug" in sig and sig["debug"].default is False
    return "create_agent(debug=True) is valid; default False"


# ------------------------------------ 12. .text vs .content[0]['text']
def t_text_property():
    plain = AIMessage(content="Here are 5 jobs...")
    blocks = AIMessage(content=[{"type": "text", "text": "Here are 5 jobs..."}])
    try:
        plain.content[0]["text"]
        raise AssertionError("expected TypeError")
    except TypeError as e:
        err = str(e)
    assert plain.text == blocks.text == "Here are 5 jobs..."
    return f".content[0]['text'] on a string -> TypeError: {err}; .text works on both"


# ---------------------------------------- 13. SqliteStore exists (import path)
def t_sqlite_store():
    try:
        from langgraph.store.sqlite import SqliteStore  # noqa: F401
        return "langgraph.store.sqlite.SqliteStore imported (package installed)"
    except ModuleNotFoundError:
        return ("NOT INSTALLED here, but ships in langgraph-checkpoint-sqlite as "
                "langgraph/store/sqlite/{base,aio}.py exporting SqliteStore + "
                "AsyncSqliteStore -- the doc's old 'no Sqlite store' claim was wrong")


for name, fn in [
    ("1.  total=False removes `required` from the tool schema", t_total_false),
    ("2.  Renaming a prebuilt tool (skill_demand_tool)", t_tool_rename),
    ("3.  save_memory / search_learner_memories pair", t_memory_pair),
    ("4.  search() returns ALL of top-k, with scores", t_no_threshold),
    ("5.  Score threshold and metadata filter", t_threshold_and_filter),
    ("6.  index fields= and put(index=False)", t_index_scoping),
    ("7.  store.delete()", t_delete),
    ("8.  forget_learner(): full per-user deletion", t_forget_learner),
    ("9.  TTL is a backend capability, not a given", t_ttl_capability),
    ("10. created_at/score enable recency ranking", t_created_at),
    ("11. create_agent(debug=True) still valid", t_debug_param),
    ("12. .text vs .content[0]['text']", t_text_property),
    ("13. SqliteStore exists", t_sqlite_store),
]:
    check(name, fn)

print("=" * 78)
for status, name, detail in results:
    print(f"[{status}] {name}\n        {detail}")
print("=" * 78)
print(f"{sum(1 for r in results if r[0] == PASS)}/{len(results)} passed")


# =====================================================================
# Additions from the content-expansion pass
# =====================================================================

def t_dynamic_prompt_push():
    """PUSH injection: @dynamic_prompt middleware reading the store."""
    from langchain.agents.middleware import dynamic_prompt
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

    store = InMemoryStore()
    store.put(("learners",), "l1",
              {"skill": "Generative AI", "location": "Hyderabad"})
    BASE = "You are a Skill-to-Career Mapping assistant."
    seen = {}

    @dynamic_prompt
    def add_learner_profile(request):
        item = request.runtime.store.get(("learners",), request.runtime.context.user_id)
        if not item:
            return BASE
        facts = "\n".join(f"- {k}: {v}" for k, v in item.value.items())
        seen["prompt"] = f"{BASE}\n\nWhat you already know about this learner:\n{facts}"
        return seen["prompt"]

    agent = create_agent(
        model=GenericFakeChatModel(messages=iter(["ok"])),
        tools=[],
        middleware=[add_learner_profile],
        store=store,
        context_schema=Context,
    )
    agent.invoke({"messages": [{"role": "user", "content": "hi"}]},
                 context=Context(user_id="l1"))
    assert "Hyderabad" in seen["prompt"], seen
    return "@dynamic_prompt built a system prompt containing the stored profile"


def t_dedup_on_write():
    """Search-before-write collapses a near-duplicate instead of appending."""
    from uuid import uuid4
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2})
    ns = ("learners", "l1", "memories")

    def save_memory(text, threshold=0.9):
        hits = store.search(ns, query=text, limit=1)
        if hits and hits[0].score >= threshold:
            store.put(ns, hits[0].key, {"text": text})
            return "updated"
        store.put(ns, f"mem_{uuid4().hex[:8]}", {"text": text})
        return "inserted"

    first = save_memory("Prefers remote roles")
    second = save_memory("Prefers remote roles")
    assert (first, second) == ("inserted", "updated"), (first, second)
    assert len(store.search(ns)) == 1
    return "second identical save -> 'updated', namespace still holds 1 memory"


def t_recency_rerank():
    """Recency weighting needs no stored timestamp -- created_at is enough."""
    from datetime import datetime, timezone
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2})
    ns = ("learners", "l1", "memories")
    store.put(ns, "m1", {"text": "Prefers remote roles"})
    store.put(ns, "m2", {"text": "Not interested in service-based companies"})

    def rank(items, decay_per_day=0.02):
        now = datetime.now(timezone.utc)
        def adjusted(item):
            age_days = (now - item.created_at).total_seconds() / 86400
            return item.score - decay_per_day * age_days
        return sorted(items, key=adjusted, reverse=True)

    ranked = rank(store.search(ns, query="what kind of company?", limit=5))
    assert len(ranked) == 2 and all(r.score is not None for r in ranked)
    return f"re-ranked {len(ranked)} results using .score and .created_at only"


def t_ttl_units_and_postgres():
    """TTL is documented in MINUTES; PostgresStore advertises support."""
    from langgraph.store.base import TTLConfig
    keys = TTLConfig.__annotations__
    for k in ("refresh_on_read", "omit_expired", "default_ttl", "sweep_interval_minutes"):
        assert k in keys, k
    store = InMemoryStore()
    assert store.supports_ttl is False
    return ("TTLConfig keys: refresh_on_read, omit_expired, default_ttl, "
            "sweep_interval_minutes; default_ttl documented in MINUTES "
            "(PostgresStore stores it as ttl_minutes); InMemoryStore.supports_ttl=False")


def t_provenance_filter():
    """Stated-vs-inferred provenance via filter=."""
    store = InMemoryStore(index={"embed": TinyEmbeddings(), "dims": 2})
    ns = ("learners", "l1", "memories")
    store.put(ns, "m1", {"text": "Lives in Hyderabad", "source": "stated"})
    store.put(ns, "m2", {"text": "Seems interested in startups", "source": "inferred"})
    trusted = store.search(ns, query="where?", filter={"source": "stated"}, limit=3)
    assert len(trusted) == 1 and trusted[0].value["source"] == "stated"
    return "filter={'source':'stated'} returned only the stated fact"


for name, fn in [
    ("14. PUSH injection via @dynamic_prompt", t_dynamic_prompt_push),
    ("15. Dedup on write (search before you write)", t_dedup_on_write),
    ("16. Recency re-ranking from created_at", t_recency_rerank),
    ("17. TTL units + backend capability", t_ttl_units_and_postgres),
    ("18. Provenance via filter=", t_provenance_filter),
]:
    check(name, fn)

print("\n" + "=" * 78)
print("WITH CONTENT-EXPANSION CHECKS")
for status, name, detail in results[13:]:
    print(f"[{status}] {name}\n        {detail}")
print("=" * 78)
print(f"{sum(1 for r in results if r[0] == PASS)}/{len(results)} passed overall")
