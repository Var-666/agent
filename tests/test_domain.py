from flow_agent.domain import (
    Artifact,
    ArtifactKind,
    Goal,
    Run,
    RunStatus,
    Task,
    TaskStatus,
)


def test_domain_public_api():
    goal = Goal(
        title="Research LangChain",
        description="Research recent LangChain updates",
    )

    run = Run(
        goal_id=goal.id,
    )

    task = Task(
        title="Search",
        description="Search official sources",
    )

    artifact = Artifact(
        run_id=run.id,
        kind=ArtifactKind.MARKDOWN,
        path="output/report.md",
    )

    assert goal.id
    assert run.status == RunStatus.QUEUED
    assert task.status == TaskStatus.PENDING
    assert artifact.kind == ArtifactKind.MARKDOWN