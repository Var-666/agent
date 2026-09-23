import pytest
from pydantic import ValidationError

from flow_agent.planning.schema import (
    ExecutionPlan,
    PlanTask,
)


def test_create_execution_plan():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Research and write a report.",
        tasks=[
            PlanTask(
                key="search",
                title="Search",
                description="Search official sources.",
            ),
            PlanTask(
                key="write",
                title="Write",
                description="Write the final report.",
                dependencies=["search"],
            ),
        ],
    )

    assert plan.goal_id == "goal-001"
    assert plan.summary == "Research and write a report."
    assert len(plan.tasks) == 2

    assert plan.tasks[0].key == "search"
    assert plan.tasks[1].dependencies == ("search",)


def test_plan_requires_at_least_one_task():
    with pytest.raises(ValidationError):
        ExecutionPlan(
            goal_id="goal-001",
            summary="Empty plan",
            tasks=[],
        )


def test_plan_task_requires_key():
    with pytest.raises(ValidationError):
        PlanTask(
            key="",
            title="Search",
            description="Search sources.",
        )


def test_plan_task_requires_title():
    with pytest.raises(ValidationError):
        PlanTask(
            key="search",
            title="",
            description="Search sources.",
        )