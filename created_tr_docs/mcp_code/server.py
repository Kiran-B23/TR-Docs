"""SkillMap MCP server — 3 tools + 1 resource + 1 prompt."""
import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError

logger = logging.getLogger(__name__)          # stderr — keep your own output off stdout

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
RAPIDAPI_KEY = os.environ.get("RAPID_API_KEY")

PROFILES = Path(__file__).parent / "profiles.json"

mcp = MCPServer("skillmap", version="1.0.0")


def _load() -> dict:
    return json.loads(PROFILES.read_text()) if PROFILES.exists() else {}


@mcp.tool()
def skill_demand(skill: str) -> str:
    """Research industry demand, salary insights and career trends for a skill."""
    logger.info("skill_demand(%s)", skill)
    if not TAVILY_API_KEY:
        raise ToolError("TAVILY_API_KEY is not configured on the server.")
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_API_KEY, "query": f"{skill} skills demand and salary 2026",
                  "max_results": 3, "search_depth": "basic"},
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("Tavily API call failed")
        raise ToolError(f"Could not reach the Tavily API: {type(e).__name__}") from e
    if r.status_code != 200:
        raise ToolError(f"Tavily search failed with status {r.status_code}.")
    results = r.json().get("results", [])
    if not results:
        raise ToolError(f"No demand information found for '{skill}'.")
    return "\n\n".join(f"{x['title']}\n{x['content'][:300]}" for x in results)


@mcp.tool()
def search_jobs(skill: str, location: str) -> list[dict]:
    """Search for real job openings requiring a specific skill in a location."""
    logger.info("search_jobs(%s, %s)", skill, location)
    if not RAPIDAPI_KEY:
        raise ToolError("RAPID_API_KEY is not configured on the server.")
    try:
        r = requests.get(
            "https://jsearch.p.rapidapi.com/search",
            headers={"x-rapidapi-key": RAPIDAPI_KEY, "x-rapidapi-host": "jsearch.p.rapidapi.com"},
            params={"query": f"{skill} in {location}", "page": "1", "num_pages": "1", "country": "in"},
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("jobs API call failed")
        raise ToolError(f"Could not reach the jobs API: {type(e).__name__}") from e
    if r.status_code != 200:
        raise ToolError(f"Job search failed with status {r.status_code}.")
    jobs = r.json().get("data", [])
    if not jobs:
        raise ToolError(f"No {skill} jobs found in {location}.")
    return [{"title": j.get("job_title"), "company": j.get("employer_name"),
             "location": j.get("job_city"), "apply_link": j.get("job_apply_link")}
            for j in jobs[:5]]


@mcp.tool()
def save_learner_profile(user_id: str, name: str, skill: str, location: str) -> str:
    """Save a learner's career profile so it can be read back in future sessions."""
    logger.info("save_learner_profile(%s)", user_id)
    data = _load()
    data[user_id] = {"name": name, "skill": skill, "location": location}
    PROFILES.write_text(json.dumps(data, indent=2))
    return f"Saved profile for {name}."


@mcp.resource("learner://profile/{user_id}", mime_type="application/json")
def learner_profile(user_id: str) -> str:
    """The saved career profile for one learner."""
    data = _load()
    if user_id not in data:
        raise ResourceNotFoundError(f"No profile saved for '{user_id}'.")
    return json.dumps(data[user_id], indent=2)


@mcp.prompt()
def career_review(skill: str, location: str) -> str:
    """Ask for a structured career review for one skill and city."""
    return (f"I am learning {skill} and job-hunting in {location}.\n"
            f"1. Check current demand for {skill}.\n"
            f"2. Find openings in {location}.\n"
            f"3. Tell me the two skills I am most likely missing.")


if __name__ == "__main__":
    mcp.run(transport="stdio")
