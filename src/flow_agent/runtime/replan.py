from collections.abc import Callable

from flow_agent.domain import Run, RunEvent, RunEventKind, Task
from flow_agent.planning import ExecutionPlan, materialize_tasks

EventSink = Callable[[RunEvent], None]

def apply_replan(
  run: Run,
  plan: ExecutionPlan,
  *,
  event_sink: EventSink | None
) -> None:
  if plan.goal_id != run.goal_id:
    raise ValueError("Replan goal_id must match Run goal_id")

  replacement_tasks = materialize_tasks(plan)
  
  superseded_task_ids = run.supersede_unfinished_tasks(replacement_tasks)
  
  _emit_replan_applied(
        run=run,
        superseded_task_ids=superseded_task_ids,
        replacement_tasks=replacement_tasks,
        event_sink=event_sink,
    )
  

def _emit_replan_applied(
  *,
  run: Run,
  superseded_task_ids: tuple[str,...],
  replacement_tasks: tuple[Task,...],
  event_sink: EventSink | None
) -> None:
  if event_sink is None:
        return

  event_sink(
      RunEvent(
          run_id=run.id,
          kind=RunEventKind.REPLAN_APPLIED,
          payload={
              "superseded_task_ids": list(superseded_task_ids),
              "new_task_ids": [
                  task.id
                  for task
                  in replacement_tasks
              ],
          },
      )
  )