from tools.tool import (
    Tool,
    ToolParameters,
    ToolArguments,
    ToolResult
)


class CalculatorTool(Tool):

    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行两个数字的加法"
        )

    def get_parameters(self):
        return [
            ToolParameters(
                name="a",
                type="number",
                description="第一个数字"
            ),
            ToolParameters(
                name="b",
                type="number",
                description="第二个数字"
            )
        ]

    def run(
        self,
        arguments: ToolArguments
    ) -> ToolResult:

        a = arguments["a"]
        b = arguments["b"]

        return str(a + b)