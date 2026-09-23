import pytest
from pydantic import ValidationError

from flow_agent.domain.task import Task, TaskStatus
from flow_agent.exceptions import InvalidTaskStateTransition


def test_create_task():
    task = Task(
        title="搜索官方资料",
        description="搜索 LangChain 最近 7 天的重要更新",
    )

    assert task.title == "搜索官方资料"
    assert task.description == "搜索 LangChain 最近 7 天的重要更新"
    assert task.status == TaskStatus.PENDING
    assert task.dependencies == ()


def test_task_generates_unique_ids():
    task1 = Task(
        title="Task 1",
        description="Description 1",
    )

    task2 = Task(
        title="Task 2",
        description="Description 2",
    )

    assert task1.id != task2.id


def test_task_accepts_dependencies():
    task = Task(
        title="生成报告",
        description="根据资料生成报告",
        dependencies=[
            "task-001",
            "task-002",
        ],
    )

    assert task.dependencies == (
        "task-001",
        "task-002",
    )


def test_task_rejects_invalid_status():
    with pytest.raises(ValidationError):
        Task(
            title="Test",
            description="Test task",
            status="UNKNOWN",
        )


def test_task_requires_non_empty_title():
    with pytest.raises(ValidationError):
        Task(
            title="",
            description="Valid description",
        )


def test_task_requires_non_empty_description():
    with pytest.raises(ValidationError):
        Task(
            title="Valid title",
            description="",
        )


def test_task_id_is_immutable():
    task = Task(
        title="Test",
        description="Test task",
    )

    with pytest.raises(ValidationError):
        task.id = "new-id"


def test_pending_task_can_start():
    task = Task(
        title="Search",
        description="Search official sources",
    )

    task.transition_to(TaskStatus.RUNNING)

    assert task.status == TaskStatus.RUNNING


def test_running_task_can_complete():
    task = Task(
        title="Search",
        description="Search official sources",
    )

    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.COMPLETED)

    assert task.status == TaskStatus.COMPLETED


def test_running_task_can_wait_and_resume():
    task = Task(
        title="Search",
        description="Search official sources",
    )

    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.WAITING)

    assert task.status == TaskStatus.WAITING

    task.transition_to(TaskStatus.RUNNING)

    assert task.status == TaskStatus.RUNNING


def test_pending_task_cannot_complete_directly():
    task = Task(
        title="Search",
        description="Search official sources",
    )

    with pytest.raises(InvalidTaskStateTransition):
        task.transition_to(TaskStatus.COMPLETED)


def test_completed_task_is_terminal():
    task = Task(
        title="Search",
        description="Search official sources",
    )

    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.COMPLETED)

    with pytest.raises(InvalidTaskStateTransition):
        task.transition_to(TaskStatus.RUNNING)


def test_failed_task_is_terminal():
    task = Task(
        title="Search",
        description="Search official sources",
    )

    task.transition_to(TaskStatus.RUNNING)
    task.transition_to(TaskStatus.FAILED)

    with pytest.raises(InvalidTaskStateTransition):
        task.transition_to(TaskStatus.RUNNING)


def test_task_status_cannot_be_modified_directly():
    task = Task(
        title="Search",
        description="Search official sources",
    )

    with pytest.raises(ValidationError):
        task.status = TaskStatus.COMPLETED


def test_task_dependencies_cannot_be_modified_directly():
    task = Task(
        title="Read",
        description="Read sources",
        dependencies=["task-001"],
    )

    with pytest.raises(AttributeError):
        task.dependencies.append("task-002")

    with pytest.raises(ValidationError):
        task.dependencies = ("task-002",)
