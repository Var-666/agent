from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from flow_agent.config import load_settings
from flow_agent.models import create_chat_model
from flow_agent.tools.file import create_read_file_tool
from flow_agent.tools.executor import execute_tool_call



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
            "Read notes.txt from the workspace "
            "and tell me what it contains."
        )
    )]

    response = model_with_tools.invoke(
        messages
    )
    
    messages.append(response)
    
    if not response.tool_calls:
      raise RuntimeError("Model did not request a tool")
    
    tool_call = response.tool_calls[0]
    tool_message = execute_tool_call(tool_call,[read_file])
    
    messages.append(tool_message)
    
    final_response = model_with_tools.invoke(messages)
    
    print(final_response.text)
    
    for index, item in enumerate(messages):
      print(
          index,
          type(item).__name__,
      )
      
    print(
        response.tool_calls[0]["id"]
    )

    print(
        tool_message.tool_call_id
    )


if __name__ == "__main__":
    main()