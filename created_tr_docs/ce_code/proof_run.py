"""Four real turns against the SkillMap agent, with and without middleware.

Produces the before/after numbers used by the doc's opening and its proof step.
"""
import os, sys, json, requests
from dotenv import load_dotenv
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import ContextEditingMiddleware, ClearToolUsesEdit
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.rate_limiters import InMemoryRateLimiter

load_dotenv("../../.env")
TAVILY = os.environ["TAVILY_API_KEY"]; RAPID = os.environ["RAPID_API_KEY"]

@tool
def skill_demand(skill: str) -> str:
    """Research industry demand, salary insights and career trends for a skill."""
    r = requests.post("https://api.tavily.com/search",
        json={"api_key": TAVILY, "query": f"{skill} skills demand and salary 2026",
              "max_results": 3, "search_depth": "basic"}, timeout=30)
    return "\n\n".join(f"{x['title']}\n{x['content'][:300]}" for x in r.json().get("results", []))

@tool
def search_jobs(skill: str, location: str) -> list:
    """Find actual job listings requiring a specific skill in a location."""
    r = requests.get("https://jsearch.p.rapidapi.com/search",
        headers={"x-rapidapi-key": RAPID, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
        params={"query": f"{skill} in {location}", "page": "1", "num_pages": "1", "country": "in"},
        timeout=30)
    return [{"title": d.get("job_title"), "company": d.get("employer_name"),
             "location": d.get("job_city")} for d in r.json().get("data", [])[:5]]

SYS = ("You are a Skill Mapping assistant that helps students understand skill demand and find "
       "matching job opportunities. Present results in a clean, readable format. "
       "Do not use markdown formatting.")

TURNS = ["Find me Generative AI jobs in Hyderabad",
         "Now AI Engineer roles in Bangalore",
         "And Machine Learning in Pune",
         "Of the Pune roles you just listed, which need less than 2 years experience?"]

# free tier allows 5 requests/minute -> pace at 1 every 15s with burst 1
LIMITER = InMemoryRateLimiter(requests_per_second=1/15, check_every_n_seconds=0.5, max_bucket_size=1)

def run(label, middleware):
    agent = create_agent(model=init_chat_model("google_genai:gemini-2.5-flash",
                                               api_key=os.environ["GOOGLE_API_KEY"],
                                               rate_limiter=LIMITER),
                         system_prompt=SYS, tools=[skill_demand, search_jobs],
                         middleware=middleware, checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": label}}
    print(f"\n=== {label} ===")
    for i, q in enumerate(TURNS, 1):
        resp = agent.invoke({"messages": [{"role": "user", "content": q}]}, config=cfg)
        um = [m for m in resp["messages"] if getattr(m, "usage_metadata", None)]
        sent = um[-1].usage_metadata["input_tokens"] if um else 0
        calls = sum(len(getattr(m, "tool_calls", []) or []) for m in resp["messages"])
        print(f"  turn {i}: input_tokens={sent:6d}  cumulative tool_calls={calls}")
    return resp

pruning = ContextEditingMiddleware(edits=[ClearToolUsesEdit(trigger=2000, keep=1)])
r1 = run("no-middleware", [])
r2 = run("with-pruning", [pruning])
print("\n--- turn 4 answer, no middleware ---\n", r1["messages"][-1].text[:400])
print("\n--- turn 4 answer, with pruning ---\n", r2["messages"][-1].text[:400])
