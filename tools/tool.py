from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, List, TypeAlias, TypeVar

from pydantic import BaseModel, Field


ToolArguments: TypeAlias = Dict[str, Any]
ToolResult: TypeAlias = str
ArgumentsModelT = TypeVar("ArgumentsModelT",bound=BaseModel)


class ToolCall(BaseModel):
  """A normalized request to execute a tool."""

  tool_name: str
  arguments: ToolArguments = Field(default_factory=dict)

class Tool(ABC,Generic[ArgumentsModelT]):
  """tool base class"""

  def __init__(
      self,
      name:str,
      description:str,
      arguments_model:type[ArgumentsModelT]):
    self.name = name
    self.description = description
    self.arguments_model = arguments_model

  def invoke(self,arguments:ToolArguments) -> ToolResult:
    """Validate raw arguments before running the tool."""
    validated_arguments = self.arguments_model.model_validate(arguments)
    result = self.run(validated_arguments)

    if not isinstance(result,str):
      raise TypeError(f"Tool '{self.name}' must return a string")

    return result

  @abstractmethod
  def run(self,arguments:ArgumentsModelT) -> ToolResult:
    """run tool"""
    pass

  def to_openai_schema(self) -> Dict[str,Any]:
      """
        Convert to OpenAI function calling schema format
        Used for FunctionCallAgent to enable tools to be used with OpenAI's native function calling

        Returns:
          A schema compliant with OpenAI function calling standards
      """
      return {
        "type":"function",
        "function":{
          "name":self.name,
          "description":self.description,
          "parameters":self.arguments_model.model_json_schema()
        }
      }

class ToolRegistry:
  """tool registry"""

  def __init__(self):
    self._tools:dict[str,Tool[Any]] = {}
    self._functions:dict[str,dict[str,Any]] = {}

  def register_tool(self,tool:Tool[Any]):
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
        return self._tools[name].invoke(arguments.copy())

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
