import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain.messages import (HumanMessage,SystemMessage,AIMessage)
from langchain.tools import tool

load_dotenv()

model = init_chat_model(
    model=os.getenv("LLM_MODEL"),
    model_provider="openai",
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)


@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"{city} 的天气是晴天"

model_with_tools = model.bind_tools([get_weather])

messages = [
    HumanMessage(
        "北京的天气怎么样？"
    )
]

ai_message = model_with_tools.invoke(messages)

messages.append(ai_message)

for tool_call in ai_message.tool_calls:
  tool_result = get_weather.invoke(tool_call)
  messages.append(tool_result)

final_response = model_with_tools.invoke(messages)

print(final_response.text)
