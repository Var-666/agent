from collections.abc import Iterable
from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from flow_agent.tools.executor import DEFAULT_TOOL_TIMEOUT_SECONDS, execute_tool_calls

DEFAULT_MAX_AGENT_STEPS = 8
DEFAULT_MAX_TOOL_CALLS = 16

class AgentLoopError(RuntimeError):
    """Base error for bounded agent execution."""
    
class AgentStepLimitExceeded(AgentLoopError):
  def __init__(self, max_steps: int) -> None:
     super().__init__(f"Agent exceeded maximum step count: {max_steps}")
     
class AgentToolCallLimitExceeded(AgentLoopError):
  def __init__(self, max_tool_calls: int) -> None:
     super().__init__(f"Agent exceeded maximum tool call count: {max_tool_calls}")
     
@dataclass(frozen=True)
class AgentLoopResult:
  messages: tuple[BaseMessage, ...]
  steps: int
  tool_calls: int
  
def run_bounded_agent_loop(
  model_with_tools: Runnable,
  tools: Iterable[BaseTool],
  initial_messages: Iterable[BaseMessage],
  *,
  run_id: str,
  task_id: str,
  max_steps: int = DEFAULT_MAX_AGENT_STEPS,
  max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS,
  tool_timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS
) -> AgentLoopResult:
  
  if max_steps < 1:
    raise ValueError("max_steps must be at least 1")
  
  if max_tool_calls < 0:
    raise ValueError("max_tool_calls cannot be negative")
  
  tools = tuple(tools)
  messages = list(initial_messages)
  
  steps = 0
  total_tool_calls = 0
  
  while True:
    if steps >= max_steps:
      raise AgentStepLimitExceeded(max_steps)
    
    response = model_with_tools.invoke(messages)
    
    if not isinstance(response, AIMessage):
      raise TypeError("Agent model must return an AIMessage")

    steps += 1
    messages.append(response)
    
    tool_calls = tuple(response.tool_calls)
    
    if not tool_calls:
      return AgentLoopResult(
        messages=tuple(messages),
        steps=steps,
        tool_calls=total_tool_calls
      )

    if steps >= max_steps:
      raise AgentStepLimitExceeded(max_steps)
    
    requested_tool_calls = total_tool_calls + len(tool_calls)
    
    if requested_tool_calls > max_tool_calls:
      raise AgentToolCallLimitExceeded(max_tool_calls)
    
    tool_messages = execute_tool_calls(
      tool_calls=tool_calls,
      tools=tools,
      run_id=run_id,
      task_id=task_id,
      timeout_seconds=tool_timeout_seconds
    )
    
    total_tool_calls = requested_tool_calls
    
    messages.extend(tool_messages)
    
    
  
