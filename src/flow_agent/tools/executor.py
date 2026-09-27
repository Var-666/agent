from collections.abc import Iterable

from langchain_core.messages import ToolCall, ToolMessage
from langchain_core.tools import BaseTool

def execute_tool_call(tool_call: ToolCall, tools: Iterable[BaseTool]) -> ToolMessage:
  tool_by_name = _index_tools(tools)
  
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
  
def execute_tool_calls(tool_calls:Iterable[ToolCall], tools:Iterable[BaseTool]) -> tuple[ToolMessage,...]:
  available_tools = tuple(tools)
  
  return tuple(
    execute_tool_call(tool_call,available_tools)
    for tool_call in tool_calls
  )
  
def _index_tools(tools: Iterable[BaseTool]) -> dict[str,BaseTool]:
  tool_by_name: dict[str, BaseTool] = {}

  for tool in tools:
      if tool.name in tool_by_name:
          raise ValueError(f"Duplicate tool name: {tool.name}")

      tool_by_name[tool.name] = tool

  return tool_by_name