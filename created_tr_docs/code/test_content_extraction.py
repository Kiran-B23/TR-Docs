"""Determine the reliable way to extract text from a LangChain v1 agent response."""
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
model = init_chat_model("google_genai:gemini-2.5-flash",
                        api_key=os.environ["GOOGLE_API_KEY"])
agent = create_agent(model=model, tools=[], system_prompt="Answer in one short sentence.")

for i, q in enumerate(["What is 2+2?", "Name one Indian city.", "Say hello."], 1):
    msg = agent.invoke({"messages": [{"role": "user", "content": q}]})["messages"][-1]
    ctype = type(msg.content).__name__
    has_text = hasattr(msg, "text")
    text_val = None
    if has_text:
        t = msg.text
        text_val = t() if callable(t) else t
    print(f"turn {i}: content={ctype:5s} | .text present={has_text} "
          f"| callable={callable(getattr(msg,'text',None))} | .text -> {str(text_val)[:60]!r}")
