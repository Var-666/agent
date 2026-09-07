import asyncio
import concurrent.futures
from typing import List

from .tool import ToolCall, ToolRegistry, ToolResult

class AsyncToolExecutor:

  def __init__(self,registry:ToolRegistry,max_workers:int = 4):
    self.registry = registry
    self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

  async def execute_tool_async(self,call:ToolCall) -> ToolResult:
    loop = asyncio.get_running_loop()

    return await loop.run_in_executor(
      self.executor,
      self.registry.execute_tool,
      call.tool_name,
      call.arguments
    )

  async def execute_tools_parallel(self,calls:List[ToolCall]) -> List[ToolResult]:
    print(f"🚀 Starting parallel execution of {len(calls)} tool tasks")

    async_tasks = [self.execute_tool_async(call) for call in calls]

    results = await asyncio.gather(*async_tasks)

    print(f"✅ All tool tasks completed")
    return results

  def shutdown(self,wait:bool = True):
    """Release worker threads owned by this executor."""
    self.executor.shutdown(wait=wait)

  async def __aenter__(self):
    return self

  async def __aexit__(self,exc_type,exc_value,traceback):
    self.shutdown()

  def __del__(self):
    if hasattr(self,'executor'):
      self.executor.shutdown(wait=False)
