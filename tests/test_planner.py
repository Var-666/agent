from unittest.mock import Mock

from langchain_core.language_models.chat_models import BaseChatModel

from flow_agent.domain import Goal
from flow_agent.planning.planner import StructuredPlanner
from flow_agent.planning.schema import (
    PlanDraft,
    PlanTask,
)

import pytest

from langchain_core.exceptions import (
    OutputParserException,
)

from flow_agent.exceptions import (
    PlannerModelError,
    PlannerOutputError,
)

def make_goal() -> Goal:
    return Goal(
        title="Research LangChain",
        description="Research recent LangChain updates",
    )


def test_planner_binds_plan_draft_schema():
    model = Mock(spec=BaseChatModel)
    structured_model = Mock()

    model.with_structured_output.return_value = (
        structured_model
    )

    StructuredPlanner(model)

    model.with_structured_output.assert_called_once_with(
        PlanDraft
    )
    
def test_planner_creates_execution_plan():
    model = Mock(spec=BaseChatModel)
    structured_model = Mock()

    model.with_structured_output.return_value = (
        structured_model
    )

    structured_model.invoke.return_value = PlanDraft(
        summary="Research and write a report",
        tasks=[
            PlanTask(
                key="search",
                title="Search",
                description="Search official sources",
            ),
            PlanTask(
                key="write",
                title="Write",
                description="Write the report",
                dependencies=["search"],
            ),
        ],
    )

    planner = StructuredPlanner(model)

    goal = Goal(
        title="Research LangChain",
        description=(
            "Research important LangChain updates "
            "from the last 7 days"
        ),
        success_criteria=[
            "Use reliable sources",
        ],
        requested_outputs=[
            "markdown_report",
        ],
    )

    plan = planner.plan(goal)

    assert plan.goal_id == goal.id
    assert plan.summary == "Research and write a report"

    assert len(plan.tasks) == 2

    assert plan.tasks[0].key == "search"
    assert plan.tasks[1].dependencies == (
        "search",
    )
    
    prompt_value = (
    structured_model.invoke.call_args.args[0]
)

    messages = prompt_value.to_messages()

    assert len(messages) == 2

    human_message = messages[1]

    assert "Research LangChain" in human_message.content
    assert "last 7 days" in human_message.content
    assert "Use reliable sources" in human_message.content
    assert "markdown_report" in human_message.content
    
def test_planner_prompt_contains_goal_fields():
    model = Mock(spec=BaseChatModel)
    structured_model = Mock()

    model.with_structured_output.return_value = (
        structured_model
    )

    structured_model.invoke.return_value = PlanDraft(
        summary="Test plan",
        tasks=[
            PlanTask(
                key="search",
                title="Search",
                description="Search sources",
            ),
        ],
    )

    goal = Goal(
        title="Goal title",
        description="Goal description",
        success_criteria=["criterion-a"],
        requested_outputs=["report.md"],
    )

    planner = StructuredPlanner(model)
    planner.plan(goal)

    prompt_value = (
        structured_model.invoke.call_args.args[0]
    )

    messages = prompt_value.to_messages()
    human_content = messages[1].content

    assert "Goal title" in human_content
    assert "Goal description" in human_content
    assert "criterion-a" in human_content
    assert "report.md" in human_content
    
def test_planner_wraps_invalid_output_error():
    model = Mock(spec=BaseChatModel)
    structured_model = Mock()

    model.with_structured_output.return_value = (
        structured_model
    )

    structured_model.invoke.side_effect = (
        OutputParserException(
            "Invalid structured output"
        )
    )

    planner = StructuredPlanner(model)

    with pytest.raises(
        PlannerOutputError
    ) as exc_info:
        planner.plan(make_goal())

    assert isinstance(
        exc_info.value.__cause__,
        OutputParserException,
    )
    
def test_planner_wraps_model_error():
    model = Mock(spec=BaseChatModel)
    structured_model = Mock()

    model.with_structured_output.return_value = (
        structured_model
    )

    structured_model.invoke.side_effect = RuntimeError(
        "provider unavailable"
    )

    planner = StructuredPlanner(model)

    with pytest.raises(
        PlannerModelError
    ) as exc_info:
        planner.plan(make_goal())

    assert isinstance(
        exc_info.value.__cause__,
        RuntimeError,
    )
    
    