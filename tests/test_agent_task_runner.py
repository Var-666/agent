from langchain_core.messages import (
    HumanMessage,
)

from flow_agent.domain import Task
from flow_agent.runtime.agent_task_runner import (
    default_task_messages,
)


def test_default_task_messages_describes_task():
    task = Task(
        title="Research LangChain",
        description=(
            "Find important recent updates."
        ),
    )

    messages = default_task_messages(
        task
    )

    assert len(messages) == 1

    assert isinstance(
        messages[0],
        HumanMessage,
    )

    assert messages[0].content == (
        "Task: Research LangChain\n\n"
        "Find important recent updates."
    )
    
from langchain.tools import tool
from langchain_core.messages import (
    AIMessage,
)
from langchain_core.runnables import (
    RunnableLambda,
)

from flow_agent.domain import (
    RunStatus,
    TaskStatus,
)
from flow_agent.planning.schema import (
    ExecutionPlan,
    PlanTask,
)
from flow_agent.runtime.agent_task_runner import (
    create_agent_task_runner,
)
from flow_agent.runtime.plan_executor import (
    create_run_from_plan,
    execute_fixed_plan,
)


def test_fixed_plan_executes_task_through_agent_loop():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Research something",
        tasks=(
            PlanTask(
                key="research",
                title="Research",
                description="Look up abc",
            ),
        ),
    )

    run = create_run_from_plan(
        plan
    )

    tool_inputs = []

    @tool("lookup")
    def lookup(value: str) -> str:
        """Look up a value."""
        tool_inputs.append(value)

        return f"result:{value}"

    responses = iter(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "lookup",
                        "args": {
                            "value": "abc",
                        },
                        "id": "call-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(
                content="done"
            ),
        ]
    )

    model = RunnableLambda(
        lambda messages:
            next(responses)
    )

    task_runner = (
        create_agent_task_runner(
            run,
            model,
            [lookup],
        )
    )

    result = execute_fixed_plan(
        run,
        task_runner,
    )

    assert result is run

    assert tool_inputs == [
        "abc",
    ]

    assert (
        run.tasks[0].status
        == TaskStatus.COMPLETED
    )

    assert (
        run.status
        == RunStatus.COMPLETED
    )
    
import pytest

from langchain.tools import tool
from langchain_core.messages import (
    AIMessage,
)
from langchain_core.runnables import (
    RunnableLambda,
)

from flow_agent.domain import (
    RunStatus,
    TaskStatus,
)
from flow_agent.planning.schema import (
    ExecutionPlan,
    PlanTask,
)
from flow_agent.runtime.agent_loop import (
    AgentStepLimitExceeded,
)
from flow_agent.runtime.agent_task_runner import (
    create_agent_task_runner,
)
from flow_agent.runtime.plan_executor import (
    FixedPlanExecutionError,
    create_run_from_plan,
    execute_fixed_plan,
)


def test_agent_step_limit_fails_task_and_run():
    plan = ExecutionPlan(
        goal_id="goal-001",
        summary="Bounded task",
        tasks=(
            PlanTask(
                key="research",
                title="Research",
                description="Keep working",
            ),
        ),
    )

    run = create_run_from_plan(
        plan
    )

    executions = []

    @tool("repeat")
    def repeat() -> str:
        """Repeat work."""
        executions.append(
            "called"
        )

        return "again"

    model = RunnableLambda(
        lambda messages:
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "repeat",
                        "args": {},
                        "id":
                            f"call-{len(messages)}",
                        "type": "tool_call",
                    }
                ],
            )
    )

    task_runner = (
        create_agent_task_runner(
            run,
            model,
            [repeat],
            max_steps=2,
        )
    )

    with pytest.raises(
        FixedPlanExecutionError
    ) as exc_info:
        execute_fixed_plan(
            run,
            task_runner,
        )

    assert executions == [
        "called",
    ]

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
        AgentStepLimitExceeded,
    )