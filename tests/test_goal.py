from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from flow_agent.domain.goal import Goal


def test_create_goal():
    goal = Goal(
        title="调查 LangChain 更新",
        description="调查 LangChain 最近 7 天的重要更新",
        success_criteria=[
            "所有重要结论有来源",
        ],
        requested_outputs=[
            "markdown_report",
        ],
    )

    assert goal.title == "调查 LangChain 更新"
    assert goal.description == "调查 LangChain 最近 7 天的重要更新"
    assert goal.success_criteria == ["所有重要结论有来源"]
    assert goal.requested_outputs == ["markdown_report"]


def test_goal_generates_unique_ids():
    goal1 = Goal(
        title="Goal 1",
        description="Description 1",
    )

    goal2 = Goal(
        title="Goal 2",
        description="Description 2",
    )

    assert goal1.id != goal2.id


def test_goal_has_default_empty_lists():
    goal = Goal(
        title="生成报告",
        description="生成一个 Markdown 报告",
    )

    assert goal.success_criteria == []
    assert goal.requested_outputs == []


def test_goal_requires_non_empty_title():
    with pytest.raises(ValidationError):
        Goal(
            title="",
            description="Valid description",
        )


def test_goal_requires_non_empty_description():
    with pytest.raises(ValidationError):
        Goal(
            title="Valid title",
            description="",
        )


def test_goal_id_is_immutable():
    goal = Goal(
        title="Test Goal",
        description="Test description",
    )

    with pytest.raises(ValidationError):
        goal.id = "new-id"


def test_goal_created_at_is_utc():
    goal = Goal(
        title="Test Goal",
        description="Test description",
    )

    assert goal.created_at.tzinfo is not None
    assert goal.created_at.utcoffset() == timezone.utc.utcoffset(goal.created_at)


def test_goal_rejects_naive_created_at():
    with pytest.raises(ValidationError):
        Goal(
            title="Test",
            description="Test",
            created_at=datetime.now(),
        )
