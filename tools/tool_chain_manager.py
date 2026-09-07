from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .tool import ToolArguments, ToolRegistry, ToolResult


@dataclass(frozen=True)
class ToolChainStep:
  tool_name: str
  arguments_template: ToolArguments
  output_key: str

class ToolChain:
  """Toolchain - Supports the sequential execution of multiple tools."""

  def __init__(self,name:str,description:str):
    self.name = name
    self.description = description
    self.steps:List[ToolChainStep] = []

  def add_step(
      self,
      tool_name:str,
      arguments_template:ToolArguments,
      output_key:Optional[str] = None):
    """
    Steps for adding a tool execution

    Args:
      tool_name: Name of the tool
      arguments_template: Tool argument templates, supports variable substitution
      output_key: Key name for the output result, used for reference in subsequent steps
    """
    if not isinstance(arguments_template, dict):
      raise TypeError("Tool arguments template must be a dictionary")

    self.steps.append(ToolChainStep(
      tool_name=tool_name,
      arguments_template=arguments_template.copy(),
      output_key=output_key or f"step_{len(self.steps)}_result"
    ))

  @classmethod
  def _render_template(cls,value:Any,context:Dict[str,Any]) -> Any:
    """Render placeholders recursively while preserving exact-value types."""
    if isinstance(value,str):
      if value.startswith("{") and value.endswith("}") and value.count("{") == 1:
        key = value[1:-1]
        if key in context:
          return context[key]
      return value.format(**context)

    if isinstance(value,dict):
      return {
        key:cls._render_template(item,context)
        for key,item in value.items()
      }

    if isinstance(value,list):
      return [cls._render_template(item,context) for item in value]

    if isinstance(value,tuple):
      return tuple(cls._render_template(item,context) for item in value)

    return value

  def execute(
      self,
      registry:ToolRegistry,
      initial_input:Any,
      context:Optional[Dict[str,Any]] = None) -> ToolResult:
    """execute tool chain"""

    if not self.steps:
      raise ValueError(f"Toolchain '{self.name}' has no steps")

    execution_context = dict(context) if context is not None else {}
    execution_context["input"] = initial_input

    print(f"🔗 starting toolchain execution: {self.name}")

    for i,step in enumerate(self.steps,1):
      try:
        arguments = self._render_template(
          step.arguments_template,
          execution_context
        )
      except KeyError as e:
        raise ValueError(
          f"Toolchain '{self.name}' template variable {e} not found"
        ) from e

      preview = repr(arguments)[:80]
      print(f"Step {i}: Using {step.tool_name} with {preview}")

      result = registry.execute_tool(step.tool_name,arguments)
      execution_context[step.output_key] = result

      print(f"✅ Step {i} complete, result length: {len(result)} characters")

    final_result = execution_context[self.steps[-1].output_key]
    print(f"🎉 Toolchain '{self.name}' execution complete")
    return final_result

class ToolChainManager:
  """ToolChainManager"""

  def __init__(self,registry:ToolRegistry):
    self.registry = registry
    self.chains:Dict[str,ToolChain] = {}

  def register_chain(self,chain:ToolChain):
    self.chains[chain.name] = chain

  def execute_chain(
      self,
      chain_name:str,
      input_data:Any,
      context:Optional[Dict[str,Any]] = None) -> ToolResult:
    if chain_name not in self.chains:
      raise ValueError(f"Toolchain '{chain_name}' does not exist")

    chain = self.chains[chain_name]
    return chain.execute(self.registry,input_data,context)

  def list_chains(self) -> List[str]:
    return list(self.chains.keys())
