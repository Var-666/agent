from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt

from tools.tool import (
    Tool,
    ToolResult
)


class CalculatorArguments(BaseModel):
    """Validated arguments for CalculatorTool."""

    model_config = ConfigDict(extra="forbid")

    a: StrictInt | StrictFloat = Field(description="第一个数字")
    b: StrictInt | StrictFloat = Field(description="第二个数字")


class CalculatorTool(Tool[CalculatorArguments]):
    """Add two numbers."""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行两个数字的加法",
            arguments_model=CalculatorArguments
        )

    def run(
        self,
        arguments: CalculatorArguments
    ) -> ToolResult:
        return str(arguments.a + arguments.b)
