from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from flow_agent.domain.run import Run, RunStatus
from flow_agent.domain.task import Task, TaskStatus
from flow_agent.domain.artifact import Artifact, ArtifactKind
from flow_agent.exceptions import (
    DuplicateTaskError,
    InvalidRunStateTransition,
    InvalidTaskDependency,
    RunNotCompletable,
    ArtifactRunMismatch,
    ArtifactTaskMismatch,
    DuplicateArtifactError,
    TaskDependencyCycle,
    TerminalRunMutationError,
)


def test_create_run():
    run = Run(
        goal_id="goal-001",
    )

    assert run.goal_id == "goal-001"
    assert run.status == RunStatus.QUEUED
    assert run.tasks == ()
    assert run.artifacts == ()
    assert run.started_at is None
    assert run.finished_at is None


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

    assert run.tasks == (task,)


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

    assert run.tasks == (
        search_task,
        read_task,
    )


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

def test_add_artifact():
    run = Run(goal_id="goal-001")

    artifact = Artifact(
        run_id=run.id,
        kind=ArtifactKind.MARKDOWN,
        path="output/report.md",
    )

    run.add_artifact(artifact)

    assert run.artifacts == (artifact,)


def test_add_artifact_produced_by_run_task():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Write report",
        description="Write final report",
    )

    run.add_task(task)

    artifact = Artifact(
        run_id=run.id,
        producer_task_id=task.id,
        kind=ArtifactKind.MARKDOWN,
        path="output/report.md",
    )

    run.add_artifact(artifact)

    assert run.artifacts == (artifact,)

def test_reject_artifact_from_another_run():
    run = Run(goal_id="goal-001")

    artifact = Artifact(
        run_id="another-run",
        kind=ArtifactKind.TEXT,
        path="output/result.txt",
    )

    with pytest.raises(ArtifactRunMismatch):
        run.add_artifact(artifact)

def test_reject_artifact_from_unknown_task():
    run = Run(goal_id="goal-001")

    artifact = Artifact(
        run_id=run.id,
        producer_task_id="missing-task",
        kind=ArtifactKind.TEXT,
        path="output/result.txt",
    )

    with pytest.raises(ArtifactTaskMismatch):
        run.add_artifact(artifact)

def test_reject_duplicate_artifact():
    run = Run(goal_id="goal-001")

    artifact = Artifact(
        run_id=run.id,
        kind=ArtifactKind.TEXT,
        path="output/result.txt",
    )

    run.add_artifact(artifact)

    with pytest.raises(DuplicateArtifactError):
        run.add_artifact(artifact)


def test_reject_task_dependency_cycle():
    task_a = Task(
        id="task-a",
        title="Task A",
        description="Task A",
        dependencies=["task-b"],
    )

    task_b = Task(
        id="task-b",
        title="Task B",
        description="Task B",
        dependencies=["task-a"],
    )

    with pytest.raises(TaskDependencyCycle):
        Run(
            goal_id="goal-001",
            tasks=[task_a, task_b],
        )


def test_tasks_cannot_be_modified_directly():
    run = Run(goal_id="goal-001")

    task = Task(
        title="Search",
        description="Search sources",
    )

    with pytest.raises(AttributeError):
        run.tasks.append(task)

    with pytest.raises(ValidationError):
        run.tasks = (task,)


def test_artifacts_cannot_be_modified_directly():
    run = Run(goal_id="goal-001")

    artifact = Artifact(
        run_id=run.id,
        kind=ArtifactKind.TEXT,
        path="output/result.txt",
    )

    with pytest.raises(AttributeError):
        run.artifacts.append(artifact)

    with pytest.raises(ValidationError):
        run.artifacts = (artifact,)


def test_reject_completed_run_with_pending_task():
    task = Task(
        title="Search",
        description="Search sources",
    )

    with pytest.raises(RunNotCompletable):
        Run(
            goal_id="goal-001",
            status=RunStatus.COMPLETED,
            tasks=[task],
        )


def test_terminal_run_cannot_add_task():
    run = Run(
        goal_id="goal-001",
    )

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)
    run.transition_to(RunStatus.COMPLETED)

    task = Task(
        title="Late task",
        description="Should not be accepted",
    )

    with pytest.raises(TerminalRunMutationError):
        run.add_task(task)


def test_terminal_run_cannot_add_artifact():
    run = Run(
        goal_id="goal-001",
    )

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)
    run.transition_to(RunStatus.COMPLETED)

    artifact = Artifact(
        run_id=run.id,
        kind=ArtifactKind.TEXT,
        path="output/result.txt",
    )

    with pytest.raises(TerminalRunMutationError):
        run.add_artifact(artifact)

def test_run_sets_started_at_when_first_running():
    run = Run(goal_id="goal-001")

    run.transition_to(RunStatus.PLANNING)

    assert run.started_at is None

    run.transition_to(RunStatus.RUNNING)

    assert run.started_at is not None
    assert run.started_at.utcoffset() == timezone.utc.utcoffset(
        run.started_at
    )


def test_run_does_not_reset_started_at_after_wait():
    run = Run(goal_id="goal-001")

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)

    started_at = run.started_at

    run.transition_to(RunStatus.WAITING_USER)
    run.transition_to(RunStatus.RUNNING)

    assert run.started_at == started_at


def test_run_sets_finished_at_when_completed():
    run = Run(goal_id="goal-001")

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.RUNNING)
    run.transition_to(RunStatus.COMPLETED)

    assert run.finished_at is not None
    assert (
        run.finished_at.utcoffset()
        == timezone.utc.utcoffset(
            run.finished_at
        )
    )


def test_failed_run_sets_finished_at():
    run = Run(goal_id="goal-001")

    run.transition_to(RunStatus.PLANNING)
    run.transition_to(RunStatus.FAILED)

    assert run.finished_at is not None


def test_cancelled_run_sets_finished_at():
    run = Run(goal_id="goal-001")

    run.transition_to(RunStatus.CANCELLED)

    assert run.finished_at is not None


def test_run_rejects_naive_started_at():
    with pytest.raises(ValidationError):
        Run(
            goal_id="goal-001",
            started_at=datetime.now(),
        )


def test_run_rejects_finished_at_before_started_at():
    started_at = datetime(
        2026,
        9,
        23,
        10,
        0,
        tzinfo=timezone.utc,
    )

    finished_at = datetime(
        2026,
        9,
        23,
        9,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(ValidationError):
        Run(
            goal_id="goal-001",
            status=RunStatus.FAILED,
            started_at=started_at,
            finished_at=finished_at,
        )
