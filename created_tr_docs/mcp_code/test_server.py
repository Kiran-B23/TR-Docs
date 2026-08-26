"""Exercise the SkillMap MCP server and print exactly what a client sees."""
import asyncio, json
from mcp import Client
from server import mcp

def show(label, obj):
    print(f"\n--- {label} ---")
    print(obj)

async def main():
    async with Client(mcp) as c:
        print("protocol_version:", c.protocol_version)
        print("server_info:", c.server_info)

        tools = await c.list_tools()
        show("tools/list", [t.name for t in tools.tools])
        print("\nsearch_jobs inputSchema:")
        print(json.dumps(next(t for t in tools.tools if t.name=="search_jobs").input_schema, indent=2))

        tpl = await c.list_resource_templates()
        show("resources/templates/list", [(t.uri_template, t.mime_type) for t in tpl.resource_templates])

        r = await c.call_tool("save_learner_profile",
                              {"user_id":"learner_001","name":"Anil",
                               "skill":"Generative AI","location":"Hyderabad"})
        show("tools/call save_learner_profile", f"isError={r.is_error}  content={r.content}")

        rr = await c.read_resource("learner://profile/learner_001")
        show("resources/read (exists)", rr.contents[0].text)

        pr = await c.list_prompts()
        show("prompts/list", [(x.name, [(a.name, a.required) for a in (x.arguments or [])])
                              for x in pr.prompts])
        gp = await c.get_prompt("career_review", {"skill":"Generative AI","location":"Hyderabad"})
        show("prompts/get career_review", gp.messages[0].content.text)

        # --- failure paths ---
        # Deterministic: a ToolError we raise ourselves, message preserved.
        import server as _s
        _saved, _s.RAPIDAPI_KEY = _s.RAPIDAPI_KEY, None
        bad = await c.call_tool("search_jobs", {"skill":"Generative AI","location":"Hyderabad"})
        show("tools/call FAILING (ToolError - message preserved)",
             f"isError={bad.is_error}\ncontent={bad.content}")
        _s.RAPIDAPI_KEY = _saved

        try:
            await c.read_resource("learner://profile/nobody")
        except Exception as e:
            show("resources/read (missing)", f"{type(e).__name__}: {e}")

        try:
            u = await c.call_tool("no_such_tool", {})
            show("tools/call unknown tool", f"is_error={u.is_error}\ncontent={u.content}")
        except Exception as e:
            show("tools/call unknown tool", f"raised {type(e).__name__}: {e}")

        try:
            b = await c.call_tool("search_jobs", {"skill": "Python"})   # missing 'location'
            show("tools/call missing argument", f"is_error={b.is_error}\ncontent={b.content}")
        except Exception as e:
            show("tools/call missing argument", f"raised {type(e).__name__}: {e}")

        # An exception that is NOT a ToolError: the message is masked.
        @mcp.tool()
        def unguarded() -> str:
            """Lets a non-ToolError exception escape."""
            raise ValueError("this detail never reaches the model")

        m = await c.call_tool("unguarded", {})
        show("tools/call unguarded (masked)", f"is_error={m.is_error}\ncontent={m.content}")

asyncio.run(main())
