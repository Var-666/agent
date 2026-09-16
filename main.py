from agents.function_calling_agent import FunctionCallingAgent
from core.config import Config
from core.llm import LLMClient
from tools.tool import ToolRegistry
from tools.tool_list.calculator_tool import CalculatorTool
from tools.tool_list.time_tool import TimeTool


SYSTEM_PROMPT = (
    "你是一个工具调用助手。"
    "根据用户的问题选择合适的工具。"
    "如果现有工具可以完成任务，应优先使用工具。"
    "如果不需要工具，则直接回答。"
)
DEFAULT_QUESTION = "先计算 25 + 37,如果结果大于 50,再告诉我东京现在几点；如果不大于 50,就只告诉我计算结果。"


def create_agent(config: Config | None = None) -> FunctionCallingAgent:
    """Create the configured agent and register its tools."""
    config = config or Config.from_env()
    llm = LLMClient(config=config)
    registry = ToolRegistry()
    registry.register_tool(CalculatorTool())
    registry.register_tool(TimeTool())

    return FunctionCallingAgent(
        name="multi_tool_agent",
        llm=llm,
        registry=registry,
        config=config,
        system_prompt=SYSTEM_PROMPT
    )


def main():
    """Run the default command-line example."""
    agent = create_agent()
    result = agent.run(DEFAULT_QUESTION)

    print("\n最终回答:")
    print(result)


if __name__ == "__main__":
    main()
