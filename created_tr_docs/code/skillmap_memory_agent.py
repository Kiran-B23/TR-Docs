"""
SkillMap Agent with Short-Term + Long-Term Memory
Runnable version of the final code in
building-llm-applications--33-building-memory-agents-long-term-memory.md

Differences from the Colab version in the doc (kept minimal, marked LOCAL):
  * secrets come from ../../.env instead of google.colab.userdata
  * skill_demand_tool / search_jobs are stubbed when TAVILY/RAPIDAPI keys are absent,
    so the memory behaviour can be tested without those services

Run:  ./.venv/bin/python skillmap_memory_agent.py
"""
import os
from datetime import datetime
from dataclasses import dataclass

from dotenv import load_dotenv
from typing_extensions import TypedDict

from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

# ---------------------------------------------------------------- LOCAL: secrets
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
RAPIDAPI_KEY = os.environ.get("RAPID_API_KEY") or os.environ.get("RAPIDAPI_KEY")

# ---------------------------------------------------------------- tools
if TAVILY_API_KEY:
    from langchain_tavily import TavilySearch
    skill_demand_tool = TavilySearch(max_results=5, search_depth="advanced",
                                     tavily_api_key=TAVILY_API_KEY)
    # The model sees .name, not our variable name. Without this the model sees
    # "tavily_search" while SYSTEM_PROMPT says "skill_demand_tool".
    skill_demand_tool.name = "skill_demand_tool"
else:
    @tool
    def skill_demand_tool(query: str) -> str:
        """Research industry demand, salary insights, and career trends for a skill."""
        print(f"\n[stub] skill_demand_tool({query!r})")
        return ("Generative AI demand is very high in India in 2026. "
                "Typical fresher AI Engineer salary: 8-14 LPA.")

if RAPIDAPI_KEY:
    import requests

    @tool
    def search_jobs(skill: str, location: str) -> list:
        """Search for jobs requiring a specific skill using the JSearch API."""
        url = "https://jsearch.p.rapidapi.com/search"
        headers = {"x-rapidapi-key": RAPIDAPI_KEY,
                   "x-rapidapi-host": "jsearch.p.rapidapi.com"}
        params = {"query": f"{skill} in {location}", "page": "1", "num_pages": "1",
                  "country": "in", "employment_types": "INTERN,FULLTIME",
                  "job_requirements": "no_experience,under_3_years_experience"}
        data = requests.get(url, headers=headers, params=params).json()
        return [{"title": j.get("job_title"), "company": j.get("employer_name"),
                 "location": j.get("job_city"), "apply_link": j.get("job_apply_link")}
                for j in data.get("data", [])]
else:
    @tool
    def search_jobs(skill: str, location: str) -> list:
        """Search for jobs requiring a specific skill using the JSearch API."""
        print(f"\n[stub] search_jobs(skill={skill!r}, location={location!r})")
        return [
            {"title": "AI Engineer", "company": "Acme AI", "location": location,
             "apply_link": "https://example.com/1"},
            {"title": "GenAI Intern", "company": "Nova Labs", "location": location,
             "apply_link": "https://example.com/2"},
        ]

# ---------------------------------------------------------------- memory
store = InMemoryStore()


@dataclass
class Context:
    user_id: str


class LearnerProfile(TypedDict, total=False):
    """A learner's career profile. Only include the fields the learner
    actually mentioned - leave the rest out."""
    name: str
    skill: str
    location: str
    experience_level: str


@tool
def save_learner_profile(profile: LearnerProfile, runtime: ToolRuntime[Context]) -> str:
    """Save the learner's career profile (name, skill, location, experience level)
    so it can be recalled in future sessions."""
    print("\nCalling save_learner_profile tool")
    existing = runtime.store.get(("learners",), runtime.context.user_id)
    merged = {**(existing.value if existing else {}), **dict(profile)}
    runtime.store.put(("learners",), runtime.context.user_id, merged)
    return "Learner profile saved."


@tool
def save_interaction(summary: str, outcome: str, runtime: ToolRuntime[Context]) -> str:
    """Record what happened in this session and how it turned out, so future
    sessions do not repeat suggestions that were already made or rejected."""
    print("\nCalling save_interaction tool")
    timestamp = datetime.now().isoformat()
    runtime.store.put(
        ("learners", runtime.context.user_id, "episodes"),
        timestamp,
        {"summary": summary, "outcome": outcome, "timestamp": timestamp},
    )
    return "Interaction recorded."


@tool
def get_learner_profile(runtime: ToolRuntime[Context]) -> str:
    """Look up the learner's saved career profile from previous sessions."""
    print("\nCalling get_learner_profile tool")
    profile = runtime.store.get(("learners",), runtime.context.user_id)
    return str(profile.value) if profile else "No saved profile yet."


SYSTEM_PROMPT = """You are a Skill-to-Career Mapping assistant that helps students understand skill demand
and find matching job opportunities.

You have access to these tools:
- skill_demand_tool: Research industry demand, salary insights, and career trends
- search_jobs: Find real job listings based on skills and location
- get_learner_profile: Look up what you already know about this learner
- save_learner_profile: Save the learner's details for future sessions
- save_interaction: Record what you showed the learner and how they responded

Memory rules:
- At the start of every conversation, call get_learner_profile first.
- When the learner shares their name, skill, location, or experience level, call save_learner_profile.
- Never ask the learner for details you already have.
- At the end of a session, call save_interaction with what you showed and how the learner responded.

Present results in a clean, readable format with clear sections and spacing.
Include all job details with apply links.
Do not use markdown formatting.
"""

model = init_chat_model("google_genai:gemini-2.5-flash", api_key=GOOGLE_API_KEY)
checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    tools=[
        skill_demand_tool,
        search_jobs,
        save_learner_profile,
        get_learner_profile,
        save_interaction,
    ],
    checkpointer=checkpointer,
    store=store,
    context_schema=Context,
    debug=True,
)


def run(label, text, thread_id, user_id):
    """LOCAL: invoke with a friendly message if the free-tier quota is exhausted."""
    try:
        return agent.invoke(
            {"messages": [{"role": "user", "content": text}]},
            config={"configurable": {"thread_id": thread_id}},
            context=Context(user_id=user_id),
        )
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            print(f"\n[{label}] SKIPPED - Gemini free tier quota exhausted "
                  f"(20 requests/day). Try again later or use a billed key.")
            return None
        raise


def show(response, label):
    """LOCAL: prints the answer AND reports how .content is actually shaped."""
    if response is None:
        return None
    msg = response["messages"][-1]
    print(f"\n--- {label}: content type = {type(msg.content).__name__} ---")
    if isinstance(msg.content, list):
        print(f"    list of {len(msg.content)}; first element: {type(msg.content[0]).__name__}")
        print(f"    repr head: {repr(msg.content)[:160]}")
    print(msg.text)          # .text handles str AND list-of-blocks
    return msg.text


if __name__ == "__main__":
    print("=" * 78)
    print("SESSION 1  (thread_id='1', user_id='learner_001')")
    print("=" * 78)
    r1 = run("session 1",
             "I'm Anil, a final-year student in Hyderabad learning Generative AI. "
             "Show me relevant job openings.", "1", "learner_001")
    show(r1, "session 1")

    print("\n" + "=" * 78)
    print("WHAT WAS REMEMBERED")
    print("=" * 78)
    prof = store.get(("learners",), "learner_001")
    print("semantic profile:", prof.value if prof else None)
    eps = store.search(("learners", "learner_001", "episodes"))
    print(f"episodic entries: {len(eps)}")
    for e in eps:
        print("   ", e.value)

    print("\n" + "=" * 78)
    print("SESSION 2  (thread_id='2' -> BRAND NEW conversation, same learner)")
    print("=" * 78)
    r2 = run("session 2", "Any new openings for me?", "2", "learner_001")
    show(r2, "session 2")

    print("\n" + "=" * 78)
    print("SESSION 3  (different user_id -> should NOT recognise the learner)")
    print("=" * 78)
    r3 = run("session 3", "Any new openings for me?", "3", "learner_999")
    show(r3, "session 3")
