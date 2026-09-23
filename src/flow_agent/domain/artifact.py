from datetime import datetime, timezone
from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, Field, field_validator


class ArtifactKind(StrEnum):
    MARKDOWN = "markdown"
    TEXT = "text"
    JSON = "json"
    CSV = "csv"


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    run_id: str = Field(min_length=1, frozen=True)
    producer_task_id: str | None = Field(default=None, frozen=True)
    kind: ArtifactKind
    path: str = Field(min_length=1, frozen=True)
    description: str | None = None
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        frozen=True,
    )

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = value.strip()

        if not path:
            raise ValueError("Artifact path cannot be empty")
        if PurePosixPath(path).is_absolute():
            raise ValueError("Artifact path must be relative")
        if PureWindowsPath(path).is_absolute():
            raise ValueError("Artifact path must be relative")

        normalized = PurePosixPath(path.replace("\\", "/"))

        if ".." in normalized.parts:
            raise ValueError("Artifact path cannot escape the workspace")

        if normalized == PurePosixPath("."):
            raise ValueError("Artifact path must point to a file")

        return normalized.as_posix()

    @field_validator("created_at")
    @classmethod
    def normalize_created_at_to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)
