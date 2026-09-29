from pathlib import Path

from langchain_core.tools import BaseTool

from flow_agent.tools.file import (
    create_read_file_tool,
    create_write_file_tool,
)
from flow_agent.tools.search import (
    SearchBackend,
    create_search_web_tool,
    create_tavily_search_backend,
)
from flow_agent.tools.web import (
    create_read_url_tool,
)

def create_default_tools(
  workspace_root: Path,
  *,
  search_backend: SearchBackend | None = None  
) -> tuple[BaseTool, ...]:
  if search_backend is None:
    search_backend = create_tavily_search_backend()
    
  return (
    create_search_web_tool(search_backend),
    create_read_url_tool(),
    create_read_file_tool(workspace_root),
    create_write_file_tool(workspace_root)
  )