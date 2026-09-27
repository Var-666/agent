from flow_agent.tools.executor import (
    execute_tool_call,
    execute_tool_calls,
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
        
def test_execute_multiple_tool_calls(
    tmp_path,
):
    (tmp_path / "a.txt").write_text(
        "content A",
        encoding="utf-8",
    )

    (tmp_path / "b.txt").write_text(
        "content B",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    messages = execute_tool_calls(
        [
            {
                "name": "read_file",
                "args": {
                    "path": "a.txt",
                },
                "id": "call-a",
                "type": "tool_call",
            },
            {
                "name": "read_file",
                "args": {
                    "path": "b.txt",
                },
                "id": "call-b",
                "type": "tool_call",
            },
        ],
        [read_file],
    )

    assert len(messages) == 2

    assert messages[0].content == "content A"
    assert messages[0].tool_call_id == "call-a"

    assert messages[1].content == "content B"
    assert messages[1].tool_call_id == "call-b"
    
def test_execute_multiple_tool_calls_keeps_errors(
    tmp_path,
):
    (tmp_path / "a.txt").write_text(
        "content A",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    messages = execute_tool_calls(
        [
            {
                "name": "read_file",
                "args": {"path": "a.txt"},
                "id": "call-a",
                "type": "tool_call",
            },
            {
                "name": "read_file",
                "args": {
                    "path": "missing.txt",
                },
                "id": "call-b",
                "type": "tool_call",
            },
        ],
        [read_file],
    )

    assert messages[0].status == "success"
    assert messages[1].status == "error"

    assert (
        messages[0].tool_call_id
        == "call-a"
    )

    assert (
        messages[1].tool_call_id
        == "call-b"
    )