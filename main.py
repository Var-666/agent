from agents.function_calling_agent import FunctionCallingAgent
from core.config import Config
from core.llm import LLMClient
from tools.tool import ToolRegistry
from tools.tool_list.calculator_tool import CalculatorTool


SYSTEM_PROMPT = (
    "你是一个计算助手。\n\n"
    "当用户提出数学计算问题时，优先使用提供的计算工具完成计算，"
    "不要自己猜测计算结果。"
)
DEFAULT_QUESTION = "帮我计算 25 + 37"


def create_agent(config: Config | None = None) -> FunctionCallingAgent:
    """Create the configured agent and register its tools."""
    config = config or Config.from_env()
    llm = LLMClient(config=config)
    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())

    return FunctionCallingAgent(
        name="calculator_agent",
        llm=llm,
        registry=registry,
        config=config,
        system_prompt=SYSTEM_PROMPT
    )


def main():
    """Run the default command-line example."""
    agent = create_agent()
    result = agent.run(DEFAULT_QUESTION)

    print("\n最终回答：")
    print(result)


if __name__ == "__main__":
    main()
