import json
import time

from pydantic import ValidationError

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
            messages.append(message.to_dict())

        # 3. 获取 Tool Schema
        tools = self.registry.get_openai_tools()

        max_steps = kwargs.get("max_steps", 5)

        # 4. Agent Loop
        for _ in range(max_steps):

            response = self.llm.call_with_tools(
                messages=messages,
                tools=tools,
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens)
            )

            if response is None:
                return "LLM 调用失败"

            # 5. 如果模型没有调用工具
            if not response.tool_calls:

                final_answer = response.content or ""

                self.add_message(
                    Message(content=final_answer, role="assistant")
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

                try:
                    arguments = json.loads(
                        tool_call.function.arguments
                    )
                except json.JSONDecodeError as e:
                    error_result = (
                        f"Tool '{tool_name}' 参数 JSON 解析失败: {e}"
                    )
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": error_result
                    })
                    continue

                print(f"🔧 调用工具: {tool_name}")
                print(f"📦 参数: {arguments}")

                result = self._execute_tool_with_retry(
                    tool_name,
                    arguments,
                    max_retries=2
                )

                print(f"✅ 工具结果: {result}")

                # 8. Tool Result 放回消息
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

        return "超过最大工具调用次数"

    def _execute_tool_with_retry(
        self,
        tool_name: str,
        arguments: dict,
        max_retries: int = 2
    ) -> str:
        for attempt in range(max_retries + 1):
            try:
                return self.registry.execute_tool(tool_name, arguments)

            except ValidationError as e:
                return f"Tool '{tool_name}' 参数验证失败: {e}"

            except (TimeoutError, ConnectionError) as e:
                if attempt < max_retries:
                    print(
                        "Tool 临时失败，正在重试 "
                        f"({attempt + 1}/{max_retries})"
                    )
                    time.sleep(1)
                    continue
                return (
                    f"Tool '{tool_name}' 重试后仍失败: "
                    f"{type(e).__name__}: {e}"
                )

            except ValueError as e:
                return f"Tool '{tool_name}' 调用失败: {e}"

            except Exception as e:
                return (
                    f"Tool '{tool_name}' 执行异常: "
                    f"{type(e).__name__}: {e}"
                )
