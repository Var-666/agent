import pytest

from flow_agent.tools.file import (
    create_read_file_tool,
)


def test_read_file(tmp_path):
    file_path = tmp_path / "notes.txt"

    file_path.write_text(
        "hello FlowAgent",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    result = read_file.invoke(
        {
            "path": "notes.txt",
        }
    )

    assert result == "hello FlowAgent"
    
def test_read_file_rejects_parent_traversal(
    tmp_path,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    with pytest.raises(ValueError):
        read_file.invoke(
            {
                "path": "../secret.txt",
            }
        )
        
def test_read_file_rejects_absolute_path(
    tmp_path,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    with pytest.raises(ValueError):
        read_file.invoke(
            {
                "path": "/etc/passwd",
            }
        )
        
def test_read_file_rejects_missing_file(
    tmp_path,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    with pytest.raises(FileNotFoundError):
        read_file.invoke(
            {
                "path": "missing.txt",
            }
        )
        
def test_read_file_rejects_symlink_escape(
    tmp_path,
):
    outside = tmp_path.parent / "outside.txt"

    outside.write_text(
        "secret",
        encoding="utf-8",
    )

    link = tmp_path / "link.txt"
    link.symlink_to(outside)

    read_file = create_read_file_tool(
        tmp_path
    )

    with pytest.raises(ValueError):
        read_file.invoke(
            {
                "path": "link.txt",
            }
        )