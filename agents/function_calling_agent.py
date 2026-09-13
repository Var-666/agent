import json

from core.agent import Agent
from core.message import Message
from tools.tool import ToolRegistry


class FunctionCallingAgent(Agent):

    def __init__(
        self,
        name,
        llm,
        registry: ToolRegistry,
        system_prompt=None,
        config=None
    ):
        super().__init__(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            config=config
        )

        self.registry = registry

    def run(self, input_text: str, **kwargs) -> str:

        # 1. 保存用户消息
        self.add_message(
            Message(
                content=input_text,
                role="user"
            )
        )

        # 2. 构造给 LLM 的消息
        messages = []

        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        for message in self.get_history():
            messages.append(
                message.to_dict()
            )

        # 3. 获取 Tool Schema
        tools = self.registry.get_openai_tools()

        max_steps = kwargs.get("max_steps", 5)

        # 4. Agent Loop
        for _ in range(max_steps):

            response = self.llm.call_with_tools(
                messages=messages,
                tools=tools,
                temperature=kwargs.get(
                    "temperature",
                    self.config.temperature
                ),
                max_tokens=kwargs.get(
                    "max_tokens",
                    self.config.max_tokens
                )
            )

            if response is None:
                return "LLM 调用失败"

            # 5. 如果模型没有调用工具
            if not response.tool_calls:

                final_answer = response.content or ""

                self.add_message(
                    Message(
                        content=final_answer,
                        role="assistant"
                    )
                )

                return final_answer

            # 6. 模型决定调用 Tool
            assistant_message = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": []
            }

            for tool_call in response.tool_calls:

                assistant_message["tool_calls"].append({
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments
                    }
                })

            messages.append(assistant_message)

            # 7. 执行所有 Tool Call
            for tool_call in response.tool_calls:

                tool_name = tool_call.function.name

                arguments = json.loads(
                    tool_call.function.arguments
                )

                print(f"🔧 调用工具: {tool_name}")
                print(f"📦 参数: {arguments}")

                try:
                    result = self.registry.execute_tool(
                        tool_name,
                        arguments
                    )

                except Exception as e:
                    result = (
                        f"Tool execution failed: {e}"
                    )

                print(
                    f"✅ 工具结果: {result}"
                )

                # 8. Tool Result 放回消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

        return "超过最大工具调用次数"
