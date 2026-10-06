import pytest

from flow_agent.domain import (
    Run,
    RunEventKind,
    RunStatus,
    Task,
    TaskStatus,
)
from flow_agent.planning.schema import (
    ExecutionPlan,
    PlanTask,
)
from flow_agent.runtime.plan_executor import (
    FixedPlanExecutionError,
    RunTimeLimitExceeded,
    create_run_from_plan,
    execute_fixed_plan,
    RetryableTaskError,
    ReplanCandidateError,
    ReplanRequired,
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
        
def test_execute_fixed_plan_rejects_running_run():
    run = create_run_from_plan(
        make_plan()
    )

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

    assert (
        run.status
        == RunStatus.RUNNING
    )
        
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
    
def test_execute_fixed_plan_records_events():
    run = create_run_from_plan(
        make_plan()
    )

    events = []

    execute_fixed_plan(
        run,
        lambda task: None,
        event_sink=events.append,
        clock=lambda: 0.0,
    )

    assert [
        event.kind
        for event in events
    ] == [
        RunEventKind.RUN_STARTED,
        RunEventKind.TASK_STARTED,
        RunEventKind.TASK_COMPLETED,
        RunEventKind.TASK_STARTED,
        RunEventKind.TASK_COMPLETED,
        RunEventKind.RUN_COMPLETED,
    ]
    
    assert events[0].run_id == run.id
    assert events[0].task_id is None

    assert events[1].task_id == (
        run.tasks[0].id
    )

    assert events[2].task_id == (
        run.tasks[0].id
    )

    assert events[3].task_id == (
        run.tasks[1].id
    )

    assert events[4].task_id == (
        run.tasks[1].id
    )

    assert events[5].task_id is None
    
    assert all(
    event.run_id == run.id
    for event in events
    )
    
def test_execute_fixed_plan_records_failure_events():
    run = create_run_from_plan(
        make_plan()
    )

    events = []

    def task_runner(task):
        raise RuntimeError(
            "provider failed"
        )

    with pytest.raises(
        FixedPlanExecutionError
    ):
        execute_fixed_plan(
            run,
            task_runner,
            event_sink=events.append,
            clock=lambda: 0.0,
        )

    assert [
        event.kind
        for event in events
    ] == [
        RunEventKind.RUN_STARTED,
        RunEventKind.TASK_STARTED,
        RunEventKind.TASK_FAILED,
        RunEventKind.RUN_FAILED,
    ]
    
    task_failed = events[-2]

    assert (
        task_failed.task_id
        == run.tasks[0].id
    )

    assert task_failed.payload == {
        "error_type": "RuntimeError",
        "error": "provider failed",
    }
    
    run_failed = events[-1]

    assert (
        run_failed.payload["reason"]
        == "task_failed"
    )

    assert (
        run_failed.payload["task_id"]
        == run.tasks[0].id
    )

def test_execute_fixed_plan_stops_when_run_time_expires():
    run = create_run_from_plan(
        make_plan()
    )

    executed = []
    events = []

    ticks = iter(
        [
            0.0,  # Run start
            0.0,  # Before Research
            2.0,  # Before Write report
        ]
    )

    def task_runner(task):
        executed.append(
            task.title
        )

    with pytest.raises(
        RunTimeLimitExceeded
    ):
        execute_fixed_plan(
            run,
            task_runner,
            max_run_seconds=1.0,
            clock=lambda: next(ticks),
            event_sink=events.append,
        )

    assert executed == [
        "Research",
    ]

    assert (
        run.tasks[0].status
        == TaskStatus.COMPLETED
    )

    assert (
        run.tasks[1].status
        == TaskStatus.PENDING
    )

    assert (
        run.status
        == RunStatus.FAILED
    )

    assert (
        events[-1].kind
        == RunEventKind.RUN_FAILED
    )

    assert events[-1].payload == {
        "reason": "time_limit_exceeded",
        "max_run_seconds": 1.0,
        "elapsed_seconds": 2.0,
    }

def test_run_time_limit_prevents_first_task():
    run = create_run_from_plan(
        make_plan()
    )

    executed = []
    events = []

    ticks = iter(
        [
            0.0,  # Run start
            1.0,  # Before first task
        ]
    )

    with pytest.raises(
        RunTimeLimitExceeded
    ):
        execute_fixed_plan(
            run,
            lambda task:
                executed.append(
                    task.title
                ),
            max_run_seconds=1.0,
            clock=lambda: next(ticks),
            event_sink=events.append,
        )

    assert executed == []

    assert all(
        task.status
        == TaskStatus.PENDING
        for task in run.tasks
    )

    assert (
        run.status
        == RunStatus.FAILED
    )

    assert [
        event.kind
        for event in events
    ] == [
        RunEventKind.RUN_STARTED,
        RunEventKind.RUN_FAILED,
    ]

    assert (
        events[-1].payload["reason"]
        == "time_limit_exceeded"
    )
        
def test_run_time_limit_is_checked_after_last_task():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="One task",
        tasks=(
            PlanTask(
                key="only",
                title="Only task",
                description="Do work",
            ),
        ),
    )

    run = create_run_from_plan(
        plan
    )

    executed = []
    events = []

    ticks = iter(
        [
            0.0,  # Run start
            0.0,  # Before task
            2.0,  # After final task
        ]
    )

    with pytest.raises(
        RunTimeLimitExceeded
    ):
        execute_fixed_plan(
            run,
            lambda task:
                executed.append(
                    task.title
                ),
            max_run_seconds=1.0,
            clock=lambda: next(ticks),
            event_sink=events.append,
        )

    assert executed == [
        "Only task",
    ]

    assert (
        run.tasks[0].status
        == TaskStatus.COMPLETED
    )

    assert (
        run.status
        == RunStatus.FAILED
    )

    assert (
        RunEventKind.RUN_COMPLETED
        not in {
            event.kind
            for event in events
        }
    )

    assert (
        events[-1].kind
        == RunEventKind.RUN_FAILED
    )

    assert (
        events[-1].payload["reason"]
        == "time_limit_exceeded"
    )
    
@pytest.mark.parametrize(
    "max_run_seconds",
    [
        0,
        -1,
        -0.5,
    ],
)
def test_execute_fixed_plan_rejects_invalid_run_budget(
    max_run_seconds,
):
    run = create_run_from_plan(
        make_plan()
    )

    with pytest.raises(
        ValueError,
        match="max_run_seconds",
    ):
        execute_fixed_plan(
            run,
            lambda task: None,
            max_run_seconds=(
                max_run_seconds
            ),
        )

    assert (
        run.status
        == RunStatus.PLANNING
    )

    assert all(
        task.status
        == TaskStatus.PENDING
        for task in run.tasks
    )
        
def test_execute_fixed_plan_does_not_require_event_sink():
    run = create_run_from_plan(
        make_plan()
    )

    result = execute_fixed_plan(
        run,
        lambda task: None,
        clock=lambda: 0.0,
    )

    assert (
        result.status
        == RunStatus.COMPLETED
    )
    
def make_single_task_plan() -> ExecutionPlan:
    return ExecutionPlan(
        goal_id="goal-001",
        summary="Single task",
        tasks=(
            PlanTask(
                key="research",
                title="Research",
                description=(
                    "Research sources"
                ),
            ),
        ),
    )
    
def test_fixed_plan_retries_retryable_task():
    run = create_run_from_plan(
        make_single_task_plan()
    )

    attempts = 0
    events = []

    def task_runner(task):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            raise RetryableTaskError(
                "temporary provider failure"
            )

    result = execute_fixed_plan(
        run,
        task_runner,
        max_task_retries=2,
        clock=lambda: 0.0,
        event_sink=events.append,
    )

    assert result is run
    assert attempts == 2

    assert (
        run.tasks[0].status
        == TaskStatus.COMPLETED
    )

    assert (
        run.status
        == RunStatus.COMPLETED
    )

    assert [
        event.kind
        for event in events
    ] == [
        RunEventKind.RUN_STARTED,
        RunEventKind.TASK_STARTED,
        RunEventKind.TASK_RETRYING,
        RunEventKind.TASK_COMPLETED,
        RunEventKind.RUN_COMPLETED,
    ]

    retry_event = events[2]

    assert retry_event.payload == {
        "retry_number": 1,
        "max_task_retries": 2,
        "error_type":
            "RetryableTaskError",
        "error":
            "temporary provider failure",
    }
    
def test_fixed_plan_fails_after_retry_budget_exhausted():
    run = create_run_from_plan(
        make_single_task_plan()
    )

    attempts = 0
    events = []

    def task_runner(task):
        nonlocal attempts
        attempts += 1

        raise RetryableTaskError(
            "still unavailable"
        )

    with pytest.raises(
        FixedPlanExecutionError
    ) as exc_info:
        execute_fixed_plan(
            run,
            task_runner,
            max_task_retries=2,
            clock=lambda: 0.0,
            event_sink=events.append,
        )

    assert attempts == 3

    assert (
        run.tasks[0].status
        == TaskStatus.FAILED
    )

    assert (
        run.status
        == RunStatus.FAILED
    )

    assert [
        event.kind
        for event in events
    ] == [
        RunEventKind.RUN_STARTED,
        RunEventKind.TASK_STARTED,
        RunEventKind.TASK_RETRYING,
        RunEventKind.TASK_RETRYING,
        RunEventKind.TASK_FAILED,
        RunEventKind.RUN_FAILED,
    ]

    retry_events = [
        event
        for event in events
        if (
            event.kind
            == RunEventKind.TASK_RETRYING
        )
    ]

    assert [
        event.payload["retry_number"]
        for event in retry_events
    ] == [
        1,
        2,
    ]

    assert isinstance(
        exc_info.value.__cause__,
        RetryableTaskError,
    )
    
def test_fixed_plan_does_not_retry_non_retryable_error():
    run = create_run_from_plan(
        make_single_task_plan()
    )

    attempts = 0
    events = []

    def task_runner(task):
        nonlocal attempts
        attempts += 1

        raise ValueError(
            "invalid task input"
        )

    with pytest.raises(
        FixedPlanExecutionError
    ) as exc_info:
        execute_fixed_plan(
            run,
            task_runner,
            max_task_retries=5,
            clock=lambda: 0.0,
            event_sink=events.append,
        )

    assert attempts == 1

    assert (
        RunEventKind.TASK_RETRYING
        not in {
            event.kind
            for event in events
        }
    )

    assert (
        run.tasks[0].status
        == TaskStatus.FAILED
    )

    assert (
        run.status
        == RunStatus.FAILED
    )

    assert isinstance(
        exc_info.value.__cause__,
        ValueError,
    )
    
def test_run_time_limit_prevents_task_retry():
    run = create_run_from_plan(
        make_single_task_plan()
    )

    attempts = 0
    events = []

    ticks = iter(
        [
            0.0,  # Run start
            0.0,  # Before initial task
            2.0,  # Before retry
        ]
    )

    def task_runner(task):
        nonlocal attempts
        attempts += 1

        raise RetryableTaskError(
            "temporary failure"
        )

    with pytest.raises(
        RunTimeLimitExceeded
    ):
        execute_fixed_plan(
            run,
            task_runner,
            max_run_seconds=1.0,
            max_task_retries=3,
            clock=lambda: next(ticks),
            event_sink=events.append,
        )

    assert attempts == 1

    assert (
        run.tasks[0].status
        == TaskStatus.FAILED
    )

    assert (
        run.status
        == RunStatus.FAILED
    )

    assert (
        RunEventKind.TASK_RETRYING
        not in {
            event.kind
            for event in events
        }
    )

    assert [
        event.kind
        for event in events
    ] == [
        RunEventKind.RUN_STARTED,
        RunEventKind.TASK_STARTED,
        RunEventKind.TASK_FAILED,
        RunEventKind.RUN_FAILED,
    ]

    assert (
        events[-1].payload["reason"]
        == "time_limit_exceeded"
    )
    
def test_fixed_plan_rejects_negative_task_retry_budget():
    run = create_run_from_plan(
        make_single_task_plan()
    )

    with pytest.raises(
        ValueError,
        match="max_task_retries",
    ):
        execute_fixed_plan(
            run,
            lambda task: None,
            max_task_retries=-1,
        )

    assert (
        run.status
        == RunStatus.PLANNING
    )

    assert (
        run.tasks[0].status
        == TaskStatus.PENDING
    )
    
def test_fixed_plan_pauses_when_replan_is_allowed():
    run = create_run_from_plan(
        make_single_task_plan()
    )

    events = []
    policy_calls = []

    def task_runner(task):
        raise ReplanCandidateError(
            "tool arguments do not fit plan"
        )

    def replan_policy(
        candidate_run,
        task,
        error,
    ):
        policy_calls.append(
            (
                candidate_run,
                task,
                error,
            )
        )

        return True

    with pytest.raises(
        ReplanRequired
    ) as exc_info:
        execute_fixed_plan(
            run,
            task_runner,
            replan_policy=replan_policy,
            clock=lambda: 0.0,
            event_sink=events.append,
        )

    assert (
        exc_info.value.task_id
        == run.tasks[0].id
    )

    assert isinstance(
        exc_info.value.__cause__,
        ReplanCandidateError,
    )

    assert len(policy_calls) == 1

    policy_run, policy_task, policy_error = (
        policy_calls[0]
    )

    assert policy_run is run
    assert policy_task is run.tasks[0]

    assert isinstance(
        policy_error,
        ReplanCandidateError,
    )

    assert (
        run.tasks[0].status
        == TaskStatus.WAITING
    )

    assert (
        run.status
        == RunStatus.PLANNING
    )

    assert run.finished_at is None

    assert [
        event.kind
        for event in events
    ] == [
        RunEventKind.RUN_STARTED,
        RunEventKind.TASK_STARTED,
        RunEventKind.REPLAN_REQUESTED,
    ]

    replan_event = events[-1]

    assert (
        replan_event.task_id
        == run.tasks[0].id
    )

    assert replan_event.payload == {
        "error_type":
            "ReplanCandidateError",
        "error":
            "tool arguments do not fit plan",
    }
    
def test_fixed_plan_denies_replan_by_default():
    run = create_run_from_plan(
        make_single_task_plan()
    )

    events = []

    def task_runner(task):
        raise ReplanCandidateError(
            "plan cannot continue"
        )

    with pytest.raises(
        FixedPlanExecutionError
    ) as exc_info:
        execute_fixed_plan(
            run,
            task_runner,
            clock=lambda: 0.0,
            event_sink=events.append,
        )

    assert (
        run.tasks[0].status
        == TaskStatus.FAILED
    )

    assert (
        run.status
        == RunStatus.FAILED
    )

    assert (
        RunEventKind.REPLAN_REQUESTED
        not in {
            event.kind
            for event in events
        }
    )

    assert [
        event.kind
        for event in events
    ] == [
        RunEventKind.RUN_STARTED,
        RunEventKind.TASK_STARTED,
        RunEventKind.TASK_FAILED,
        RunEventKind.RUN_FAILED,
    ]

    assert isinstance(
        exc_info.value.__cause__,
        ReplanCandidateError,
    )
    
def test_fixed_plan_fails_when_replan_policy_denies():
    run = create_run_from_plan(
        make_single_task_plan()
    )

    policy_calls = 0

    def task_runner(task):
        raise ReplanCandidateError(
            "bad execution strategy"
        )

    def replan_policy(
        candidate_run,
        task,
        error,
    ):
        nonlocal policy_calls
        policy_calls += 1

        return False

    with pytest.raises(
        FixedPlanExecutionError
    ):
        execute_fixed_plan(
            run,
            task_runner,
            replan_policy=replan_policy,
            clock=lambda: 0.0,
        )

    assert policy_calls == 1

    assert (
        run.tasks[0].status
        == TaskStatus.FAILED
    )

    assert (
        run.status
        == RunStatus.FAILED
    )