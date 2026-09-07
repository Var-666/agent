from agents.function_calling_agent import FunctionCallingAgent
from core.config import Config
from core.llm import AgentsLLM
from tools.tool import ToolRegistry
from tools.tool_list.calculatorTool import CalculatorTool


def main():

    config = Config.from_env()
    llm = AgentsLLM(config=config)

    registry = ToolRegistry()

    registry.register_tool(
        CalculatorTool()
    )

    agent = FunctionCallingAgent(
        name="calculator_agent",
        llm=llm,
        registry=registry,
        config=config,
        system_prompt="""
          你是一个计算助手。

          当用户提出数学计算问题时，
          优先使用提供的计算工具完成计算，
          不要自己猜测计算结果。
          """
    )

    result = agent.run(
        "帮我计算 25 + 37"
    )

    print("\n最终回答：")
    print(result)


if __name__ == "__main__":
    main()
