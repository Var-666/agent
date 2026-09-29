import errno
import os
from contextlib import ExitStack
from pathlib import Path,PureWindowsPath

from langchain.tools import tool
from langchain_core.tools import BaseTool

def resolve_workspace_path(
    workspace_root: Path,
    path: str,
) -> Path:
    raw_path = path.strip()

    if not raw_path:
        raise ValueError(
            "File path cannot be empty"
        )

    windows_path = PureWindowsPath(raw_path)

    if (
        Path(raw_path).is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
    ):
        raise ValueError(
            "File path must be relative to the workspace"
        )

    relative_path = Path(
        raw_path.replace("\\", "/")
    )

    if ".." in relative_path.parts:
        raise ValueError(
            "File path cannot escape the workspace"
        )

    root = workspace_root.resolve()
    target = (root / relative_path).resolve()

    if not target.is_relative_to(root):
        raise ValueError(
            "File path cannot escape the workspace"
        )

    return target


def _open_workspace_file(
    workspace_root: Path,
    path: str,
    flags: int,
    *,
    create_parents: bool = False,
) -> int:
    # Validate the public path contract, then anchor every open to a directory FD.
    resolve_workspace_path(workspace_root, path)

    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise RuntimeError("Secure workspace file access requires POSIX directory FDs")

    root = workspace_root.resolve()
    if create_parents:
        root.mkdir(parents=True, exist_ok=True)

    parts = Path(path.replace("\\", "/")).parts
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW

    try:
        with ExitStack() as stack:
            directory_fd = os.open(root, directory_flags)
            stack.callback(os.close, directory_fd)

            for part in parts[:-1]:
                if create_parents:
                    try:
                        os.mkdir(part, dir_fd=directory_fd)
                    except FileExistsError:
                        pass

                directory_fd = os.open(part, directory_flags, dir_fd=directory_fd)
                stack.callback(os.close, directory_fd)

            return os.open(
                parts[-1],
                flags | os.O_NOFOLLOW,
                0o666,
                dir_fd=directory_fd,
            )
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise ValueError("File path cannot escape the workspace") from exc
        raise

def create_read_file_tool(workspace_root: Path) -> BaseTool:
  
  @tool("read_file")
  def read_file(path: str) -> str:
    """Read a UTF-8 text file from the current workspace."""
    
    try:
        fd = _open_workspace_file(workspace_root, path, os.O_RDONLY)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"File not found: {path}") from exc

    with os.fdopen(fd, "r", encoding="utf-8") as file:
        return file.read()
  
  return read_file

def create_write_file_tool(workspace_root: Path) -> BaseTool:
  
  @tool("write_file")
  def write_file(path: str, content: str) -> str:
    """Write UTF-8 text to a file in the current workspace."""
    
    fd = _open_workspace_file(
        workspace_root,
        path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        create_parents=True,
    )

    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(content)
    
    return f"Wrote file: {path}"
  
  return write_file
