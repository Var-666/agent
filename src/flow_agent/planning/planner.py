from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.exceptions import OutputParserException

from pydantic import ValidationError

from flow_agent.domain import Goal
from flow_agent.planning.prompt import PLANNER_PROMPT
from flow_agent.planning.schema import PlanDraft, ExecutionPlan
from flow_agent.exceptions import PlannerModelError, PlannerOutputError

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
    
    try:
      draft = self._structured_model.invoke(prompt_value)
    except (ValidationError,OutputParserException) as exc:
      raise PlannerOutputError() from exc
    except Exception as exc:
        raise PlannerModelError() from exc
      
    return ExecutionPlan(
            goal_id=goal.id,
            summary=draft.summary,
            tasks=draft.tasks,
        )