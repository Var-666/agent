from pathlib import Path,PureWindowsPath

from langchain.tools import tool
from langchain_core.tools import BaseTool

def create_read_file_tool(workspace_root: Path) -> BaseTool:
  
  @tool("read_file")
  def read_file(path: str) -> str:
    """Read a UTF-8 text file from the current workspace."""
    
    raw_path = path.strip()
    
    if not raw_path:
      raise ValueError("File path cannot be empty")
    
    
    windows_path = PureWindowsPath(raw_path)
    
    if (Path(raw_path).is_absolute() or windows_path.is_absolute() or windows_path.drive):
      raise ValueError("File path must be relative to the workspace")
    
    
    relative_path = Path(raw_path.replace("\\","/"))
  
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