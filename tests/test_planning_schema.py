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


def test_plan_rejects_duplicate_task_keys():
    with pytest.raises(ValidationError):
        ExecutionPlan(
            goal_id="goal-001",
            summary="Invalid plan",
            tasks=[
                PlanTask(
                    key="search",
                    title="Search A",
                    description="Search A",
                ),
                PlanTask(
                    key="search",
                    title="Search B",
                    description="Search B",
                ),
            ],
        )


def test_plan_rejects_unknown_dependency():
    with pytest.raises(ValidationError):
        ExecutionPlan(
            goal_id="goal-001",
            summary="Invalid plan",
            tasks=[
                PlanTask(
                    key="write",
                    title="Write",
                    description="Write report",
                    dependencies=["search"],
                ),
            ],
        )


def test_plan_rejects_self_dependency():
    with pytest.raises(ValidationError):
        ExecutionPlan(
            goal_id="goal-001",
            summary="Invalid plan",
            tasks=[
                PlanTask(
                    key="search",
                    title="Search",
                    description="Search sources",
                    dependencies=["search"],
                ),
            ],
        )


def test_plan_rejects_dependency_cycle():
    with pytest.raises(ValidationError):
        ExecutionPlan(
            goal_id="goal-001",
            summary="Invalid plan",
            tasks=[
                PlanTask(
                    key="a",
                    title="A",
                    description="Task A",
                    dependencies=["b"],
                ),
                PlanTask(
                    key="b",
                    title="B",
                    description="Task B",
                    dependencies=["c"],
                ),
                PlanTask(
                    key="c",
                    title="C",
                    description="Task C",
                    dependencies=["a"],
                ),
            ],
        )


def test_plan_allows_dependency_on_later_task():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Valid plan",
        tasks=[
            PlanTask(
                key="write",
                title="Write",
                description="Write report",
                dependencies=["search"],
            ),
            PlanTask(
                key="search",
                title="Search",
                description="Search sources",
            ),
        ],
    )

    assert plan.tasks[0].dependencies == ("search",)

def test_plan_task_is_immutable():
    task = PlanTask(
        key="search",
        title="Search",
        description="Search sources",
    )

    with pytest.raises(ValidationError):
        task.dependencies = ("missing",)
        
def test_execution_plan_is_immutable():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Search sources",
        tasks=[
            PlanTask(
                key="search",
                title="Search",
                description="Search sources",
            ),
        ],
    )

    with pytest.raises(ValidationError):
        plan.summary = "Changed"