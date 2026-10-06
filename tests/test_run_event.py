from datetime import (
    datetime,
    timedelta,
    timezone,
)

from flow_agent.domain import (
    RunEvent,
    RunEventKind,
)


def test_run_event_defaults_to_utc():
    event = RunEvent(
        run_id="run-001",
        kind=RunEventKind.RUN_STARTED,
    )

    assert (
        event.created_at.utcoffset()
        == timedelta(0)
    )


def test_run_event_normalizes_datetime_to_utc():
    event = RunEvent(
        run_id="run-001",
        kind=RunEventKind.RUN_STARTED,
        created_at=datetime(
            2026,
            9,
            30,
            12,
            0,
            tzinfo=timezone(
                timedelta(hours=8)
            ),
        ),
    )

    assert event.created_at == datetime(
        2026,
        9,
        30,
        4,
        0,
        tzinfo=timezone.utc,
    )