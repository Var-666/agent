from pathlib import Path

from langchain.tools import tool
from langchain_core.tools import BaseTool

def create_read_file_tool(workspace_root: Path) -> BaseTool:
  
  @tool("read_file")
  def read_file(path: str) -> str:
    """Read a UTF-8 text file from the current workspace."""
    
    relative_path = Path(path)
    
    if relative_path.is_absolute():
      raise ValueError("File path must be relative to the workspace")
  
    if ".." in relative_path.parts:
      raise ValueError("File path cannot escape the workspace")
    
    root = workspace_root.resolve()
    target = (root / relative_path).resolve()
    
    if not target.is_relative_to(root):
      raise ValueError("File path cannot escape the workspace")
    
    if not target.is_file():
      raise FileNotFoundError( f"File not found: {path}")
    
    return target.read_text(encoding="utf-8")
  
  return read_file