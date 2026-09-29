import logging
from collections.abc import Iterable, Callable
from time import perf_counter
from concurrent.futures import ThreadPoolExecutor

from langchain_core.messages import ToolCall, ToolMessage
from langchain_core.tools import BaseTool

Clock = Callable[[],float]

_LOGGER = logging.getLogger(__name__)
DEFAULT_MAX_PARALLEL_TOOL_CALLS = 4

def execute_tool_call(
  tool_call: ToolCall, 
  tools: Iterable[BaseTool],
  *,
  run_id: str,
  task_id: str,
  clock: Clock = perf_counter,
  logger: logging.Logger = _LOGGER
) -> ToolMessage:
  
  if not run_id.strip():
    raise ValueError("run_id cannot be empty")
  
  if not task_id.strip():
    raise ValueError("task_id cannot be empty")
  
  tool_by_name = _index_tools(tools)
  
  tool_name = tool_call["name"]
  tool_call_id = tool_call["id"]
  
  if tool_call_id is None:
    raise ValueError("Tool call must have an id")
  
  if tool_name not in tool_by_name:
    raise ValueError(f"Unknown tool: {tool_name}")
  
  tool = tool_by_name[tool_name]
  
  started_at = clock()
  error: str | None = None
  
  try:
    result = tool.invoke(tool_call["args"])
    
    message = ToolMessage(
      content=str(result),
      tool_call_id=tool_call_id,
      status="success"
    )
  except Exception as exc:
    error = (f"{type(exc).__name__}:{exc}")
    
    message =  ToolMessage(
      content=str(exc),
      tool_call_id=tool_call_id,
      status="error"
    )
    
  latency_ms = (clock() - started_at) * 1000
  
  logger.info(
        (
            "tool_call "
            "run_id=%s "
            "task_id=%s "
            "tool_call_id=%s "
            "tool_name=%s "
            "latency_ms=%.3f "
            "error=%s"
        ),
        run_id,
        task_id,
        tool_call_id,
        tool_name,
        latency_ms,
        error,
        extra={
            "run_id": run_id,
            "task_id": task_id,
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "latency_ms": latency_ms,
            "error": error,
        },
    )

  return message
  
def execute_tool_calls(
    tool_calls: Iterable[ToolCall],
    tools: Iterable[BaseTool],
    *,
    run_id: str,
    task_id: str,
    clock: Clock = perf_counter,
    logger: logging.Logger = _LOGGER,
) -> tuple[ToolMessage, ...]:
    available_tools = tuple(tools)

    return tuple(
        execute_tool_call(
            tool_call,
            available_tools,
            run_id=run_id,
            task_id=task_id,
            clock=clock,
            logger=logger,
        )
        for tool_call in tool_calls
    )
  
def execute_tool_calls_parallel(
  tool_calls: Iterable[ToolCall],
  tools: Iterable[BaseTool],
  *,
  run_id: str,
  task_id: str,
  max_workers: int = (DEFAULT_MAX_PARALLEL_TOOL_CALLS),
  clock: Clock = perf_counter,
  logger: logging.Logger = _LOGGER
) -> tuple[ToolMessage,...]:
  
  if max_workers < 1:
    raise ValueError("max_workers must be at least 1")
  
  available_tools = tuple(tools)
  calls = tuple(tool_calls)
  
  if not calls:
    return ()
  
  worker_count = min(max_workers, len(calls))
  
  with ThreadPoolExecutor(max_workers=worker_count) as pool:
    futures = [
      pool.submit(
        execute_tool_call,
        tool_call,
        available_tools,
        run_id=run_id,
        task_id=task_id,
        clock=clock,
        logger=logger,
      )
      for tool_call in calls
    ]
  
  return tuple(
            future.result()
            for future in futures
        )
    
def _index_tools(tools: Iterable[BaseTool]) -> dict[str,BaseTool]:
  tool_by_name: dict[str, BaseTool] = {}

  for tool in tools:
      if tool.name in tool_by_name:
          raise ValueError(f"Duplicate tool name: {tool.name}")

      tool_by_name[tool.name] = tool

  return tool_by_name