import pytest
import flow_agent.tools.file as file_module

from flow_agent.tools.file import (
    create_read_file_tool,
    create_write_file_tool
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
        
@pytest.mark.parametrize(
    "path",
    [
        r"C:\secret.txt",
        r"C:secret.txt",
        r"..\secret.txt",
    ],
)
def test_read_file_rejects_windows_escape(
    tmp_path,
    path,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    with pytest.raises(ValueError):
        read_file.invoke({"path": path})
        
def test_write_file(tmp_path):
    write_file = create_write_file_tool(
        tmp_path
    )

    result = write_file.invoke(
        {
            "path": "output/report.md",
            "content": "# Report",
        }
    )

    assert (
        tmp_path
        / "output"
        / "report.md"
    ).read_text(
        encoding="utf-8"
    ) == "# Report"

    assert "output/report.md" in result
    
def test_write_file_overwrites_existing_file(
    tmp_path,
):
    target = tmp_path / "report.md"

    target.write_text(
        "old",
        encoding="utf-8",
    )

    write_file = create_write_file_tool(
        tmp_path
    )

    write_file.invoke(
        {
            "path": "report.md",
            "content": "new",
        }
    )

    assert target.read_text(
        encoding="utf-8"
    ) == "new"
    
@pytest.mark.parametrize(
    "path",
    [
        "../secret.txt",
        r"..\secret.txt",
        "/tmp/secret.txt",
        r"C:\secret.txt",
        r"C:secret.txt",
    ],
)
def test_write_file_rejects_workspace_escape(
    tmp_path,
    path,
):
    write_file = create_write_file_tool(
        tmp_path
    )

    with pytest.raises(ValueError):
        write_file.invoke(
            {
                "path": path,
                "content": "secret",
            }
        )
        
def test_write_file_rejects_symlink_escape(
    tmp_path,
):
    outside = tmp_path.parent / "outside"

    outside.mkdir(
        exist_ok=True
    )

    link = tmp_path / "output"
    link.symlink_to(
        outside,
        target_is_directory=True,
    )

    write_file = create_write_file_tool(
        tmp_path
    )

    with pytest.raises(ValueError):
        write_file.invoke(
            {
                "path": "output/report.md",
                "content": "secret",
            }
        )


def test_write_file_rejects_parent_swapped_after_validation(tmp_path, monkeypatch):
    outside = tmp_path.parent / "outside-race"
    outside.mkdir(exist_ok=True)
    parent = tmp_path / "output"
    parent.mkdir()
    original = file_module.resolve_workspace_path

    def swap_parent(workspace_root, path):
        target = original(workspace_root, path)
        parent.rmdir()
        parent.symlink_to(outside, target_is_directory=True)
        return target

    monkeypatch.setattr(file_module, "resolve_workspace_path", swap_parent)
    write_file = create_write_file_tool(tmp_path)

    with pytest.raises(ValueError, match="escape"):
        write_file.invoke({"path": "output/report.md", "content": "secret"})

    assert not (outside / "report.md").exists()


def test_read_file_rejects_file_swapped_after_validation(tmp_path, monkeypatch):
    outside = tmp_path.parent / "outside-read-race.txt"
    outside.write_text("secret", encoding="utf-8")
    target = tmp_path / "notes.txt"
    target.write_text("safe", encoding="utf-8")
    original = file_module.resolve_workspace_path

    def swap_file(workspace_root, path):
        resolved = original(workspace_root, path)
        target.unlink()
        target.symlink_to(outside)
        return resolved

    monkeypatch.setattr(file_module, "resolve_workspace_path", swap_file)
    read_file = create_read_file_tool(tmp_path)

    with pytest.raises(ValueError, match="escape"):
        read_file.invoke({"path": "notes.txt"})
