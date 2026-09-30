import pytest

from langchain.tools import tool
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.runnables import (
    RunnableLambda,
)

from flow_agent.runtime.agent_loop import (
    AgentStepLimitExceeded,
    AgentToolCallLimitExceeded,
    run_bounded_agent_loop,
)

def test_agent_loop_finishes_without_tool_calls():
    model = RunnableLambda(
        lambda messages: AIMessage(
            content="done"
        )
    )

    result = run_bounded_agent_loop(
        model,
        [],
        [
            HumanMessage(
                content="hello"
            )
        ],
        run_id="run-001",
        task_id="task-001",
    )

    assert result.steps == 1
    assert result.tool_calls == 0

    assert (
        result.messages[-1].content
        == "done"
    )
    
def test_agent_loop_executes_tool_and_continues():
    @tool("lookup")
    def lookup(value: str) -> str:
        """Look up a value."""
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
                content="finished"
            ),
        ]
    )

    model = RunnableLambda(
        lambda messages: next(
            responses
        )
    )

    result = run_bounded_agent_loop(
        model,
        [lookup],
        [
            HumanMessage(
                content="lookup abc"
            )
        ],
        run_id="run-001",
        task_id="task-001",
    )

    assert result.steps == 2
    assert result.tool_calls == 1

    assert isinstance(
        result.messages[2],
        ToolMessage,
    )

    assert (
        result.messages[2].content
        == "result:abc"
    )

    assert (
        result.messages[-1].content
        == "finished"
    )
    
def test_agent_loop_returns_tool_error_to_model():
    @tool("failing_tool")
    def failing_tool() -> str:
        """Always fail."""
        raise RuntimeError(
            "temporary failure"
        )

    def respond(messages):
        tool_messages = [
            message
            for message in messages
            if isinstance(
                message,
                ToolMessage,
            )
        ]

        if tool_messages:
            assert (
                tool_messages[-1].status
                == "error"
            )

            return AIMessage(
                content=(
                    "Could not complete "
                    "the tool operation."
                )
            )

        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name":
                        "failing_tool",
                    "args": {},
                    "id": "call-1",
                    "type": "tool_call",
                }
            ],
        )

    model = RunnableLambda(
        respond
    )

    result = run_bounded_agent_loop(
        model,
        [failing_tool],
        [
            HumanMessage(
                content="do it"
            )
        ],
        run_id="run-001",
        task_id="task-001",
    )

    assert result.steps == 2
    assert result.tool_calls == 1

    assert (
        result.messages[-1].content
        == (
            "Could not complete "
            "the tool operation."
        )
    )
    
def test_agent_loop_enforces_step_limit():
    executions = []

    @tool("repeat")
    def repeat() -> str:
        """Repeat forever."""
        executions.append("called")
        return "again"

    model = RunnableLambda(
        lambda messages: AIMessage(
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

    with pytest.raises(
        AgentStepLimitExceeded
    ):
        run_bounded_agent_loop(
            model,
            [repeat],
            [
                HumanMessage(
                    content="repeat"
                )
            ],
            run_id="run-001",
            task_id="task-001",
            max_steps=2,
        )

    assert executions == [
        "called",
    ]
    
def test_agent_loop_enforces_tool_call_limit():
    executions = []

    @tool("record")
    def record(value: str) -> str:
        """Record a value."""
        executions.append(value)
        return value

    model = RunnableLambda(
        lambda messages: AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "record",
                    "args": {
                        "value": "a",
                    },
                    "id": "call-a",
                    "type": "tool_call",
                },
                {
                    "name": "record",
                    "args": {
                        "value": "b",
                    },
                    "id": "call-b",
                    "type": "tool_call",
                },
            ],
        )
    )

    with pytest.raises(
        AgentToolCallLimitExceeded
    ):
        run_bounded_agent_loop(
            model,
            [record],
            [
                HumanMessage(
                    content="record"
                )
            ],
            run_id="run-001",
            task_id="task-001",
            max_tool_calls=1,
        )

    assert executions == []
    
@pytest.mark.parametrize(
    (
        "max_steps",
        "max_tool_calls",
        "message",
    ),
    [
        (
            0,
            1,
            "max_steps",
        ),
        (
            -1,
            1,
            "max_steps",
        ),
        (
            1,
            -1,
            "max_tool_calls",
        ),
    ],
)
def test_agent_loop_rejects_invalid_budgets(
    max_steps,
    max_tool_calls,
    message,
):
    model = RunnableLambda(
        lambda messages: AIMessage(
            content="done"
        )
    )

    with pytest.raises(
        ValueError,
        match=message,
    ):
        run_bounded_agent_loop(
            model,
            [],
            [],
            run_id="run-001",
            task_id="task-001",
            max_steps=max_steps,
            max_tool_calls=(
                max_tool_calls
            ),
        )