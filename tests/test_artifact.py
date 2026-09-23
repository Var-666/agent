from datetime import timezone

import pytest
from pydantic import ValidationError

from flow_agent.domain.artifact import Artifact, ArtifactKind


def test_create_artifact():
    artifact = Artifact(
        run_id="run-001",
        producer_task_id="task-001",
        kind=ArtifactKind.MARKDOWN,
        path="output/report.md",
        description="Generated report",
    )

    assert artifact.run_id == "run-001"
    assert artifact.producer_task_id == "task-001"
    assert artifact.kind == ArtifactKind.MARKDOWN
    assert artifact.path == "output/report.md"


def test_artifact_has_utc_created_at():
    artifact = Artifact(
        run_id="run-001",
        kind=ArtifactKind.TEXT,
        path="output/result.txt",
    )

    assert artifact.created_at.tzinfo is not None
    assert (
        artifact.created_at.utcoffset()
        == timezone.utc.utcoffset(artifact.created_at)
    )


def test_reject_absolute_posix_path():
    with pytest.raises(ValidationError):
        Artifact(
            run_id="run-001",
            kind=ArtifactKind.TEXT,
            path="/etc/passwd",
        )


def test_reject_absolute_windows_path():
    with pytest.raises(ValidationError):
        Artifact(
            run_id="run-001",
            kind=ArtifactKind.TEXT,
            path=r"C:\Users\secret.txt",
        )


def test_reject_parent_directory_escape():
    with pytest.raises(ValidationError):
        Artifact(
            run_id="run-001",
            kind=ArtifactKind.TEXT,
            path="../../secret.txt",
        )


def test_reject_nested_parent_directory_escape():
    with pytest.raises(ValidationError):
        Artifact(
            run_id="run-001",
            kind=ArtifactKind.TEXT,
            path="output/../../secret.txt",
        )


def test_artifact_id_is_immutable():
    artifact = Artifact(
        run_id="run-001",
        kind=ArtifactKind.JSON,
        path="output/result.json",
    )

    with pytest.raises(ValidationError):
        artifact.id = "new-id"
