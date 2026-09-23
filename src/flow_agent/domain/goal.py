from datetime import datetime, timezone
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, Field, field_validator


class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), frozen=True)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    success_criteria: list[str] = Field(default_factory=list)
    requested_outputs: list[str] = Field(default_factory=list)
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        frozen=True,
    )

    @field_validator("created_at")
    @classmethod
    def normalize_created_at_to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)
