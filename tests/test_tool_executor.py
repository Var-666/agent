from flow_agent.tools.executor import (
    execute_tool_call,
)
from flow_agent.tools.file import (
    create_read_file_tool,
)


def test_execute_tool_call(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text(
        "hello FlowAgent",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    message = execute_tool_call(
        {
            "name": "read_file",
            "args": {
                "path": "notes.txt",
            },
            "id": "call-001",
            "type": "tool_call",
        },
        [read_file],
    )

    assert message.content == "hello FlowAgent"
    assert message.tool_call_id == "call-001"
    assert message.status == "success"
    
def test_execute_tool_call_returns_error_message(
    tmp_path,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    message = execute_tool_call(
        {
            "name": "read_file",
            "args": {
                "path": "missing.txt",
            },
            "id": "call-001",
            "type": "tool_call",
        },
        [read_file],
    )

    assert message.tool_call_id == "call-001"
    assert message.status == "error"
    assert "missing.txt" in message.content
    
import pytest


def test_execute_tool_call_rejects_unknown_tool():
    with pytest.raises(
        ValueError,
        match="Unknown tool",
    ):
        execute_tool_call(
            {
                "name": "delete_everything",
                "args": {},
                "id": "call-001",
                "type": "tool_call",
            },
            [],
        )

def test_execute_tool_call_requires_id(
    tmp_path,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="must have an id",
    ):
        execute_tool_call(
            {
                "name": "read_file",
                "args": {
                    "path": "notes.txt",
                },
                "id": None,
                "type": "tool_call",
            },
            [read_file],
        )