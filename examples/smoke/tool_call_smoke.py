from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from flow_agent.config import load_settings
from flow_agent.models import create_chat_model
from flow_agent.tools.file import create_read_file_tool
from flow_agent.tools.executor import execute_tool_call,execute_tool_calls



def main() -> None:
    load_dotenv()

    settings = load_settings()

    model = create_chat_model(settings)

    read_file = create_read_file_tool(
        Path("workspace")
    )

    model_with_tools = model.bind_tools(
        [read_file]
    )

    messages = [HumanMessage(
        content=(
            "Read both a.txt and b.txt from the workspace "
            "and tell me what each file contains."
        )
    )]

    response = model_with_tools.invoke(
        messages
    )
    
    if not response.tool_calls:
      raise RuntimeError("Model did not request a tool")
    
    messages.append(response)
    
    tool_messages = execute_tool_calls(response.tool_calls,[read_file])
    
    messages.extend(tool_messages)
    
    final_response = model_with_tools.invoke(messages)
    
    print(final_response.text)
    
    print(
    "tool calls:",
    len(response.tool_calls),
)

    for tool_call in response.tool_calls:
        print(
            tool_call["id"],
            tool_call["name"],
            tool_call["args"],
        )

    for tool_message in tool_messages:
        print(
            tool_message.tool_call_id,
            tool_message.status,
            tool_message.content,
        )


if __name__ == "__main__":
    main()