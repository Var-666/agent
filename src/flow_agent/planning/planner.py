from langchain_core.language_models.chat_models import BaseChatModel

from flow_agent.domain import Goal
from flow_agent.planning.prompt import PLANNER_PROMPT
from flow_agent.planning.schema import PlanDraft, ExecutionPlan

class StructuredPlanner:
  def __init__(self,model:BaseChatModel) -> None:
    self._structured_model = model.with_structured_output(PlanDraft)
    
  def plan(self,goal: Goal) -> ExecutionPlan:
    prompt_value = PLANNER_PROMPT.invoke({
      "title":goal.title,
      "description":goal.description,
      "success_criteria":goal.success_criteria,
      "requested_outputs": goal.requested_outputs,
    })
    
    draft = self._structured_model.invoke(prompt_value)
    
    return ExecutionPlan(
            goal_id=goal.id,
            summary=draft.summary,
            tasks=draft.tasks,
        )