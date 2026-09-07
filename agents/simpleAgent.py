from core.agent import Agent
from core.message import Message


class SimpleAgent(Agent):
    """最简单的 Agent:保存历史并调用 LLM"""

    def run(self, input_text: str, **kwargs) -> str:

        # 1. 把用户输入包装成 Message
        user_message = Message(
            content=input_text,
            role="user"
        )

        # 2. 加入历史记录
        self.add_message(user_message)

        # 3. 准备发送给 LLM 的消息
        messages = []

        # 如果存在 system prompt，先加入
        if self.system_prompt:
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

        # 加入历史消息
        for message in self.get_history():
            messages.append(
                message.to_dict()
            )

        # 4. 调用 LLM
        response = self.llm.think(
            messages=messages,
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

        # 5. 把模型回答也保存进历史
        assistant_message = Message(
            content=response,
            role="assistant"
        )

        self.add_message(assistant_message)

        # 6. 返回结果
        return response
