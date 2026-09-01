"""Numbers printed in the Hands-On section of
`../building-llm-applications--context-engineering-in-practice.md`.

Payload shapes are taken from a real SkillMap run: Tavily prose from
skill_demand, and a JSON list of job dicts from search_jobs. Each turn's
payload carries its own city and skill, so we can ask not just "how many
tokens survived pruning?" but "which facts survived?"

Importable: `from ce_code.skillmap_context_lab import history` builds the
message list without running any of the reports below.

Run the reports:  ./code/.venv/bin/python ce_code/skillmap_context_lab.py
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately
from langchain.agents.middleware import ClearToolUsesEdit

SYSTEM = ("You are a Skill Mapping assistant that helps students understand skill demand "
          "and find matching job opportunities.\nYou have access to these tools:\n"
          "- skill_demand: Research industry demand, salary insights and career trends\n"
          "- search_jobs: Find actual job listings requiring specific skills\n"
          "Present results in a clean, readable format with clear sections.")

TURNS = [("Generative AI", "Hyderabad"),
         ("AI Engineer", "Bangalore"),
         ("Machine Learning", "Pune")]


# ---- realistic tool payloads (shapes from a live run, one per turn) ----
def demand(skill):
    """What skill_demand returns: Tavily prose, ~3 paragraphs."""
    return (f"88 {skill} Job Creation Statistics and Trends for 2026\n"
            f"Entry-level {skill} roles average $50,000 to $80,000, while senior "
            "specialized positions in big tech can exceed $500,000 annually. "
            f"Professionals with {skill} expertise can expect an average salary of "
            "around $174,727 per year.\n\n") * 3


def jobs(skill, city):
    """What search_jobs returns: a JSON list of 5 job dicts."""
    return json.dumps([{"title": f"{skill} Engineer (LLM + RAG)",
                        "company": "Top Gen AI Jobs",
                        "location": city,
                        "apply_link": "https://in.linkedin.com/jobs/view/"
                                      "generative-ai-agentic-ai-engineer-4459016350"}] * 5,
                      indent=2)


def history(turns=3):
    """One user question per turn, each firing skill_demand + search_jobs."""
    ms = [SystemMessage(SYSTEM)]
    for i, (skill, city) in enumerate(TURNS[:turns]):
        ms.append(HumanMessage(f"Find me {skill} jobs in {city}"))
        ms.append(AIMessage(content="", tool_calls=[
            {"name": "skill_demand", "args": {"skill": skill}, "id": f"d{i}"},
            {"name": "search_jobs", "args": {"skill": skill, "location": city}, "id": f"j{i}"}]))
        ms.append(ToolMessage(content=demand(skill), tool_call_id=f"d{i}"))
        ms.append(ToolMessage(content=jobs(skill, city), tool_call_id=f"j{i}"))
        ms.append(AIMessage(content=f"Here are 5 {skill} openings in {city}."))
    return ms


POISON = '"location": "Kolkata"'


def poisoned_history():
    """Turn 1's job search comes back wrong: Hyderabad listings labelled
    Kolkata, a city the learner never asked about. Nothing raises an error,
    and the bad fact sits in the window for every later turn."""
    ms = history(3)
    for m in ms:
        if isinstance(m, ToolMessage) and m.tool_call_id == "j0":
            m.content = jobs("Generative AI", "Kolkata")        # <-- the poison
    return ms


def prune(ms, keep=1, trigger=500, **kw):
    """Apply tool-output pruning in place and return the same list."""
    ClearToolUsesEdit(trigger=trigger, keep=keep, placeholder="[cleared]", **kw).apply(
        ms, count_tokens=count_tokens_approximately)
    return ms


def survives(ms, fact):
    """Is this fact still visible anywhere in the window?"""
    return any(fact in (m.text if hasattr(m, "text") else str(m.content)) for m in ms)


if __name__ == "__main__":
    print("== how context grows, turn by turn ==")
    for t in (1, 2, 3):
        print(f"  after turn {t}: {count_tokens_approximately(history(t)):5d} tokens")

    ms = history(3)
    before = count_tokens_approximately(ms)
    share = count_tokens_approximately([m for m in ms if isinstance(m, ToolMessage)])
    print("\n== where the tokens are, at turn 3 ==")
    print(f"  total                {before:5d}")
    print(f"  tool output          {share:5d}  ({100 * share // before}% of the window)")
    print(f"  everything else      {before - share:5d}")

    print("\n== per message ==")
    for i, m in enumerate(history(3)):
        print(f"  {i:2d} {type(m).__name__:14s} {count_tokens_approximately([m]):5d}")

    after = count_tokens_approximately(prune(ms, keep=1))
    print("\n== after tool-output pruning (keep=1) ==")
    print(f"  {before} -> {after} tokens  ({100 * (before - after) // before}% smaller)")
    print(f"  tool messages now: {[m.content[:30] for m in ms if isinstance(m, ToolMessage)]}")

    # ---- did the facts survive? the number tokens cannot tell us -------------
    FACTS = {"Hyderabad job listings": '"location": "Hyderabad"',
             "Bangalore job listings": '"location": "Bangalore"',
             "Pune job listings":      '"location": "Pune"',
             "the salary figure":      "$174,727",
             "what the learner asked": "Find me Machine Learning jobs in Pune"}
    print("\n== fact retention vs keep ==")
    print(f"  {'keep':>4} {'tokens':>7}   facts still in the window")
    for k in (1, 2, 3, 6):
        m = prune(history(3), keep=k)
        kept = [name for name, f in FACTS.items() if survives(m, f)]
        print(f"  {k:>4} {count_tokens_approximately(m):>7}   {len(kept)}/{len(FACTS)}"
              f"  ({', '.join(kept)})")

    # ---- context poisoning, and what pruning does to it --------------------
    print("\n== context poisoning ==")
    print(f"  turn 1 returned Kolkata listings for a Hyderabad question.")
    _unpruned = survives(poisoned_history(), POISON)
    _keep1 = survives(prune(poisoned_history(), keep=1), POISON)
    _keep6 = survives(prune(poisoned_history(), keep=6), POISON)
    assert (_unpruned, _keep1, _keep6) == (True, False, True), (_unpruned, _keep1, _keep6)
    print(f"  in the window, unpruned:      {_unpruned}   <- every later turn reads it")
    print(f"  after pruning (keep=1):       {_keep1}  <- stale, so it was cleared")
    print(f"  after pruning (keep=6):       {_keep6}   <- nothing was old enough to clear")

    # ---- answers to "Try It Yourself", asserted so the doc cannot drift ----
    print("\n== Try It Yourself, verified ==")
    _base = count_tokens_approximately(history(3))
    assert _base == 1897, _base
    for _keep, _want in ((1, 677), (2, 907)):
        _got = count_tokens_approximately(prune(history(3), keep=_keep))
        assert _got == _want, f"keep={_keep}: {_got} != {_want}"
        print(f"  1. keep={_keep} -> {_got} tokens")
    _m = prune(history(3), keep=1, trigger=100000)
    assert count_tokens_approximately(_m) == _base
    print(f"  2. trigger=100000 -> {_base} (unchanged: trigger never reached)")
    _m = prune(history(3), keep=1, exclude_tools=("search_jobs",))
    _got = count_tokens_approximately(_m)
    assert _got == 1226, _got
    assert all(survives(_m, f'"location": "{c}"') for c in ("Hyderabad", "Bangalore", "Pune"))
    print(f"  3. exclude_tools=('search_jobs',) -> {_got} "
          f"(every job list survives; only skill_demand prose is cleared)")
    print(f"  4. poisoning: unpruned={_unpruned}, keep=1={_keep1}, keep=6={_keep6}")

    print("\nall assertions passed")
