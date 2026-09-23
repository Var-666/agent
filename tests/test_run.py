import pytest

from flow_agent.domain.run import Run, RunStatus
from flow_agent.domain.task import Task
from flow_agent.exceptions import (
    DuplicateTaskError,
    InvalidTaskDependency,
)


def test_create_run():
    run = Run(
        goal_id="goal-001",
    )

    assert run.goal_id == "goal-001"
    assert run.status == RunStatus.QUEUED
    assert run.tasks == []


def test_run_generates_unique_ids():
    run1 = Run(goal_id="goal-001")
    run2 = Run(goal_id="goal-001")

    assert run1.id != run2.id


def test_add_task():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Search",
        description="Search official sources",
    )

    run.add_task(task)

    assert run.tasks == [task]


def test_add_task_with_valid_dependency():
    run = Run(goal_id="goal-001")

    search_task = Task(
        title="Search",
        description="Search official sources",
    )

    read_task = Task(
        title="Read",
        description="Read search results",
        dependencies=[search_task.id],
    )

    run.add_task(search_task)
    run.add_task(read_task)

    assert run.tasks == [
        search_task,
        read_task,
    ]


def test_reject_duplicate_task():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Search",
        description="Search official sources",
    )

    run.add_task(task)

    with pytest.raises(DuplicateTaskError):
        run.add_task(task)


def test_reject_missing_dependency():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Read",
        description="Read source",
        dependencies=["missing-task"],
    )

    with pytest.raises(InvalidTaskDependency):
        run.add_task(task)


def test_reject_self_dependency():
    run = Run(goal_id="goal-001")

    task = Task(
        id="task-001",
        title="Search",
        description="Search source",
        dependencies=["task-001"],
    )

    with pytest.raises(InvalidTaskDependency):
        run.add_task(task)