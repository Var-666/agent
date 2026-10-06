from collections.abc import Callable, Iterable

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from flow_agent.domain import Run, Task
from flow_agent.runtime.agent_loop import (
  DEFAULT_MAX_AGENT_STEPS,
  DEFAULT_MAX_TOOL_CALLS,
  run_bounded_agent_loop
)
from flow_agent.tools.executor import DEFAULT_TOOL_TIMEOUT_SECONDS

TaskMessageFactory = Callable[[Task],Iterable[BaseMessage]]

def default_task_messages(task: Task) -> tuple[BaseMessage,...]:
  return (HumanMessage(
    content=(
          f"Task: {task.title}\n\n"
          f"{task.description}"
      )
    ),
  )
def create_agent_task_runner(
  run: Run,
  model_with_tools: Runnable,
  tools: Iterable[BaseTool],
  *,
  message_factory: TaskMessageFactory = default_task_messages,
  max_steps: int = DEFAULT_MAX_AGENT_STEPS,
  max_tool_calls: int = DEFAULT_MAX_TOOL_CALLS,
  tool_timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS
) -> Callable[[Task],None]:
  tools = tuple(tools)
  
  def task_runner(task: Task) -> None:
    run_bounded_agent_loop(
      model_with_tools,
      tools,
      message_factory(task),
      run_id=run.id,
      task_id=task.id,
      max_steps=max_steps,
      max_tool_calls=max_tool_calls,
      tool_timeout_seconds=tool_timeout_seconds
    )
    
  return task_runner