import pytest

from flow_agent.domain import (
    RunStatus,
    TaskStatus,
)
from flow_agent.planning.schema import (
    ExecutionPlan,
    PlanTask,
)
from flow_agent.runtime.plan_executor import (
    FixedPlanExecutionError,
    create_run_from_plan,
    execute_fixed_plan,
)


def make_plan() -> ExecutionPlan:
    return ExecutionPlan(
        goal_id="goal-001",
        summary="Test plan",
        tasks=(
            PlanTask(
                key="report",
                title="Write report",
                description="Write the report",
                dependencies=(
                    "research",
                ),
            ),
            PlanTask(
                key="research",
                title="Research",
                description="Research sources",
            ),
        ),
    )
    
def test_create_run_from_plan_materializes_tasks():
    run = create_run_from_plan(
        make_plan()
    )

    assert run.goal_id == "goal-001"

    assert (
        run.status
        == RunStatus.PLANNING
    )

    assert len(run.tasks) == 2

    assert [
        task.title
        for task in run.tasks
    ] == [
        "Research",
        "Write report",
    ]

    research = run.tasks[0]
    report = run.tasks[1]

    assert report.dependencies == (
        research.id,
    )

    assert all(
        task.status
        == TaskStatus.PENDING
        for task in run.tasks
    )
    
def test_execute_fixed_plan_completes_tasks_in_dependency_order():
    run = create_run_from_plan(
        make_plan()
    )

    executed = []

    def task_runner(task):
        executed.append(
            task.title
        )

    result = execute_fixed_plan(
        run,
        task_runner,
    )

    assert result is run

    assert executed == [
        "Research",
        "Write report",
    ]

    assert all(
        task.status
        == TaskStatus.COMPLETED
        for task in run.tasks
    )

    assert (
        run.status
        == RunStatus.COMPLETED
    )

    assert run.started_at is not None
    assert run.finished_at is not None
    
def test_execute_fixed_plan_stops_after_task_failure():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Failure test",
        tasks=(
            PlanTask(
                key="a",
                title="Task A",
                description="A",
            ),
            PlanTask(
                key="b",
                title="Task B",
                description="B",
                dependencies=("a",),
            ),
            PlanTask(
                key="c",
                title="Task C",
                description="C",
                dependencies=("b",),
            ),
        ),
    )

    run = create_run_from_plan(
        plan
    )

    executed = []

    def task_runner(task):
        executed.append(
            task.title
        )

        if task.title == "Task B":
            raise RuntimeError(
                "boom"
            )

    with pytest.raises(
        FixedPlanExecutionError
    ) as exc_info:
        execute_fixed_plan(
            run,
            task_runner,
        )

    assert executed == [
        "Task A",
        "Task B",
    ]

    assert (
        run.tasks[0].status
        == TaskStatus.COMPLETED
    )

    assert (
        run.tasks[1].status
        == TaskStatus.FAILED
    )

    assert (
        run.tasks[2].status
        == TaskStatus.PENDING
    )

    assert (
        run.status
        == RunStatus.FAILED
    )

    assert isinstance(
        exc_info.value.__cause__,
        RuntimeError,
    )
    
@pytest.mark.parametrize(
    "status",
    [
        RunStatus.QUEUED,
        RunStatus.RUNNING,
    ],
)
def test_execute_fixed_plan_requires_planning_run(
    status,
):
    run = create_run_from_plan(
        make_plan()
    )

    if status == RunStatus.QUEUED:
        object.__setattr__(
            run,
            "status",
            RunStatus.QUEUED,
        )
    else:
        run.transition_to(
            RunStatus.RUNNING
        )

    with pytest.raises(
        ValueError,
        match="PLANNING",
    ):
        execute_fixed_plan(
            run,
            lambda task: None,
        )
        
from flow_agent.domain import Run


def test_execute_fixed_plan_rejects_queued_run():
    run = Run(
        goal_id="goal-001"
    )

    with pytest.raises(
        ValueError,
        match="PLANNING",
    ):
        execute_fixed_plan(
            run,
            lambda task: None,
        )
        
from flow_agent.domain import Task

def test_fixed_plan_waits_for_dependencies():
    dependency = Task(
        title="Dependency",
        description="First",
    )

    dependent = Task(
        title="Dependent",
        description="Second",
        dependencies=(
            dependency.id,
        ),
    )

    run = Run(
        goal_id="goal-001",
        status=RunStatus.PLANNING,
        tasks=(
            dependent,
            dependency,
        ),
    )

    executed = []

    execute_fixed_plan(
        run,
        lambda task:
            executed.append(
                task.title
            ),
    )

    assert executed == [
        "Dependency",
        "Dependent",
    ]

    assert all(
        task.status
        == TaskStatus.COMPLETED
        for task in run.tasks
    )

    assert (
        run.status
        == RunStatus.COMPLETED
    )
    
