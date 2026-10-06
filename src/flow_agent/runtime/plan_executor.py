from collections.abc import Callable
from time import perf_counter

from flow_agent.domain import Run, RunEvent, RunEventKind, RunStatus, Task, TaskStatus
from flow_agent.planning import materialize_tasks, ExecutionPlan

Clock = Callable[[],float]
EventSink = Callable[[RunEvent],None]
TaskRunner = Callable[[Task],None]

DEFAULT_MAX_RUN_SECONDS = 300.0

class FixedPlanExecutionError(RuntimeError):
  def __init__(self, task_id: str) -> None:
    self.task_id = task_id
    super().__init__(f"Task execution failed: {task_id}")
    
class RunTimeLimitExceeded(RuntimeError):
  def __init__(self, max_run_seconds: float) -> None:
    self.max_run_seconds = max_run_seconds
    super().__init__("Run exceeded maximum duration: " f"{max_run_seconds:g} seconds")
    
def create_run_from_plan(plan: ExecutionPlan) -> Run:
  run = Run(goal_id=plan.goal_id)
  run.transition_to(RunStatus.PLANNING)
  
  for task in materialize_tasks(plan):
    run.add_task(task)
    
  return run

def execute_fixed_plan(
  run: Run, 
  task_runner: TaskRunner,
  *,
  max_run_seconds: float = DEFAULT_MAX_RUN_SECONDS,
  clock: Clock = perf_counter,
  event_sink: EventSink | None = None
) -> Run:
  if run.status != RunStatus.PLANNING:
      raise ValueError("Run must be in PLANNING state")
  
  if max_run_seconds <= 0:
    raise ValueError("max_run_seconds must be positive")
  
  started_at = clock()
  
  run.transition_to(RunStatus.RUNNING)
  
  _emit_event(run=run,kind=RunEventKind.RUN_STARTED,event_sink=event_sink)
  
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
    
    _ensure_within_run_budget(
      run=run,
      started_at=started_at,
      max_run_seconds=max_run_seconds,
      clock=clock,
      event_sink=event_sink
    )
    
    ready_task = next((
      task
      for task in pending_tasks
      if _dependencies_completed(task, task_by_id)
    ),None)
    
    if ready_task is None:
      run.transition_to(RunStatus.FAILED)
      
      _emit_event(
                run=run,
                kind=RunEventKind.RUN_FAILED,
                event_sink=event_sink,
                payload={
                    "reason":"no_executable_task",
                },
            )
      
      raise RuntimeError("No executable task found for the fixed plan")
    
    ready_task.transition_to(TaskStatus.RUNNING)
    
    _emit_event(
            run=run,
            task_id=ready_task.id,
            kind=RunEventKind.TASK_STARTED,
            event_sink=event_sink,
        )
    
    try:
      task_runner(ready_task)
    except Exception as exc:
      ready_task.transition_to(TaskStatus.FAILED)
      
      _emit_event(
                run=run,
                task_id=ready_task.id,
                kind=RunEventKind.TASK_FAILED,
                event_sink=event_sink,
                payload={
                    "error_type":type(exc).__name__,
                    "error":str(exc),
                },
            )
      
      run.transition_to(RunStatus.FAILED)
      
      _emit_event(
                run=run,
                kind=RunEventKind.RUN_FAILED,
                event_sink=event_sink,
                payload={
                    "reason":"task_failed",
                    "task_id":ready_task.id,
                },
            )
      
      raise FixedPlanExecutionError(ready_task.id) from exc
    
    ready_task.transition_to(TaskStatus.COMPLETED)
    
    _emit_event(
            run=run,
            task_id=ready_task.id,
            kind=RunEventKind.TASK_COMPLETED,
            event_sink=event_sink,
        )
    
  _ensure_within_run_budget(
        run=run,
        started_at=started_at,
        max_run_seconds=max_run_seconds,
        clock=clock,
        event_sink=event_sink,
    )
  
  run.transition_to(RunStatus.COMPLETED)
  
  _emit_event(
        run=run,
        kind=RunEventKind.RUN_COMPLETED,
        event_sink=event_sink,
    )
    
  return run

    
def _dependencies_completed(task: Task, task_by_id: dict[str, Task]) -> bool:
  return all((
    task_by_id[dependency_id].status == TaskStatus.COMPLETED
    for dependency_id in task.dependencies
  ))

def _emit_event(
  *, 
  run: Run,
  kind: RunEventKind,
  event_sink: EventSink | None,
  task_id: str | None = None,
  payload: dict | None = None  
) -> None:
  if event_sink is None:
    return
  
  event_sink(
    RunEvent(
      run_id=run.id,
      task_id=task_id,
      kind=kind,
      payload=payload or {}
    )
  )

def _ensure_within_run_budget(
  *,
  run:Run,
  started_at: float,
  max_run_seconds: float,
  clock: Clock,
  event_sink: EventSink | None
) -> None:
  elapsed = clock() - started_at
  
  if elapsed < max_run_seconds:
    return
  
  run.transition_to(RunStatus.FAILED)
  
  _emit_event(
        run=run,
        kind=RunEventKind.RUN_FAILED,
        event_sink=event_sink,
        payload={
            "reason":"time_limit_exceeded",
            "max_run_seconds":max_run_seconds,
            "elapsed_seconds":elapsed,
        },
    )
  
  raise RunTimeLimitExceeded(max_run_seconds)