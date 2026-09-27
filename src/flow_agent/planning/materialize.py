from flow_agent.domain import Task
from flow_agent.planning.schema import ExecutionPlan, PlanTask

def materialize_tasks(plan: ExecutionPlan) -> tuple[Task,...]:
  ordered_plan_tasks = _topological_order(plan)
  
  created: dict[str,Task] = {}
  
  for plan_task in ordered_plan_tasks:
    dependencies = tuple(created[dependency_key].id for dependency_key in plan_task.dependencies)
    
    created[plan_task.key] = Task(
      title=plan_task.title,
      description=plan_task.description,
      dependencies=dependencies
    )
    
  return tuple(
    created[plan_task.key]
    for plan_task in ordered_plan_tasks
  )
   

def _topological_order(plan: ExecutionPlan) -> tuple[PlanTask,...]:
  task_by_key = {task.key : task for task in plan.tasks}
  
  visited: set[str] = set()
  ordered: list[PlanTask] = []
  
  def visit(task_key: str) -> None:
    if task_key in visited:
      return
    
    task = task_by_key[task_key]
    
    for dependency_key in task.dependencies:
      visit(dependency_key)
      
    visited.add(task_key)
    ordered.append(task)
    
  for task in plan.tasks:
    visit(task.key)
  
  return tuple(ordered)
  
  