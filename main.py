import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain.messages import (HumanMessage,SystemMessage,AIMessage)

load_dotenv()

model = init_chat_model(
    model=os.getenv("LLM_MODEL"),
    model_provider="openai",
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)



def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"{city} 的天气是晴天"

messages = [
    SystemMessage(
        "你是一名 Python 老师，回答尽量简洁。"
    ),
    HumanMessage(
        "我正在学习 Python,我的名字叫 Var。"
    ),
    AIMessage(
        "好的,Var。"
    ),
    HumanMessage(
        "我的名字是什么？我正在学习什么语言？"
    )
]


agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

response = model.invoke(messages)

print("类型：")
print(type(response))

print("\n文本:")
print(response.text)

print("\n完整 Message:")
print(response)

print("\nToken 信息：")
print(response.usage_metadata)
