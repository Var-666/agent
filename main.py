import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

load_dotenv()

model = ChatOpenAI(
    model=os.getenv("LLM_MODEL"),
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"{city} 的天气是晴天"


agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "东京天气怎么样？"
            }
        ]
    }
)

print(result["messages"][-1].content)
