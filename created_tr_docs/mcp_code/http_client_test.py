import asyncio
from mcp import Client

async def main():
    async with Client("http://127.0.0.1:8000/mcp") as c:
        print("connected over Streamable HTTP")
        print("protocol_version:", c.protocol_version)
        print("server_info:", c.server_info.name, c.server_info.version)
        t = await c.list_tools()
        print("tools:", [x.name for x in t.tools])
        r = await c.call_tool("save_learner_profile",
                              {"user_id": "http_user", "name": "Bhavya",
                               "skill": "RAG", "location": "Bangalore"})
        print("call over http -> is_error:", r.is_error, "|", r.content[0].text)

asyncio.run(main())
