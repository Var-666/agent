from collections.abc import Iterable

from langchain_core.messages import ToolCall, ToolMessage
from langchain_core.tools import BaseTool

def execute_tool_call(tool_call: ToolCall, tools: Iterable[BaseTool]) -> ToolMessage:
  tool_by_name = {
    tool.name: tool
    for tool in tools
  }
  
  tool_name = tool_call["name"]
  tool_call_id = tool_call["id"]
  
  if tool_call_id is None:
    raise ValueError("Tool call must have an id")
  
  if tool_name not in tool_by_name:
    raise ValueError(f"Unknown tool: {tool_name}")
  
  tool = tool_by_name[tool_name]
  
  try:
    result = tool.invoke(tool_call["args"])
  except Exception as exc:
    return ToolMessage(
      content=str(exc),
      tool_call_id=tool_call_id,
      status="error"
    )
    
  return ToolMessage(
        content=str(result),
        tool_call_id=tool_call_id,
        status="success",
    )