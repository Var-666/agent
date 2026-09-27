from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from flow_agent.config import load_settings
from flow_agent.models import create_chat_model
from flow_agent.tools.file import (
    create_read_file_tool,
)


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

    message = HumanMessage(
        content=(
            "Read notes.txt from the workspace "
            "and tell me what it contains."
        )
    )

    response = model_with_tools.invoke(
        [message]
    )

    print("content:")
    print(response.content)

    print("\ntool_calls:")
    print(response.tool_calls)


if __name__ == "__main__":
    main()