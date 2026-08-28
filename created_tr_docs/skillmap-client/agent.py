import asyncio
import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

SYSTEM_PROMPT = """You are a Skill-to-Career Mapping assistant that helps students
understand skill demand and find matching job opportunities."""

client = MultiServerMCPClient({
    "skillmap": {
        "transport": "stdio",
        "command": "uv",
        "args": ["--directory", "/home/nxtwave/TR Docs/created_tr_docs/mcp_code", "run", "server.py"],
    }
})


async def main():
    tools = await client.get_tools()
    print("tools:", [t.name for t in tools])

    model = init_chat_model("google_genai:gemini-2.5-flash",
                            api_key=os.environ["GOOGLE_API_KEY"])
    agent = create_agent(model=model, tools=tools, system_prompt=SYSTEM_PROMPT)

    response = await agent.ainvoke({"messages": [{"role": "user", "content":
        "Save my profile: I am Anil, learning Generative AI in Hyderabad, user id learner_002."}]})
    print(response["messages"][-1].text)


asyncio.run(main())
