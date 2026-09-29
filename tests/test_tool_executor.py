from flow_agent.tools.executor import (
    execute_tool_call,
    execute_tool_calls,
    execute_tool_calls_parallel
)
from flow_agent.tools.file import (
    create_read_file_tool,
)

import logging
from threading import Barrier

from langchain.tools import tool

RUN_ID = "run-001"
TASK_ID = "task-001"


def test_execute_tool_call(tmp_path):
    file_path = tmp_path / "notes.txt"
    file_path.write_text(
        "hello FlowAgent",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    message = execute_tool_call(
        {
            "name": "read_file",
            "args": {
                "path": "notes.txt",
            },
            "id": "call-001",
            "type": "tool_call",
        },
        [read_file],
        run_id=RUN_ID,
        task_id=TASK_ID,
    )

    assert message.content == "hello FlowAgent"
    assert message.tool_call_id == "call-001"
    assert message.status == "success"
    
def test_execute_tool_call_returns_error_message(
    tmp_path,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    message = execute_tool_call(
        {
            "name": "read_file",
            "args": {
                "path": "missing.txt",
            },
            "id": "call-001",
            "type": "tool_call",
        },
        [read_file],
        run_id=RUN_ID,
        task_id=TASK_ID,
    )

    assert message.tool_call_id == "call-001"
    assert message.status == "error"
    assert "missing.txt" in message.content
    
import pytest


def test_execute_tool_call_rejects_unknown_tool():
    with pytest.raises(
        ValueError,
        match="Unknown tool",
    ):
        execute_tool_call(
            {
                "name": "delete_everything",
                "args": {},
                "id": "call-001",
                "type": "tool_call",
            },
            [],
            run_id=RUN_ID,
            task_id=TASK_ID,
        )

def test_execute_tool_call_requires_id(
    tmp_path,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="must have an id",
    ):
        execute_tool_call(
            {
                "name": "read_file",
                "args": {
                    "path": "notes.txt",
                },
                "id": None,
                "type": "tool_call",
            },
            [read_file],
            run_id=RUN_ID,
            task_id=TASK_ID,
        )
        
def test_execute_multiple_tool_calls(
    tmp_path,
):
    (tmp_path / "a.txt").write_text(
        "content A",
        encoding="utf-8",
    )

    (tmp_path / "b.txt").write_text(
        "content B",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    messages = execute_tool_calls(
        [
            {
                "name": "read_file",
                "args": {
                    "path": "a.txt",
                },
                "id": "call-a",
                "type": "tool_call",
            },
            {
                "name": "read_file",
                "args": {
                    "path": "b.txt",
                },
                "id": "call-b",
                "type": "tool_call",
            },
        ],
        [read_file],
        run_id=RUN_ID,
        task_id=TASK_ID,
    )

    assert len(messages) == 2

    assert messages[0].content == "content A"
    assert messages[0].tool_call_id == "call-a"

    assert messages[1].content == "content B"
    assert messages[1].tool_call_id == "call-b"
    
def test_execute_multiple_tool_calls_keeps_errors(
    tmp_path,
):
    (tmp_path / "a.txt").write_text(
        "content A",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    messages = execute_tool_calls(
        [
            {
                "name": "read_file",
                "args": {"path": "a.txt"},
                "id": "call-a",
                "type": "tool_call",
            },
            {
                "name": "read_file",
                "args": {
                    "path": "missing.txt",
                },
                "id": "call-b",
                "type": "tool_call",
            },
        ],
        [read_file],
        run_id=RUN_ID,
        task_id=TASK_ID,
    )

    assert messages[0].status == "success"
    assert messages[1].status == "error"

    assert (
        messages[0].tool_call_id
        == "call-a"
    )

    assert (
        messages[1].tool_call_id
        == "call-b"
    )
    
def test_execute_tool_call_records_success(
    tmp_path,
    caplog,
):
    file_path = tmp_path / "notes.txt"

    file_path.write_text(
        "hello FlowAgent",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    ticks = iter(
        [
            10.0,
            10.25,
        ]
    )

    with caplog.at_level(
        logging.INFO,
        logger="flow_agent.tools.executor",
    ):
        message = execute_tool_call(
            {
                "name": "read_file",
                "args": {
                    "path": "notes.txt",
                },
                "id": "call-001",
                "type": "tool_call",
            },
            [read_file],
            run_id="run-001",
            task_id="task-001",
            clock=lambda: next(ticks),
        )

    assert message.status == "success"

    record = caplog.records[-1]

    assert record.run_id == "run-001"
    assert record.task_id == "task-001"

    assert (
        record.tool_call_id
        == "call-001"
    )

    assert (
        record.tool_name
        == "read_file"
    )

    assert record.latency_ms == pytest.approx(
        250.0
    )

    assert record.error is None
    
def test_execute_tool_call_records_error(
    tmp_path,
    caplog,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    ticks = iter(
        [
            20.0,
            20.1,
        ]
    )

    with caplog.at_level(
        logging.INFO,
        logger="flow_agent.tools.executor",
    ):
        message = execute_tool_call(
            {
                "name": "read_file",
                "args": {
                    "path": "missing.txt",
                },
                "id": "call-error",
                "type": "tool_call",
            },
            [read_file],
            run_id="run-001",
            task_id="task-001",
            clock=lambda: next(ticks),
        )

    assert message.status == "error"

    record = caplog.records[-1]

    assert (
        record.tool_call_id
        == "call-error"
    )

    assert record.latency_ms == pytest.approx(
        100.0
    )

    assert record.error.startswith(
        "FileNotFoundError:"
    )

    assert "missing.txt" in record.error
    
@pytest.mark.parametrize(
    (
        "run_id",
        "task_id",
        "message",
    ),
    [
        (
            "",
            "task-001",
            "run_id cannot be empty",
        ),
        (
            "run-001",
            "",
            "task_id cannot be empty",
        ),
    ],
)
def test_execute_tool_call_requires_runtime_context(
    tmp_path,
    run_id,
    task_id,
    message,
):
    read_file = create_read_file_tool(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match=message,
    ):
        execute_tool_call(
            {
                "name": "read_file",
                "args": {
                    "path": "notes.txt",
                },
                "id": "call-001",
                "type": "tool_call",
            },
            [read_file],
            run_id=run_id,
            task_id=task_id,
        )

def test_execute_multiple_tool_calls_records_each_call(
    tmp_path,
    caplog,
):
    (tmp_path / "a.txt").write_text(
        "A",
        encoding="utf-8",
    )

    (tmp_path / "b.txt").write_text(
        "B",
        encoding="utf-8",
    )

    read_file = create_read_file_tool(
        tmp_path
    )

    ticks = iter(
        [
            1.0,
            1.1,
            2.0,
            2.2,
        ]
    )

    with caplog.at_level(
        logging.INFO,
        logger="flow_agent.tools.executor",
    ):
        messages = execute_tool_calls(
            [
                {
                    "name": "read_file",
                    "args": {
                        "path": "a.txt",
                    },
                    "id": "call-a",
                    "type": "tool_call",
                },
                {
                    "name": "read_file",
                    "args": {
                        "path": "b.txt",
                    },
                    "id": "call-b",
                    "type": "tool_call",
                },
            ],
            [read_file],
            run_id="run-001",
            task_id="task-001",
            clock=lambda: next(ticks),
        )

    assert len(messages) == 2

    records = [
        record
        for record in caplog.records
        if record.getMessage().startswith(
            "tool_call "
        )
    ]

    assert len(records) == 2

    assert [
        record.tool_call_id
        for record in records
    ] == [
        "call-a",
        "call-b",
    ]

    assert all(
        record.run_id == "run-001"
        for record in records
    )

    assert all(
        record.task_id == "task-001"
        for record in records
    )

    assert [
        record.latency_ms
        for record in records
    ] == pytest.approx(
        [
            100.0,
            200.0,
        ]
    )
    
def test_execute_tool_calls_parallel_runs_concurrently():
    barrier = Barrier(2)

    @tool("first")
    def first() -> str:
        """Run the first independent operation."""
        barrier.wait(timeout=1)
        return "first result"

    @tool("second")
    def second() -> str:
        """Run the second independent operation."""
        barrier.wait(timeout=1)
        return "second result"

    messages = execute_tool_calls_parallel(
        [
            {
                "name": "first",
                "args": {},
                "id": "call-first",
                "type": "tool_call",
            },
            {
                "name": "second",
                "args": {},
                "id": "call-second",
                "type": "tool_call",
            },
        ],
        [
            first,
            second,
        ],
        run_id=RUN_ID,
        task_id=TASK_ID,
        max_workers=2,
    )

    assert [
        message.content
        for message in messages
    ] == [
        "first result",
        "second result",
    ]

    assert [
        message.tool_call_id
        for message in messages
    ] == [
        "call-first",
        "call-second",
    ]
    
from threading import Event


def test_execute_tool_calls_parallel_preserves_order():
    first_started = Event()
    second_finished = Event()

    @tool("slow_first")
    def slow_first() -> str:
        """Run the first operation."""

        first_started.set()

        if not second_finished.wait(
            timeout=1
        ):
            raise RuntimeError(
                "Second tool did not finish"
            )

        return "first"

    @tool("fast_second")
    def fast_second() -> str:
        """Run the second operation."""

        if not first_started.wait(
            timeout=1
        ):
            raise RuntimeError(
                "First tool did not start"
            )

        second_finished.set()

        return "second"

    messages = execute_tool_calls_parallel(
        [
            {
                "name": "slow_first",
                "args": {},
                "id": "call-a",
                "type": "tool_call",
            },
            {
                "name": "fast_second",
                "args": {},
                "id": "call-b",
                "type": "tool_call",
            },
        ],
        [
            slow_first,
            fast_second,
        ],
        run_id=RUN_ID,
        task_id=TASK_ID,
        max_workers=2,
    )

    assert [
        message.tool_call_id
        for message in messages
    ] == [
        "call-a",
        "call-b",
    ]
    
def test_execute_tool_calls_parallel_keeps_errors():
    barrier = Barrier(2)

    @tool("successful")
    def successful() -> str:
        """Return a successful result."""
        barrier.wait(timeout=1)
        return "ok"

    @tool("failing")
    def failing() -> str:
        """Fail during execution."""
        barrier.wait(timeout=1)
        raise RuntimeError(
            "tool failed"
        )

    messages = execute_tool_calls_parallel(
        [
            {
                "name": "successful",
                "args": {},
                "id": "call-success",
                "type": "tool_call",
            },
            {
                "name": "failing",
                "args": {},
                "id": "call-error",
                "type": "tool_call",
            },
        ],
        [
            successful,
            failing,
        ],
        run_id=RUN_ID,
        task_id=TASK_ID,
        max_workers=2,
    )

    assert messages[0].status == "success"
    assert messages[0].content == "ok"

    assert messages[1].status == "error"
    assert "tool failed" in messages[1].content
    
@pytest.mark.parametrize(
    "max_workers",
    [
        0,
        -1,
    ],
)
def test_execute_tool_calls_parallel_rejects_invalid_worker_count(
    max_workers,
):
    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        execute_tool_calls_parallel(
            [],
            [],
            run_id=RUN_ID,
            task_id=TASK_ID,
            max_workers=max_workers,
        )
        
def test_execute_tool_calls_parallel_records_each_call(
    caplog,
):
    barrier = Barrier(2)

    @tool("first")
    def first() -> str:
        """Run first."""
        barrier.wait(timeout=1)
        return "A"

    @tool("second")
    def second() -> str:
        """Run second."""
        barrier.wait(timeout=1)
        return "B"

    with caplog.at_level(
        logging.INFO,
        logger="flow_agent.tools.executor",
    ):
        execute_tool_calls_parallel(
            [
                {
                    "name": "first",
                    "args": {},
                    "id": "call-a",
                    "type": "tool_call",
                },
                {
                    "name": "second",
                    "args": {},
                    "id": "call-b",
                    "type": "tool_call",
                },
            ],
            [
                first,
                second,
            ],
            run_id=RUN_ID,
            task_id=TASK_ID,
            max_workers=2,
        )

    records = [
        record
        for record in caplog.records
        if record.getMessage().startswith(
            "tool_call "
        )
    ]

    assert {
        record.tool_call_id
        for record in records
    } == {
        "call-a",
        "call-b",
    }

    assert all(
        record.run_id == RUN_ID
        for record in records
    )

    assert all(
        record.task_id == TASK_ID
        for record in records
    )