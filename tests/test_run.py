import pytest

from pydantic import ValidationError

from flow_agent.domain.run import Run, RunStatus
from flow_agent.domain.task import Task, TaskStatus
from flow_agent.exceptions import (
    DuplicateTaskError,
    InvalidRunStateTransition,
    InvalidTaskDependency,
    RunNotCompletable,
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

def test_run_can_follow_normal_lifecycle():
    run = Run(goal_id="goal-001")

    run.transition_to(RunStatus.PLANNING)
    assert run.status == RunStatus.PLANNING

    run.transition_to(RunStatus.RUNNING)
    assert run.status == RunStatus.RUNNING

def test_queued_run_cannot_complete_directly():
    run = Run(goal_id="goal-001")

    with pytest.raises(InvalidRunStateTransition):
        run.transition_to(RunStatus.COMPLETED)

def test_run_can_wait_for_user_and_resume():
    run = Run(goal_id="goal-001")

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)

    run.transition_to(RunStatus.WAITING_USER)

    assert run.status == RunStatus.WAITING_USER

    run.transition_to(RunStatus.RUNNING)

    assert run.status == RunStatus.RUNNING

def test_run_can_complete_when_all_tasks_completed():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Search",
        description="Search official sources",
    )

    run.add_task(task)

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)

    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.COMPLETED)

    run.transition_to(RunStatus.COMPLETED)

    assert run.status == RunStatus.COMPLETED

def test_run_cannot_complete_with_pending_task():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Search",
        description="Search official sources",
    )

    run.add_task(task)

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)

    with pytest.raises(RunNotCompletable):
        run.transition_to(RunStatus.COMPLETED)

    assert run.status == RunStatus.RUNNING

def test_skipped_task_does_not_block_run_completion():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Optional task",
        description="Optional work",
    )

    run.add_task(task)

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)

    task.transition_to(TaskStatus.SKIPPED)

    run.transition_to(RunStatus.COMPLETED)

    assert run.status == RunStatus.COMPLETED

def test_failed_task_blocks_run_completion():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Search",
        description="Search official sources",
    )

    run.add_task(task)

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)

    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.FAILED)

    with pytest.raises(RunNotCompletable):
        run.transition_to(RunStatus.COMPLETED)

def test_completed_run_is_terminal():
    run = Run(goal_id="goal-001")

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)
    run.transition_to(RunStatus.COMPLETED)

    with pytest.raises(InvalidRunStateTransition):
        run.transition_to(RunStatus.RUNNING)

def test_run_status_cannot_be_modified_directly():
    run = Run(goal_id="goal-001")

    with pytest.raises(ValidationError):
        run.status = RunStatus.COMPLETED