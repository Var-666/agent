"""带短期会话记忆的购物 Agent 学习示例。"""

import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()

checkpointer = InMemorySaver()

model = init_chat_model(
    model=os.getenv("LLM_MODEL"),
    model_provider="openai",
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)

config = {"configurable": {"thread_id": "chat-A"}}


@tool
def get_product_price(product: str) -> float:
    """查询商品的单价。"""

    prices = {
        "MacBook": 10000,
        "iPhone": 6000,
    }

    return prices.get(product, 0)


@tool
def multiply(a: float, b: float) -> float:
    """计算两个数字的乘积。"""

    return a * b


agent = create_agent(
    model=model,
    tools=[get_product_price, multiply],
    system_prompt="你是一个购物助手，需要使用工具获取商品价格并完成计算。",
    checkpointer=checkpointer,
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "买 3 台 MacBook 一共多少钱？"}]},
    config,
)
print(result["messages"][-1].content)

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "在前面 3 台 MacBook 的前提下，那我再买 2 台 iPhone 一共多少钱？",
            }
        ]
    },
    config,
)
print(result["messages"][-1].content)
