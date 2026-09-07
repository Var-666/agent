from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, TypeAlias

from pydantic import BaseModel, Field


ToolArguments: TypeAlias = Dict[str, Any]
ToolResult: TypeAlias = str


class ToolCall(BaseModel):
  """A normalized request to execute a tool."""

  tool_name: str
  arguments: ToolArguments = Field(default_factory=dict)

class ToolParameters(BaseModel):
  """tool parameters"""

  name:str
  type:str
  description:str
  required:bool = True
  default:Any = None

class Tool(ABC):
  """tool base class"""

  def __init__(self,name:str,description:str):
    self.name = name
    self.description = description

  @abstractmethod
  def run(self,arguments:ToolArguments) -> ToolResult:
    """run tool"""
    pass

  @abstractmethod
  def get_parameters(self) -> List[ToolParameters]:
    """get tool parameters"""
    pass

  def to_openai_schema(self) -> Dict[str,Any]:
      """
        Convert to OpenAI function calling schema format
        Used for FunctionCallAgent to enable tools to be used with OpenAI's native function calling

        Returns:
          A schema compliant with OpenAI function calling standards
      """
      parameters = self.get_parameters()

      properties = {}
      required = []

      for param in parameters:
        prop = {
          "type":param.type,
          "description":param.description
        }

        if param.default is not None:
          prop["description"] = f"{param.description} (default: {param.default})"

        if param.type == "array":
          prop["items"] = {"type":"string"}

        properties[param.name] = prop

        if param.required:
          required.append(param.name)

      return {
        "type":"function",
        "function":{
          "name":self.name,
          "description":self.description,
          "parameters":{
            "type":"object",
            "properties":properties,
            "required":required
          }
        }
      }

class ToolRegistry:
  """tool registry"""

  def __init__(self):
    self._tools:dict[str,Tool] = {}
    self._functions:dict[str,dict[str,Any]] = {}

  def register_tool(self,tool:Tool):
    """register tool obj"""
    if tool.name in self._tools:
      print(f"Warning: Tool '{tool.name}' already exists and will be overwritten.")
    self._tools[tool.name] = tool

  def register_function(self,name:str,description:str,func:Callable[...,ToolResult]):
    """
      register functions directly as tools.

      Args:
        name: Tool name
        description: Tool description
        func: Tool function; accepts keyword arguments and returns a string result
    """

    if name in self._functions:
      print(f"Warning: Function '{name}' already exists and will be overwritten.")

    self._functions[name] = {
      "description":description,
      "func":func
    }

  def get_tools_description(self) -> str:
    """get a formatted description string of all available tools."""

    descriptions = []

    for tool in self._tools.values():
      descriptions.append(f"- {tool.name} : {tool.description}")

    for name,info in self._functions.items():
      descriptions.append(f"- {name} : {info['description']}")

    return "\n".join(descriptions) if descriptions else "no use tool"

  def get_tool(self,name:str):
    return self._tools.get(name)

  def execute_tool(self,name:str,arguments:ToolArguments) -> ToolResult:
    if not isinstance(arguments, dict):
      raise TypeError("Tool arguments must be a dictionary")

    if name in self._tools:
        return self._tools[name].run(arguments.copy())

    if name in self._functions:
        func = self._functions[name]["func"]
        return func(**arguments)

    raise ValueError(
        f"Tool '{name}' not found"
    )

  def get_openai_tools(self)->List[Dict[str,Any]]:
    """get the OpenAI Function Calling Schema for all tools."""
    return [
      tool.to_openai_schema()
      for tool in self._tools.values()
    ]