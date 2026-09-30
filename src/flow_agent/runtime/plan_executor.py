from collections.abc import Callable

from flow_agent.domain import Run, RunStatus, Task, TaskStatus
from flow_agent.planning import materialize_tasks, ExecutionPlan

TaskRunner = Callable[[Task],None]

class FixedPlanExecutionError(RuntimeError):
  def __init__(self, task_id: str) -> None:
    self.task_id = task_id
    super().__init__(f"Task execution failed: {task_id}")
    
def create_run_from_plan(plan: ExecutionPlan) -> Run:
  run = Run(goal_id=plan.goal_id)
  run.transition_to(RunStatus.PLANNING)
  
  for task in materialize_tasks(plan):
    run.add_task(task)
    
  return run

def execute_fixed_plan(run: Run, task_runner: TaskRunner) -> Run:
  if run.status != RunStatus.PLANNING:
    raise ValueError("Run must be in PLANNING state")
  
  run.transition_to(RunStatus.RUNNING)
  
  task_by_id = {
    task.id: task
    for task in run.tasks
  }
  
  while True:
    pending_tasks = [
      task
      for task in run.tasks
      if task.status == TaskStatus.PENDING
    ]
    
    if not pending_tasks:
      break
    
    ready_task = next((
      task
      for task in pending_tasks
      if _dependencies_completed(task, task_by_id)
    ),None)
    
    if ready_task is None:
      raise RuntimeError("No executable task found for the fixed plan")
    
    ready_task.transition_to(TaskStatus.RUNNING)
    
    try:
      task_runner(ready_task)
    except Exception as exc:
      ready_task.transition_to(TaskStatus.FAILED)
      run.transition_to(RunStatus.FAILED)
      
      raise FixedPlanExecutionError(ready_task.id) from exc
    
    ready_task.transition_to(TaskStatus.COMPLETED)
    
  run.transition_to(RunStatus.COMPLETED)
    
  return run

    
def _dependencies_completed(task: Task, task_by_id: dict[str, Task]) -> bool:
  return all((
    task_by_id[dependency_id].status == TaskStatus.COMPLETED
    for dependency_id in task.dependencies
  ))